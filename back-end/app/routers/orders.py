from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import delete, func, select

from app.core.deps import DB, AdminUser, CurrentUser
from app.models import CartItem, Order, OrderItem, OrderStatus, Role
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate, Page
from app.services.pricing import apply_discount, best_discount_percent

router = APIRouter(prefix="/orders", tags=["Orders"])

# الانتقالات المسموحة لحالة الأوردر (الأدمن)
ALLOWED = {
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
    OrderStatus.confirmed: {OrderStatus.preparing, OrderStatus.cancelled},
    OrderStatus.preparing: {OrderStatus.out_for_delivery, OrderStatus.cancelled},
    OrderStatus.out_for_delivery: {OrderStatus.delivered, OrderStatus.cancelled},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


@router.post("", response_model=OrderOut, status_code=201, summary="Place an order from my cart")
def create_order(data: OrderCreate, db: DB, user: CurrentUser):
    cart = db.scalars(select(CartItem).where(CartItem.user_id == user.id)).all()
    if not cart:
        raise HTTPException(400, "Cart is empty")
    unavailable = [c.product.name for c in cart if not c.product.is_available]
    if unavailable:
        raise HTTPException(400, f"Not available anymore: {', '.join(unavailable)}")

    subtotal = sum((Decimal(c.product.price) * c.quantity for c in cart), Decimal("0"))
    discount, total = apply_discount(subtotal, best_discount_percent(db))
    order = Order(user_id=user.id, delivery_address=data.delivery_address, phone=data.phone,
                  payment_method=data.payment_method, notes=data.notes,
                  subtotal=subtotal, discount=discount, total=total)
    order.items = [OrderItem(product_id=c.product_id, product_name=c.product.name,
                             unit_price=c.product.price, quantity=c.quantity) for c in cart]
    db.add(order)
    db.execute(delete(CartItem).where(CartItem.user_id == user.id))
    db.commit()
    db.refresh(order)
    return order


@router.get("/me", response_model=list[OrderOut], summary="My orders")
def my_orders(db: DB, user: CurrentUser):
    return db.scalars(select(Order).where(Order.user_id == user.id).order_by(Order.id.desc())).all()


@router.get("", response_model=Page[OrderOut], summary="All orders (admin)")
def all_orders(db: DB, _: AdminUser, status: OrderStatus | None = None,
               page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    q = select(Order)
    if status:
        q = q.where(Order.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Order.id.desc()).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: DB, user: CurrentUser):
    order = db.get(Order, order_id)
    if not order or (order.user_id != user.id and user.role == Role.customer):
        raise HTTPException(404, "Order not found")
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut, summary="Cancel my order (only while pending)")
def cancel_order(order_id: int, db: DB, user: CurrentUser):
    order = db.get(Order, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(404, "Order not found")
    if order.status != OrderStatus.pending:
        raise HTTPException(400, "Only pending orders can be cancelled")
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderOut, summary="Update order status (admin)")
def update_status(order_id: int, data: OrderStatusUpdate, db: DB, _: AdminUser):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Order not found")
    if data.status not in ALLOWED[order.status]:
        raise HTTPException(400, f"Cannot move order from '{order.status.value}' to '{data.status.value}'")
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
