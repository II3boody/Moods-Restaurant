"""Contact, Festivals, About, Home"""
import json
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.deps import DB, AdminUser
from app.models import (Category, ContactMessage, Festival, Product, Review, SiteContent)
from app.services.catalog import best_sellers, live_bundles
from app.schemas import (AboutContent, ContactIn, ContactOut, FestivalIn, FestivalOut,
                         FestivalUpdate, HomeOut, Message, Page)

contact_router = APIRouter(prefix="/contact", tags=["Contact"])
festivals_router = APIRouter(prefix="/festivals", tags=["Festivals"])
about_router = APIRouter(prefix="/about", tags=["About"])
home_router = APIRouter(prefix="/home", tags=["Home"])


# ---------------- Contact ----------------
@contact_router.post("", response_model=Message, status_code=201, summary="Send us a message (public)")
def send_message(data: ContactIn, db: DB):
    db.add(ContactMessage(**data.model_dump()))
    db.commit()
    return Message(message="Thanks! We received your message")


@contact_router.get("", response_model=Page[ContactOut], summary="Inbox (admin)")
def inbox(db: DB, _: AdminUser, unread_only: bool = False,
          page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    q = select(ContactMessage)
    if unread_only:
        q = q.where(ContactMessage.is_read.is_(False))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(ContactMessage.id.desc()).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@contact_router.patch("/{message_id}/read", response_model=ContactOut)
def mark_read(message_id: int, db: DB, _: AdminUser):
    msg = db.get(ContactMessage, message_id)
    if not msg:
        raise HTTPException(404, "Message not found")
    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg


@contact_router.delete("/{message_id}", response_model=Message)
def delete_message(message_id: int, db: DB, _: AdminUser):
    msg = db.get(ContactMessage, message_id)
    if not msg:
        raise HTTPException(404, "Message not found")
    db.delete(msg)
    db.commit()
    return Message(message="Message deleted")


# ---------------- Festivals ----------------
@festivals_router.get("", response_model=list[FestivalOut], summary="Current festivals / offers (public)")
def list_festivals(db: DB, include_all: bool = False):
    q = select(Festival)
    if not include_all:
        today = date.today()
        q = q.where(Festival.is_active.is_(True), Festival.end_date >= today)
    return db.scalars(q.order_by(Festival.start_date)).all()


@festivals_router.post("", response_model=FestivalOut, status_code=201)
def create_festival(data: FestivalIn, db: DB, _: AdminUser):
    if data.end_date < data.start_date:
        raise HTTPException(400, "end_date must be after start_date")
    f = Festival(**data.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@festivals_router.put("/{festival_id}", response_model=FestivalOut)
def update_festival(festival_id: int, data: FestivalUpdate, db: DB, _: AdminUser):
    f = db.get(Festival, festival_id)
    if not f:
        raise HTTPException(404, "Festival not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(f, k, v)
    if f.end_date < f.start_date:
        db.rollback()
        raise HTTPException(400, "end_date must be after start_date")
    db.commit()
    db.refresh(f)
    return f


@festivals_router.delete("/{festival_id}", response_model=Message)
def delete_festival(festival_id: int, db: DB, _: AdminUser):
    f = db.get(Festival, festival_id)
    if not f:
        raise HTTPException(404, "Festival not found")
    db.delete(f)
    db.commit()
    return Message(message="Festival deleted")


# ---------------- About ----------------
def load_about(db) -> AboutContent:
    row = db.get(SiteContent, "about")
    return AboutContent(**json.loads(row.value)) if row else AboutContent()


@about_router.get("", response_model=AboutContent, summary="About + contact info + working hours (public)")
def get_about(db: DB):
    return load_about(db)


@about_router.put("", response_model=AboutContent,
                  summary="Edit About page content, English and/or Arabic (admin)")
@about_router.patch("", response_model=AboutContent,
                    summary="Edit About page content, English and/or Arabic (admin)")
def update_about(data: AboutContent, db: DB, _: AdminUser):
    """Only the fields you send are changed; omitted fields (e.g. story_ar) keep their stored value."""
    merged = load_about(db).model_dump()
    merged.update(data.model_dump(exclude_unset=True))
    result = AboutContent(**merged)
    payload = json.dumps(result.model_dump(), ensure_ascii=False)
    row = db.get(SiteContent, "about")
    if row:
        row.value = payload
    else:
        db.add(SiteContent(key="about", value=payload))
    db.commit()
    return result


# ---------------- Home ----------------
@home_router.get("", response_model=HomeOut, summary="Everything the home page needs in ONE request")
def home(db: DB):
    today = date.today()
    available = Product.is_available.is_(True)
    return HomeOut(
        categories=db.scalars(select(Category).where(
            Category.is_active.is_(True), Category.show_on_home.is_(True),
            Category.parent_id.is_(None)).order_by(Category.sort_order, Category.id)).all(),
        popular_products=db.scalars(select(Product).where(
            Product.is_popular.is_(True), available).limit(12)).all(),
        recommended_products=db.scalars(select(Product).where(
            Product.is_recommended.is_(True), available).limit(12)).all(),
        best_sellers=best_sellers(db, limit=10, days=30),
        offers=live_bundles(db),
        festivals=db.scalars(select(Festival).where(
            Festival.is_active.is_(True), Festival.end_date >= today)).all(),
        latest_reviews=db.scalars(select(Review).where(Review.is_approved.is_(True))
                                  .order_by(Review.id.desc()).limit(6)).all(),
        about=load_about(db),
    )
