import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import DB, AdminUser
from app.models import Category, Product
from app.schemas import (CategoryIn, CategoryOut, CategoryUpdate, Message, Page, ProductIn,
                         ProductOut, ProductUpdate)

categories_router = APIRouter(prefix="/categories", tags=["Categories"])
products_router = APIRouter(prefix="/products", tags=["Products"])


# ---------------- Categories ----------------
@categories_router.get("", response_model=list[CategoryOut])
def list_categories(db: DB, include_inactive: bool = False):
    q = select(Category).order_by(Category.sort_order, Category.id)
    if not include_inactive:
        q = q.where(Category.is_active.is_(True))
    return db.scalars(q).all()


@categories_router.post("", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, db: DB, _: AdminUser):
    if db.scalar(select(Category).where(Category.name == data.name)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Category already exists")
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@categories_router.put("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, data: CategoryUpdate, db: DB, _: AdminUser):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@categories_router.delete("/{category_id}", response_model=Message)
def delete_category(category_id: int, db: DB, _: AdminUser):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    if db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id)):
        raise HTTPException(409, "Category has products. Move or delete them first")
    db.delete(cat)
    db.commit()
    return Message(message="Category deleted")


# ---------------- Products ----------------
@products_router.get("", response_model=Page[ProductOut], summary="List products (search / filter / paginate)")
def list_products(
    db: DB,
    category_id: int | None = None,
    search: str | None = Query(None, description="search in product name"),
    popular: bool | None = None,
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    include_unavailable: bool = False,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    q = select(Product)
    if not include_unavailable:
        q = q.where(Product.is_available.is_(True))
    if category_id:
        q = q.where(Product.category_id == category_id)
    if search:
        q = q.where(Product.name.ilike(f"%{search}%"))
    if popular is not None:
        q = q.where(Product.is_popular.is_(popular))
    if min_price is not None:
        q = q.where(Product.price >= min_price)
    if max_price is not None:
        q = q.where(Product.price <= max_price)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Product.id).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@products_router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: DB):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@products_router.post("", response_model=ProductOut, status_code=201)
def create_product(data: ProductIn, db: DB, _: AdminUser):
    if not db.get(Category, data.category_id):
        raise HTTPException(400, "Category does not exist")
    p = Product(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@products_router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: DB, _: AdminUser):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    changes = data.model_dump(exclude_unset=True)
    if "category_id" in changes and not db.get(Category, changes["category_id"]):
        raise HTTPException(400, "Category does not exist")
    for k, v in changes.items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@products_router.delete("/{product_id}", response_model=Message)
def delete_product(product_id: int, db: DB, _: AdminUser):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    db.delete(p)
    db.commit()
    return Message(message="Product deleted")


@products_router.post("/{product_id}/image", response_model=ProductOut, summary="Upload product image")
def upload_product_image(product_id: int, db: DB, _: AdminUser, file: UploadFile = File(...)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "Only png/jpg/jpeg/webp images are allowed")
    folder = Path(settings.UPLOAD_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    with open(folder / name, "wb") as out:
        shutil.copyfileobj(file.file, out)
    p.image = f"/uploads/{name}"
    db.commit()
    db.refresh(p)
    return p
