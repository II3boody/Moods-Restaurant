from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Festival


def best_discount_percent(db: Session) -> int:
    today = date.today()
    percents = db.scalars(
        select(Festival.discount_percent).where(
            Festival.is_active.is_(True), Festival.start_date <= today, Festival.end_date >= today
        )
    ).all()
    return max(percents, default=0)


def apply_discount(subtotal: Decimal, percent: int) -> tuple[Decimal, Decimal]:
    """returns (discount, total)"""
    discount = (subtotal * percent / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return discount, subtotal - discount
