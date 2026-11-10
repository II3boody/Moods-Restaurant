"""رفع الصور على Cloudinary (signed upload عبر REST API، من غير SDK)."""
import hashlib
import logging
import re
import time

import httpx
from fastapi import HTTPException

from app.core.config import settings

log = logging.getLogger("moods.media")
TIMEOUT = 30


def enabled() -> bool:
    return bool(settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY
                and settings.CLOUDINARY_API_SECRET)


def _api(path: str) -> str:
    return f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/{path}"


def _sign(params: dict) -> str:
    # التوقيع = sha1( "k1=v1&k2=v2" (مرتبين أبجدياً) + api_secret )
    to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.sha1((to_sign + settings.CLOUDINARY_API_SECRET).encode()).hexdigest()


def upload(source: bytes | str, folder: str) -> str:
    """بيرفع صورة (bytes أو لينك صورة موجودة على النت) وبيرجع الـ secure_url الكامل."""
    params = {"folder": f"{settings.CLOUDINARY_FOLDER}/{folder}", "timestamp": int(time.time())}
    data = {**params, "api_key": settings.CLOUDINARY_API_KEY, "signature": _sign(params)}
    files = None
    if isinstance(source, bytes):
        files = {"file": ("image", source)}
    else:
        data["file"] = source
    try:
        r = httpx.post(_api("image/upload"), data=data, files=files, timeout=TIMEOUT)
    except httpx.HTTPError as exc:
        log.exception("Cloudinary upload failed")
        raise HTTPException(502, "Could not reach Cloudinary") from exc
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or "secure_url" not in body:
        msg = body.get("error", {}).get("message", r.text[:200])
        log.error("Cloudinary error %s: %s", r.status_code, msg)
        raise HTTPException(502, f"Cloudinary upload failed: {msg}")
    return body["secure_url"]


def _public_id(url: str | None) -> str | None:
    """بيطلّع public_id من لينك Cloudinary بتاعنا. أي لينك تاني بيرجع None."""
    if not url or f"res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/" not in url:
        return None
    m = re.search(r"/upload/(?:v\d+/)?(.+)\.[A-Za-z0-9]+$", url.split("?")[0])
    return m.group(1) if m else None


def destroy_by_url(url: str | None) -> None:
    """بيمسح الصورة من Cloudinary (best effort: لو فشل بيكمل ومبيوقعش الريكوست)."""
    public_id = _public_id(url) if enabled() else None
    if not public_id:
        return
    params = {"public_id": public_id, "timestamp": int(time.time())}
    data = {**params, "api_key": settings.CLOUDINARY_API_KEY, "signature": _sign(params)}
    try:
        httpx.post(_api("image/destroy"), data=data, timeout=TIMEOUT)
    except httpx.HTTPError:
        log.warning("Could not delete %s from Cloudinary", public_id)
