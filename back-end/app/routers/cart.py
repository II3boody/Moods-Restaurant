from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, select

from app.core.deps import DB, CurrentUser
from app.models import CartItem, Product
from app.schemas import CartAddIn, CartItemOut, CartOut, CartUpdateIn
from app.services.pricing import apply_discount, best_discount_percent

router = APIRouter(prefix="/cart", tags=["Cart"])


def build_cart(db, user) -> CartOut:
    rows = db.scalars(select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id)).all()
    subtotal = sum((Decimal(r.product.price) * r.quantity for r in rows), Decimal("0"))
    discount, total = apply_discount(subtotal, best_discount_percent(db))
    return CartOut(
        items=[CartItemOut(product=r.product, quantity=r.quantity,
                           line_total=float(Decimal(r.product.price) * r.quantity)) for r in rows],
        subtotal=float(subtotal), discount=float(discount), total=float(total),
        items_count=sum(r.quantity for r in rows))


@router.get("", response_model=CartOut)
def get_cart(db: DB, user: CurrentUser):
    return build_cart(db, user)


@router.post("/items", response_model=CartOut, summary="Add a product (increments if already in cart)")
def add_item(data: CartAddIn, db: DB, user: CurrentUser):
    product = db.get(Product, data.product_id)
    if not product or not product.is_available:
        raise HTTPException(404, "Product not available")
    item = db.scalar(select(CartItem).where(CartItem.user_id == user.id,
                                            CartItem.product_id == data.product_id))
    if item:
        item.quantity = min(item.quantity + data.quantity, 50)
    else:
        db.add(CartItem(user_id=user.id, product_id=data.product_id, quantity=data.quantity))
    db.commit()
    return build_cart(db, user)


@router.patch("/items/{product_id}", response_model=CartOut, summary="Set exact quantity")
def update_item(product_id: int, data: CartUpdateIn, db: DB, user: CurrentUser):
    item = db.scalar(select(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id))
    if not item:
        raise HTTPException(404, "Item not in cart")
    item.quantity = data.quantity
    db.commit()
    return build_cart(db, user)


@router.delete("/items/{product_id}", response_model=CartOut)
def remove_item(product_id: int, db: DB, user: CurrentUser):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id, CartItem.product_id == product_id))
    db.commit()
    return build_cart(db, user)


@router.delete("", response_model=CartOut, summary="Empty the cart")
def clear_cart(db: DB, user: CurrentUser):
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    return build_cart(db, user)
