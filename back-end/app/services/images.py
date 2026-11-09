from fastapi import HTTPException, UploadFile

MAX_BYTES = 2 * 1024 * 1024  # 2MB (حد Vercel للـ request حوالي 4.5MB)
ALLOWED = {"image/png", "image/jpeg", "image/webp"}


def _looks_like(data: bytes, content_type: str) -> bool:
    if content_type == "image/png":
        return data.startswith(b"\x89PNG")
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8")
    if content_type == "image/webp":
        return data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    return False


def read_image(file: UploadFile) -> tuple[bytes, str]:
    """بيقرا الصورة المرفوعة ويتأكد من النوع والحجم، وبيرجع (bytes, content_type)."""
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "Only png / jpeg / webp images are allowed")
    data = file.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image is too large (max 2MB)")
    if not _looks_like(data, file.content_type):
        raise HTTPException(400, "File content does not match its image type")
    return data, file.content_type
