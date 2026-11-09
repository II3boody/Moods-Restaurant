from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.core.deps import DB, AdminUser, CurrentUser
from app.models import Complaint, ComplaintStatus, Order
from app.schemas import ComplaintIn, ComplaintOut, ComplaintUpdate, Page

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintOut, status_code=201, summary="Submit a complaint")
def create_complaint(data: ComplaintIn, db: DB, user: CurrentUser):
    if data.order_id:
        order = db.get(Order, data.order_id)
        if not order or order.user_id != user.id:
            raise HTTPException(400, "Order not found")
    complaint = Complaint(user_id=user.id, **data.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@router.get("/me", response_model=list[ComplaintOut], summary="My complaints")
def my_complaints(db: DB, user: CurrentUser):
    return db.scalars(select(Complaint).where(Complaint.user_id == user.id)
                      .order_by(Complaint.id.desc())).all()


@router.get("", response_model=Page[ComplaintOut], summary="All complaints (admin)")
def all_complaints(db: DB, _: AdminUser, status: ComplaintStatus | None = None,
                   page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    q = select(Complaint)
    if status:
        q = q.where(Complaint.status == status)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    items = db.scalars(q.order_by(Complaint.id.desc()).offset((page - 1) * size).limit(size)).all()
    return dict(items=items, total=total, page=page, size=size)


@router.patch("/{complaint_id}", response_model=ComplaintOut, summary="Respond / change status (admin)")
def update_complaint(complaint_id: int, data: ComplaintUpdate, db: DB, admin: AdminUser):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(complaint, k, v)
    complaint.handled_by = admin.id
    db.commit()
    db.refresh(complaint)
    return complaint
