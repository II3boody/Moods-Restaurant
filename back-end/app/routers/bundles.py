
from fastapi import APIRouter, File, HTTPException, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.core.deps import DB, AdminUser
from app.models import Bundle, BundleItem, CartItem, Product, utcnow
from app.schemas import BundleIn, BundleOut, BundleUpdate, Message
from app.services import media
from app.services.catalog import live_bundles
from app.services.images import read_image

router = APIRouter(prefix="/bundles", tags=["Offers (Bundles)"])


def build_items(db, items) -> list[BundleItem]:
    merged: dict[int, int] = {}
    for i in items:
        merged[i.product_id] = merged.get(i.product_id, 0) + i.quantity
    products = {p.id for p in db.scalars(select(Product).where(Product.id.in_(merged)))}
    missing = set(merged) - products
    if missing:
        raise HTTPException(400, f"Products not found: {sorted(missing)}")
    return [BundleItem(product_id=pid, quantity=q) for pid, q in merged.items()]


def check_dates(start, end):
    if start and end and end < start:
        raise HTTPException(400, "end_date must be after start_date")


@router.get("", response_model=list[BundleOut], summary="Live offers (public, for the website)")
def list_offers(db: DB):
    return live_bundles(db)


@router.get("/admin/all", response_model=list[BundleOut], summary="All offers incl. inactive/expired (admin)")
def list_all(db: DB, _: AdminUser):
    return db.scalars(select(Bundle).order_by(Bundle.id.desc())).all()


@router.get("/{bundle_id}", response_model=BundleOut)
def get_offer(bundle_id: int, db: DB):
    b = db.get(Bundle, bundle_id)
    if not b:
        raise HTTPException(404, "Offer not found")
    return b


@router.post("", response_model=BundleOut, status_code=201, summary="Create an offer / package (admin)")
def create_offer(data: BundleIn, db: DB, _: AdminUser):
    check_dates(data.start_date, data.end_date)
    b = Bundle(**data.model_dump(exclude={"items"}))
    b.items = build_items(db, data.items)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.put("/{bundle_id}", response_model=BundleOut, summary="Edit an offer (admin)")
@router.patch("/{bundle_id}", response_model=BundleOut, summary="Edit an offer (admin)")
def update_offer(bundle_id: int, data: BundleUpdate, db: DB, _: AdminUser):
    b = db.get(Bundle, bundle_id)
    if not b:
        raise HTTPException(404, "Offer not found")
    changes = data.model_dump(exclude_unset=True)
    items = data.items if "items" in changes else None
    changes.pop("items", None)
    for k, v in changes.items():
        setattr(b, k, v)
    check_dates(b.start_date, b.end_date)
    if items is not None:
        b.items = build_items(db, items)  # بيستبدل المحتويات كلها
    db.commit()
    db.refresh(b)
    return b


@router.delete("/{bundle_id}", response_model=Message)
def delete_offer(bundle_id: int, db: DB, _: AdminUser):
    b = db.get(Bundle, bundle_id)
    if not b:
        raise HTTPException(404, "Offer not found")
    old_image = b.image
    db.query(CartItem).filter(CartItem.bundle_id == bundle_id).delete()
    db.delete(b)
    db.commit()
    media.destroy_by_url(old_image)
    return Message(message="Offer deleted")


@router.post("/{bundle_id}/image", response_model=BundleOut, summary="Upload offer image")
def upload_image(bundle_id: int, db: DB, _: AdminUser, file: UploadFile = File(...)):
    b = db.get(Bundle, bundle_id)
    if not b:
        raise HTTPException(404, "Offer not found")
    data, content_type = read_image(file)
    old_image = b.image
    if media.enabled():
        b.image = media.upload(data, "bundles")
        b.image_data = b.image_type = None
    else:  # fallback: تخزين في الداتابيز
        b.image_data, b.image_type = data, content_type
        b.image = f"/api/v1/bundles/{b.id}/image?v={int(utcnow().timestamp())}"
    db.commit()
    db.refresh(b)
    media.destroy_by_url(old_image)
    return b


@router.get("/{bundle_id}/image", response_class=Response, summary="Offer image file")
def get_image(bundle_id: int, db: DB):
    b = db.get(Bundle, bundle_id)
    if not b:
        raise HTTPException(404, "Offer not found")
    if b.image_data:
        return Response(b.image_data, media_type=b.image_type or "image/jpeg",
                        headers={"Cache-Control": "public, max-age=86400"})
    if b.image and b.image.startswith(("http://", "https://")):
        return RedirectResponse(b.image, status_code=307, headers={"Cache-Control": "public, max-age=3600"})
    raise HTTPException(404, "This offer has no image")
