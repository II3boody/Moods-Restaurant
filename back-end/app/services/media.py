"""رفع الصور على Cloudinary (signed upload عبر REST API، من غير SDK)."""
import hashlib
import logging
import re
import time

from fastapi import HTTPException

from app.core.config import settings

log = logging.getLogger("moods.media")
TIMEOUT = 30
_CLOUD_NAME = re.compile(r"[A-Za-z0-9_-]+")


def _clean(value: str) -> str:
    # حماية إضافية فوق الـ validator في config: أي whitespace/tab/newline/تنصيص يتشال
    return (value or "").strip().strip("\"'").strip()


def _cloud() -> str:
    return _clean(settings.CLOUDINARY_CLOUD_NAME)


def _key() -> str:
    return _clean(settings.CLOUDINARY_API_KEY)


def _secret() -> str:
    return _clean(settings.CLOUDINARY_API_SECRET)


def _folder() -> str:
    return _clean(settings.CLOUDINARY_FOLDER).strip("/") or "moods"


def enabled() -> bool:
    return bool(_cloud() and _key() and _secret())


def _api(path: str) -> str:
    """https://api.cloudinary.com/v1_1/{cloud_name}/{path}"""
    cloud = _cloud()
    if not _CLOUD_NAME.fullmatch(cloud):
        # مفيش طباعة للقيمة نفسها في الرسالة
        log.error("CLOUDINARY_CLOUD_NAME has invalid characters (length=%d)", len(cloud))
        raise HTTPException(500, "Cloudinary is misconfigured: CLOUDINARY_CLOUD_NAME is invalid")
    return f"https://api.cloudinary.com/v1_1/{cloud}/{path}"


def _sign(params: dict) -> str:
    # التوقيع = sha1( "k1=v1&k2=v2" (مرتبين أبجدياً) + api_secret )
    to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return hashlib.sha1((to_sign + _secret()).encode()).hexdigest()


def upload(source: bytes | str, folder: str) -> str:
    """بيرفع صورة (bytes أو لينك صورة موجودة على النت) وبيرجع الـ secure_url الكامل."""
    import httpx  # lazy: التطبيق يفضل شغال حتى لو المكتبة مش متثبتة (الرفع بس هو اللي يفشل)

    params = {"folder": f"{_folder()}/{folder}", "timestamp": int(time.time())}
    data = {**params, "api_key": _key(), "signature": _sign(params)}
    files = None
    if isinstance(source, bytes):
        files = {"file": ("image", source)}
    else:
        data["file"] = source
    url = _api("image/upload")
    try:
        r = httpx.post(url, data=data, files=files, timeout=TIMEOUT)
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        log.error("Cloudinary upload failed: %s", type(exc).__name__)  # من غير تفاصيل ممكن تكشف أسرار
        raise HTTPException(502, "Could not reach Cloudinary") from exc
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    secure_url = body.get("secure_url", "")
    if r.status_code != 200 or not secure_url.startswith("https://"):
        msg = body.get("error", {}).get("message", r.text[:200])
        log.error("Cloudinary error %s: %s", r.status_code, msg)
        raise HTTPException(502, f"Cloudinary upload failed: {msg}")
    return secure_url


def _public_id(url: str | None) -> str | None:
    """بيطلّع public_id من لينك Cloudinary بتاعنا. أي لينك تاني بيرجع None."""
    if not url or f"res.cloudinary.com/{_cloud()}/" not in url:
        return None
    m = re.search(r"/upload/(?:v\d+/)?(.+)\.[A-Za-z0-9]+$", url.split("?")[0])
    return m.group(1) if m else None


def destroy_by_url(url: str | None) -> None:
    """بيمسح الصورة من Cloudinary (best effort: لو فشل بيكمل ومبيوقعش الريكوست)."""
    public_id = _public_id(url) if enabled() else None
    if not public_id:
        return
    import httpx

    params = {"public_id": public_id, "timestamp": int(time.time())}
    data = {**params, "api_key": _key(), "signature": _sign(params)}
    try:
        httpx.post(_api("image/destroy"), data=data, timeout=TIMEOUT)
    except (httpx.HTTPError, httpx.InvalidURL, HTTPException):
        log.warning("Could not delete %s from Cloudinary", public_id)
