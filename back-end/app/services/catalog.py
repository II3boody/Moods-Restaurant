from datetime import date, timedelta

from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.models import Bundle, Order, OrderItem, OrderStatus, Product, utcnow


def best_sellers(db: Session, limit: int = 10, days: int | None = None) -> list[Product]:
    """أكتر المنتجات طلباً (من الأوردرات غير الملغية). days=30 يعني آخر 30 يوم بس."""
    q = (select(OrderItem.product_id, func.sum(OrderItem.quantity).label("sold"))
         .join(Order, Order.id == OrderItem.order_id)
         .where(Order.status != OrderStatus.cancelled, OrderItem.product_id.is_not(None)))
    if days:
        q = q.where(Order.created_at >= utcnow() - timedelta(days=days))
    q = q.group_by(OrderItem.product_id).order_by(desc("sold")).limit(limit)
    ids = [r.product_id for r in db.execute(q)]
    if not ids:
        return []
    found = {p.id: p for p in db.scalars(
        select(Product).where(Product.id.in_(ids), Product.is_available.is_(True)))}
    return [found[i] for i in ids if i in found]


def live_bundles(db: Session) -> list[Bundle]:
    today = date.today()
    return list(db.scalars(
        select(Bundle).where(
            Bundle.is_active.is_(True),
            or_(Bundle.start_date.is_(None), Bundle.start_date <= today),
            or_(Bundle.end_date.is_(None), Bundle.end_date >= today),
        ).order_by(Bundle.id.desc())))
