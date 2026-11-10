from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import func, or_, select

from app.core.deps import DB, AdminUser
from app.models import BundleItem, CartItem, Category, Product, utcnow
from app.schemas import (CategoryIn, CategoryOut, CategoryTree, CategoryUpdate, Message, Page,
                         ProductIn, ProductOut, ProductUpdate)
from app.services import media
from app.services.catalog import best_sellers
from app.services.images import read_image

categories_router = APIRouter(prefix="/categories", tags=["Categories"])
products_router = APIRouter(prefix="/products", tags=["Products"])


# ---------------- Categories ----------------
def check_parent(db, parent_id: int | None, self_id: int | None = None) -> None:
    """مستويين بس: قسم ← قسم فرعي."""
    if parent_id is None:
        return
    parent = db.get(Category, parent_id)
    if not parent:
        raise HTTPException(400, "Parent category does not exist")
    if parent.parent_id is not None:
        raise HTTPException(400, "Only 2 levels are allowed (category → sub-category)")
    if self_id is not None:
        if parent_id == self_id:
            raise HTTPException(400, "A category cannot be its own parent")
        if db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == self_id)):
            raise HTTPException(400, "This category has sub-categories, so it cannot become a sub-category")


@categories_router.get("", response_model=list[CategoryOut], summary="Flat list of categories")
def list_categories(db: DB, include_inactive: bool = False, parent_id: int | None = None):
    q = select(Category).order_by(Category.sort_order, Category.id)
    if not include_inactive:
        q = q.where(Category.is_active.is_(True))
    if parent_id is not None:
        q = q.where(Category.parent_id == parent_id)
    return db.scalars(q).all()


@categories_router.get("/tree", response_model=list[CategoryTree],
                       summary="Categories with their sub-categories (for menus)")
def category_tree(db: DB, include_inactive: bool = False):
    q = select(Category).order_by(Category.sort_order, Category.id)
    if not include_inactive:
        q = q.where(Category.is_active.is_(True))
    rows = db.scalars(q).all()
    children: dict[int, list[Category]] = {}
    for c in rows:
        if c.parent_id:
            children.setdefault(c.parent_id, []).append(c)
    return [CategoryTree.model_validate(c).model_copy(
        update={"children": [CategoryOut.model_validate(x) for x in children.get(c.id, [])]})
        for c in rows if c.parent_id is None]


@categories_router.post("", response_model=CategoryOut, status_code=201)
def create_category(data: CategoryIn, db: DB, _: AdminUser):
    if db.scalar(select(Category).where(Category.name == data.name)):
        raise HTTPException(409, "Category already exists")
    check_parent(db, data.parent_id)
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@categories_router.put("/{category_id}", response_model=CategoryOut)
@categories_router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, data: CategoryUpdate, db: DB, _: AdminUser):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    changes = data.model_dump(exclude_unset=True)
    if "parent_id" in changes:
        check_parent(db, changes["parent_id"], category_id)
    for k, v in changes.items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@categories_router.delete("/{category_id}", response_model=Message)
def delete_category(category_id: int, db: DB, _: AdminUser):
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(404, "Category not found")
    if db.scalar(select(func.count()).select_from(Category).where(Category.parent_id == category_id)):
        raise HTTPException(409, "Category has sub-categories. Delete or move them first")
    if db.scalar(select(func.count()).select_from(Product).where(Product.category_id == category_id)):
        raise HTTPException(409, "Category has products. Move or delete them first")
    db.delete(cat)
    db.commit()
    return Message(message="Category deleted")


# ---------------- Products ----------------
@products_router.get("", response_model=Page[ProductOut], summary="List products (search / filter / paginate)")
def list_products(
    db: DB,
    category_id: int | None = Query(None, description="لو قسم أب بيجيب منتجات أقسامه الفرعية كمان"),
    search: str | None = Query(None, description="search in product name"),
    popular: bool | None = None,
    recommended: bool | None = None,
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
        children = select(Category.id).where(Category.parent_id == category_id)
        q = q.where(or_(Product.category_id == category_id, Product.category_id.in_(children)))
    if search:
        q = q.where(or_(Product.name.ilike(f"%{search}%"), Product.name_ar.ilike(f"%{search}%")))
    if popular is not None:
        q = q.where(Product.is_popular.is_(popular))
    if recommended is not None:
        q = q.where(Product.is_recommended.is_(recommended))
    if min_price is not None:
        q = q.where(Product.price >= min_price)
    if max_price is not None:
        q = q.where(Product.price <= max_price)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Product.id).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


# لازم قبل /{product_id}
@products_router.get("/best-sellers", response_model=list[ProductOut],
                     summary="Most ordered products (calculated automatically from orders)")
def get_best_sellers(db: DB, limit: int = Query(10, ge=1, le=50),
                     days: int | None = Query(None, ge=1, description="آخر كام يوم، فاضي = كل الوقت")):
    return best_sellers(db, limit, days)


@products_router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: DB):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@products_router.post("", response_model=ProductOut, status_code=201, summary="Add a product (admin)")
def create_product(data: ProductIn, db: DB, _: AdminUser):
    if not db.get(Category, data.category_id):
        raise HTTPException(400, "Category does not exist")
    p = Product(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@products_router.put("/{product_id}", response_model=ProductOut, summary="Edit any field (admin)")
@products_router.patch("/{product_id}", response_model=ProductOut, summary="Edit any field (admin)")
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
    if db.scalar(select(func.count()).select_from(BundleItem).where(BundleItem.product_id == product_id)):
        raise HTTPException(409, "Product is part of an offer/bundle. Remove it from the bundle first "
                                 "(or just set is_available=false)")
    old_image = p.image
    db.query(CartItem).filter(CartItem.product_id == product_id).delete()
    db.delete(p)
    db.commit()
    media.destroy_by_url(old_image)
    return Message(message="Product deleted")


# ---- الصور: متخزنة في الداتابيز (Vercel مفيهوش فايل سيستم دايم) ----
@products_router.post("/{product_id}/image", response_model=ProductOut,
                      summary="Upload product image (png/jpeg/webp, max 2MB)")
def upload_product_image(product_id: int, db: DB, _: AdminUser, file: UploadFile = File(...)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    data, content_type = read_image(file)
    old_image = p.image
    if media.enabled():
        p.image = media.upload(data, "products")
        p.image_data = p.image_type = None
    else:  # fallback: تخزين في الداتابيز
        p.image_data, p.image_type = data, content_type
        p.image = f"/api/v1/products/{p.id}/image?v={int(utcnow().timestamp())}"
    db.commit()
    db.refresh(p)
    media.destroy_by_url(old_image)  # يمسح الصورة القديمة من Cloudinary لو كانت هناك
    return p


@products_router.get("/{product_id}/image", summary="Product image file", response_class=Response)
def get_product_image(product_id: int, db: DB):
    p = db.get(Product, product_id)
    if not p or not p.image_data:
        raise HTTPException(404, "No uploaded image")
    return Response(p.image_data, media_type=p.image_type or "image/jpeg",
                    headers={"Cache-Control": "public, max-age=86400"})


@products_router.delete("/{product_id}/image", response_model=ProductOut, summary="Remove product image")
def delete_product_image(product_id: int, db: DB, _: AdminUser):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    old_image = p.image
    p.image = p.image_data = p.image_type = None
    db.commit()
    db.refresh(p)
    media.destroy_by_url(old_image)
    return p
