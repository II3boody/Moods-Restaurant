from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from app.core.deps import DB, CurrentUser
from app.models import Bundle, CartItem, Product
from app.schemas import CartAddIn, CartItemOut, CartOut, CartUpdateIn
from app.services.pricing import apply_discount, best_discount_percent

router = APIRouter(prefix="/cart", tags=["Cart"])


def unit_price(item: CartItem) -> Decimal:
    return Decimal(item.product.price if item.product else item.bundle.price)


def build_cart(db, user) -> CartOut:
    rows = db.scalars(select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id)).all()
    lines = [(r, unit_price(r) * r.quantity) for r in rows]
    subtotal = sum((line for _, line in lines), Decimal("0"))
    discount, total = apply_discount(subtotal, best_discount_percent(db))
    return CartOut(
        items=[CartItemOut(id=r.id, product=r.product, bundle=r.bundle, quantity=r.quantity,
                           line_total=float(line)) for r, line in lines],
        subtotal=float(subtotal), discount=float(discount), total=float(total),
        items_count=sum(r.quantity for r in rows))


@router.get("", response_model=CartOut)
def get_cart(db: DB, user: CurrentUser):
    return build_cart(db, user)


@router.post("/items", response_model=CartOut,
             summary="Add a product OR an offer (send product_id or bundle_id)")
def add_item(data: CartAddIn, db: DB, user: CurrentUser):
    if data.product_id:
        product = db.get(Product, data.product_id)
        if not product or not product.is_available:
            raise HTTPException(404, "Product not available")
        cond = CartItem.product_id == data.product_id
        new = dict(product_id=data.product_id)
    else:
        bundle = db.get(Bundle, data.bundle_id)
        if not bundle or not bundle.is_live:
            raise HTTPException(404, "Offer not available")
        cond = CartItem.bundle_id == data.bundle_id
        new = dict(bundle_id=data.bundle_id)
    item = db.scalar(select(CartItem).where(CartItem.user_id == user.id, cond))
    if item:
        item.quantity = min(item.quantity + data.quantity, 50)
    else:
        db.add(CartItem(user_id=user.id, quantity=data.quantity, **new))
    db.commit()
    return build_cart(db, user)


@router.patch("/items/{item_id}", response_model=CartOut, summary="Set exact quantity of a cart line")
def update_item(item_id: int, data: CartUpdateIn, db: DB, user: CurrentUser):
    item = db.scalar(select(CartItem).where(CartItem.user_id == user.id, CartItem.id == item_id))
    if not item:
        raise HTTPException(404, "Item not in cart")
    item.quantity = data.quantity
    db.commit()
    return build_cart(db, user)


@router.delete("/items/{item_id}", response_model=CartOut, summary="Remove a cart line")
def remove_item(item_id: int, db: DB, user: CurrentUser):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id, CartItem.id == item_id))
    db.commit()
    return build_cart(db, user)


@router.delete("", response_model=CartOut, summary="Empty the cart")
def clear_cart(db: DB, user: CurrentUser):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    return build_cart(db, user)
