from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import DB, AdminUser, SuperAdminUser
from app.core.security import hash_password
from app.models import (Complaint, ComplaintStatus, ContactMessage, Order, OrderStatus, Review,
                        Role, User)
from app.schemas import ActiveUpdate, AdminCreateIn, Page, RoleUpdate, StatsOut, UserOut

router = APIRouter(prefix="/admin", tags=["Admin & Super Admin"])


@router.get("/stats", response_model=StatsOut, summary="Dashboard numbers (admin)")
def stats(db: DB, _: AdminUser):
    count = lambda q: db.scalar(q) or 0  # noqa: E731
    revenue = db.scalar(select(func.coalesce(func.sum(Order.total), 0)).where(
        Order.status == OrderStatus.delivered))
    return StatsOut(
        users=count(select(func.count()).select_from(User)),
        customers=count(select(func.count()).select_from(User).where(User.role == Role.customer)),
        orders=count(select(func.count()).select_from(Order)),
        pending_orders=count(select(func.count()).select_from(Order).where(Order.status == OrderStatus.pending)),
        revenue=float(revenue),
        open_complaints=count(select(func.count()).select_from(Complaint).where(
            Complaint.status.in_([ComplaintStatus.open, ComplaintStatus.in_progress]))),
        unread_messages=count(select(func.count()).select_from(ContactMessage).where(
            ContactMessage.is_read.is_(False))),
        pending_reviews=count(select(func.count()).select_from(Review).where(Review.is_approved.is_(False))),
    )


@router.get("/users", response_model=Page[UserOut], summary="List users (admin)")
def list_users(db: DB, _: AdminUser, role: Role | None = None, search: str | None = None,
               page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    q = select(User)
    if role:
        q = q.where(User.role == role)
    if search:
        q = q.where(User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(User.id).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@router.post("/users", response_model=UserOut, status_code=201,
             summary="Create an admin account (super admin only)")
def create_staff(data: AdminCreateIn, db: DB, _: SuperAdminUser):
    if data.role == Role.super_admin:
        raise HTTPException(400, "Cannot create another super admin from the API")
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(full_name=data.full_name, email=data.email.lower(), phone=data.phone,
                password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserOut, summary="Promote / demote (super admin only)")
def change_role(user_id: int, data: RoleUpdate, db: DB, me: SuperAdminUser):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == me.id:
        raise HTTPException(400, "You cannot change your own role")
    if data.role == Role.super_admin or user.role == Role.super_admin:
        raise HTTPException(400, "Super admin role cannot be assigned/removed from the API")
    user.role = data.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/active", response_model=UserOut, summary="Enable / disable an account")
def set_active(user_id: int, data: ActiveUpdate, db: DB, me: AdminUser):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == me.id:
        raise HTTPException(400, "You cannot disable yourself")
    # الأدمن العادي يقدر يوقف العملاء بس. السوبر أدمن يوقف أي حد
    if me.role == Role.admin and user.role != Role.customer:
        raise HTTPException(403, "Only super admin can change staff accounts")
    if user.role == Role.super_admin:
        raise HTTPException(403, "Super admin cannot be disabled")
    user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user


@router.get("/media-status", summary="Where do uploaded images go? (no secrets are shown)")
def media_status(_: AdminUser):
    from app.services import media

    return {
        "storage": "cloudinary" if media.enabled() else "database",
        "cloudinary_enabled": media.enabled(),
        "cloud_name": media._cloud() or None,
        "cloud_name_length": len(media._cloud()),
        "cloud_name_valid": bool(media._CLOUD_NAME.fullmatch(media._cloud())),
        # أي حرف غلط في الاسم (بيظهر كـ U+XXXX عشان الحروف المخفية تبان). مفيش أسرار هنا
        "cloud_name_bad_characters": sorted({f"U+{ord(c):04X}" for c in settings.CLOUDINARY_CLOUD_NAME
                                              if not media._CLOUD_NAME.fullmatch(c)}),
        "api_key_set": bool(media._key()),
        "api_secret_set": bool(media._secret()),
        "folder": media._folder(),
    }
