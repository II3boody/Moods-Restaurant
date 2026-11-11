from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models import ComplaintStatus, OrderStatus, PaymentMethod, Role

T = TypeVar("T")


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


# ---------- Auth / Users ----------
class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=72)


class UserOut(ORM):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: Role
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(BaseModel):
    refresh_token: str


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=72)


class AdminCreateIn(RegisterIn):
    role: Role = Role.admin


class RoleUpdate(BaseModel):
    role: Role


class ActiveUpdate(BaseModel):
    is_active: bool


# ---------- Menu ----------
class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    name_ar: str | None = Field(default=None, max_length=100, description="الاسم بالعربي (اختياري)")
    description: str | None = None
    description_ar: str | None = Field(default=None, description="الوصف بالعربي (اختياري)")
    image: str | None = None
    sort_order: int = 0
    is_active: bool = True
    show_on_home: bool = True
    parent_id: int | None = None

    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "Sandwiches", "name_ar": "ساندويتشات",
        "description": "Freshly grilled sandwiches", "description_ar": "ساندويتشات مشوية طازجة",
        "image": None, "sort_order": 0, "is_active": True, "show_on_home": True, "parent_id": None}]})


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    name_ar: str | None = Field(default=None, max_length=100)
    description: str | None = None
    description_ar: str | None = None
    image: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    show_on_home: bool | None = None
    parent_id: int | None = None


class CategoryOut(ORM, CategoryIn):
    id: int
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": 1, "name": "Sandwiches", "name_ar": "ساندويتشات",
        "description": "Freshly grilled sandwiches", "description_ar": "ساندويتشات مشوية طازجة",
        "image": None, "sort_order": 0, "is_active": True, "show_on_home": True, "parent_id": None}]})


class CategoryTree(CategoryOut):
    children: list[CategoryOut] = []


class ProductIn(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=150)
    name_ar: str | None = Field(default=None, max_length=150, description="الاسم بالعربي (اختياري)")
    description: str | None = None
    description_ar: str | None = Field(default=None, description="الوصف بالعربي (اختياري)")
    details: str | None = None
    details_ar: str | None = Field(default=None, description="التفاصيل بالعربي (اختياري)")
    price: float = Field(gt=0)
    image: str | None = None
    is_popular: bool = False
    is_recommended: bool = False
    is_available: bool = True
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "category_id": 1,
        "name": "Beef Burger", "name_ar": "برجر لحم",
        "description": "Grilled beef burger", "description_ar": "برجر لحم مشوي",
        "details": "150g beef, cheddar, lettuce, tomato", "details_ar": "150 جم لحم بقري، جبنة شيدر، خس، طماطم",
        "price": 120, "is_popular": False, "is_recommended": True, "is_available": True}]})


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=150)
    name_ar: str | None = Field(default=None, max_length=150)
    description: str | None = None
    description_ar: str | None = None
    details: str | None = None
    details_ar: str | None = None
    price: float | None = Field(default=None, gt=0)
    image: str | None = None
    is_popular: bool | None = None
    is_recommended: bool | None = None
    is_available: bool | None = None


class ProductOut(ORM):
    id: int
    category_id: int
    name: str
    name_ar: str | None = None
    description: str | None
    description_ar: str | None = None
    details: str | None
    details_ar: str | None = None
    price: float
    image: str | None
    is_popular: bool
    is_recommended: bool
    is_available: bool
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": 7, "category_id": 1,
        "name": "Beef Burger", "name_ar": "برجر لحم",
        "description": "Grilled beef burger", "description_ar": "برجر لحم مشوي",
        "details": "150g beef, cheddar, lettuce, tomato", "details_ar": "150 جم لحم بقري، جبنة شيدر، خس، طماطم",
        "price": 120.0, "image": "https://res.cloudinary.com/your-cloud/image/upload/v1/moods/products/beef-burger.jpg",
        "is_popular": False, "is_recommended": True, "is_available": True}]})


# ---------- Bundles (offers / packages) ----------
class BundleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class BundleIn(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    name_ar: str | None = Field(default=None, max_length=150, description="الاسم بالعربي (اختياري)")
    description: str | None = None
    description_ar: str | None = Field(default=None, description="الوصف بالعربي (اختياري)")
    image: str | None = None
    price: float = Field(gt=0, description="سعر الباقة ككل")
    is_active: bool = True
    start_date: date | None = None
    end_date: date | None = None
    items: list[BundleItemIn] = Field(min_length=1)
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "Burger Combo", "name_ar": "كومبو برجر",
        "description": "Burger + fries + drink", "description_ar": "برجر + بطاطس + مشروب",
        "price": 149, "is_active": True, "start_date": None, "end_date": None,
        "items": [{"product_id": 7, "quantity": 1}, {"product_id": 8, "quantity": 1}]}]})


class BundleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    name_ar: str | None = Field(default=None, max_length=150)
    description: str | None = None
    description_ar: str | None = None
    image: str | None = None
    price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None
    start_date: date | None = None
    end_date: date | None = None
    items: list[BundleItemIn] | None = Field(default=None, min_length=1)


class BundleItemOut(ORM):
    product: ProductOut
    quantity: int


class BundleOut(ORM):
    id: int
    name: str
    name_ar: str | None = None
    description: str | None
    description_ar: str | None = None
    image: str | None
    price: float
    original_price: float
    savings: float
    is_active: bool
    is_live: bool
    start_date: date | None
    end_date: date | None
    items: list[BundleItemOut]
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": 3, "name": "Burger Combo", "name_ar": "كومبو برجر",
        "description": "Burger + fries + drink", "description_ar": "برجر + بطاطس + مشروب",
        "image": None, "price": 149.0, "original_price": 175.0, "savings": 26.0,
        "is_active": True, "is_live": True, "start_date": None, "end_date": None,
        "items": [{"quantity": 1, "product": {
            "id": 7, "category_id": 1, "name": "Beef Burger", "name_ar": "برجر لحم",
            "description": "Grilled beef burger", "description_ar": "برجر لحم مشوي",
            "details": None, "details_ar": None, "price": 120.0, "image": None,
            "is_popular": False, "is_recommended": True, "is_available": True}}]}]})


# ---------- Cart ----------
class CartAddIn(BaseModel):
    product_id: int | None = None
    bundle_id: int | None = None
    quantity: int = Field(default=1, ge=1, le=50)

    @model_validator(mode="after")
    def exactly_one(self):
        if (self.product_id is None) == (self.bundle_id is None):
            raise ValueError("Send exactly one of product_id or bundle_id")
        return self


class CartUpdateIn(BaseModel):
    quantity: int = Field(ge=1, le=50)


class CartItemOut(BaseModel):
    id: int
    product: ProductOut | None = None
    bundle: BundleOut | None = None
    quantity: int
    line_total: float


class CartOut(BaseModel):
    items: list[CartItemOut]
    subtotal: float
    discount: float
    total: float
    items_count: int


# ---------- Orders ----------
class OrderCreate(BaseModel):
    delivery_address: str = Field(min_length=5)
    phone: str = Field(min_length=7, max_length=30)
    payment_method: PaymentMethod = PaymentMethod.cash
    notes: str | None = None


class OrderItemOut(ORM):
    product_id: int | None
    bundle_id: int | None
    product_name: str
    unit_price: float
    quantity: int


class OrderOut(ORM):
    id: int
    user_id: int
    status: OrderStatus
    payment_method: PaymentMethod
    delivery_address: str
    phone: str
    notes: str | None
    subtotal: float
    discount: float
    total: float
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ---------- Reviews ----------
class ReviewIn(BaseModel):
    product_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewOut(ORM):
    id: int
    user_id: int
    user_name: str
    product_id: int | None
    rating: int
    comment: str | None
    is_approved: bool
    created_at: datetime


# ---------- Complaints ----------
class ComplaintIn(BaseModel):
    order_id: int | None = None
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10)


class ComplaintUpdate(BaseModel):
    status: ComplaintStatus | None = None
    admin_response: str | None = None


class ComplaintOut(ORM):
    id: int
    user_id: int
    order_id: int | None
    subject: str
    message: str
    status: ComplaintStatus
    admin_response: str | None
    created_at: datetime
    updated_at: datetime


# ---------- Contact ----------
class ContactIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10)


class ContactOut(ORM, ContactIn):
    id: int
    is_read: bool
    created_at: datetime


# ---------- Festivals ----------
class FestivalIn(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str | None = None
    image: str | None = None
    discount_percent: int = Field(default=0, ge=0, le=100)
    start_date: date
    end_date: date
    is_active: bool = True


class FestivalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    image: str | None = None
    discount_percent: int | None = Field(default=None, ge=0, le=100)
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None


class FestivalOut(ORM, FestivalIn):
    id: int


# ---------- About / Home / Stats ----------
class AboutContent(BaseModel):
    story: str = ""
    story_ar: str | None = None
    mission: str = ""
    mission_ar: str | None = None
    address: str = ""
    phone: str = ""
    email: str = ""
    working_hours: str = ""
    facebook: str = ""
    instagram: str = ""
    map_embed_url: str = ""
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "story": "MOODS: your spot for fast food, juices & desserts.",
        "story_ar": "مودز: مكانك للوجبات السريعة والعصائر والحلويات.",
        "mission": "Save the moment.", "mission_ar": "احفظ اللحظة.",
        "address": "Qena, Egypt", "phone": "01000000000", "email": "moods.restaurant.cafe@gmail.com",
        "working_hours": "10:00 - 00:00", "facebook": "https://www.facebook.com/moodsqena",
        "instagram": "https://www.instagram.com/moodsqena", "map_embed_url": ""}]})


class HomeOut(BaseModel):
    categories: list[CategoryOut]
    popular_products: list[ProductOut]
    recommended_products: list[ProductOut]
    best_sellers: list[ProductOut]
    offers: list[BundleOut]
    festivals: list[FestivalOut]
    latest_reviews: list[ReviewOut]
    about: AboutContent
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "categories": [{"id": 1, "name": "Sandwiches", "name_ar": "ساندويتشات",
                        "description": "Freshly grilled sandwiches", "description_ar": "ساندويتشات مشوية طازجة",
                        "image": None, "sort_order": 0, "is_active": True, "show_on_home": True, "parent_id": None}],
        "popular_products": [{"id": 7, "category_id": 1, "name": "Beef Burger", "name_ar": "برجر لحم",
                              "description": "Grilled beef burger", "description_ar": "برجر لحم مشوي",
                              "details": "150g beef, cheddar", "details_ar": "150 جم لحم بقري، جبنة شيدر",
                              "price": 120.0, "image": None, "is_popular": True,
                              "is_recommended": False, "is_available": True}],
        "recommended_products": [], "best_sellers": [],
        "offers": [{"id": 3, "name": "Burger Combo", "name_ar": "كومبو برجر",
                    "description": "Burger + fries", "description_ar": "برجر + بطاطس", "image": None,
                    "price": 149.0, "original_price": 175.0, "savings": 26.0, "is_active": True,
                    "is_live": True, "start_date": None, "end_date": None, "items": []}],
        "festivals": [], "latest_reviews": [],
        "about": {"story": "MOODS: your spot for fast food, juices & desserts.",
                  "story_ar": "مودز: مكانك للوجبات السريعة والعصائر والحلويات.",
                  "mission": "Save the moment.", "mission_ar": "احفظ اللحظة.",
                  "address": "Qena, Egypt", "phone": "", "email": "moods.restaurant.cafe@gmail.com",
                  "working_hours": "", "facebook": "", "instagram": "", "map_embed_url": ""}}]})


class StatsOut(BaseModel):
    users: int
    customers: int
    orders: int
    pending_orders: int
    revenue: float
    open_complaints: int
    unread_messages: int
    pending_reviews: int
