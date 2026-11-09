"""بيتشغل أوتوماتيك عند تشغيل التطبيق: بيعمل السوبر أدمن + داتا مبدئية لو الداتابيز فاضية."""
import json

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Category, Product, Role, SiteContent, User

CATEGORIES = ["Sandwiches", "Meals", "Sides", "Desserts", "Seyami"]

# (name, price, category, image) - من قسم "popular" في الموقع الحالي. كمّل باقي المنيو من لوحة الأدمن.
PRODUCTS = [
    ("Chicken Ranchy", 109, "Sandwiches", "imgs/most_wanted/chickenranchy.png"),
    ("Classic", 89, "Sandwiches", "imgs/most_wanted/classic.png"),
    ("Twister", 75, "Sandwiches", "imgs/most_wanted/twister.png"),
    ("Boom", 109, "Sandwiches", "imgs/most_wanted/boom.png"),
    ("Mix Fries", 70, "Sides", "imgs/most_wanted/mix fries.png"),
    ("Rizo", 70, "Meals", "imgs/most_wanted/rizo.png"),
    ("Waffel", 60, "Desserts", "imgs/most_wanted/waffel.png"),
    ("Big Fries", 30, "Sides", "imgs/most_wanted/bigfries.png"),
    ("Crespy Strips", 107, "Meals", "imgs/most_wanted/crespystrips.png"),
    ("Chicken Turky", 117, "Sandwiches", "imgs/most_wanted/Chickenturky.png"),
]

ABOUT = {
    "story": "MOODS: your spot for fast food, juices & desserts.",
    "mission": "Save the moment.",
    "address": "Qena, Egypt",
    "phone": "",
    "email": "moods.restaurant.cafe@gmail.com",
    "working_hours": "",
    "facebook": "https://www.facebook.com/moodsqena",
    "instagram": "https://www.instagram.com/moodsqena",
    "map_embed_url": "",
}


def seed() -> None:
    with SessionLocal() as db:
        email = settings.FIRST_SUPERADMIN_EMAIL.lower()
        if not db.scalar(select(User).where(User.email == email)):
            db.add(User(full_name=settings.FIRST_SUPERADMIN_NAME, email=email,
                        password_hash=hash_password(settings.FIRST_SUPERADMIN_PASSWORD),
                        role=Role.super_admin))

        if not db.scalar(select(Category)):
            cats = {n: Category(name=n, sort_order=i) for i, n in enumerate(CATEGORIES)}
            db.add_all(cats.values())
            db.flush()
            db.add_all(Product(name=n, price=p, category_id=cats[c].id, image=img, is_popular=True)
                       for n, p, c, img in PRODUCTS)

        if not db.get(SiteContent, "about"):
            db.add(SiteContent(key="about", value=json.dumps(ABOUT, ensure_ascii=False)))
        db.commit()
