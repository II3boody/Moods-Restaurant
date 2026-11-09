from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.deps import DB, AdminUser, CurrentUser
from app.models import Product, Review, Role
from app.schemas import Message, Page, ReviewIn, ReviewOut

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=Page[ReviewOut], summary="Public approved reviews")
def list_reviews(db: DB, product_id: int | None = None,
                 page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=50)):
    q = select(Review).where(Review.is_approved.is_(True))
    if product_id:
        q = q.where(Review.product_id == product_id)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Review.id.desc()).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@router.post("", response_model=ReviewOut, status_code=201, summary="Add a review (needs admin approval)")
def create_review(data: ReviewIn, db: DB, user: CurrentUser):
    if data.product_id and not db.get(Product, data.product_id):
        raise HTTPException(400, "Product does not exist")
    review = Review(user_id=user.id, **data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/admin/all", response_model=Page[ReviewOut], summary="All reviews incl. pending (admin)")
def admin_list(db: DB, _: AdminUser, is_approved: bool | None = None,
               page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    q = select(Review)
    if is_approved is not None:
        q = q.where(Review.is_approved.is_(is_approved))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Review.id.desc()).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@router.patch("/{review_id}/approve", response_model=ReviewOut)
def approve(review_id: int, db: DB, _: AdminUser, approved: bool = True):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(404, "Review not found")
    review.is_approved = approved
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", response_model=Message, summary="Delete my review (or any review if admin)")
def delete_review(review_id: int, db: DB, user: CurrentUser):
    review = db.get(Review, review_id)
    if not review or (review.user_id != user.id and user.role == Role.customer):
        raise HTTPException(404, "Review not found")
    db.delete(review)
    db.commit()
    return Message(message="Review deleted")
