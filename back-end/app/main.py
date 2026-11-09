from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import admin, auth, cart, complaints, content, menu, orders, reviews
from app.seed import seed

DESCRIPTION = """
Backend لمطعم **MOODS Restaurant & Cafe**.

### الأدوار (Roles)
| Role | الصلاحيات |
|---|---|
| `customer` | تسجيل/دخول، كارت، أوردرز، ريفيو، شكاوى |
| `admin` | إدارة المنيو والأوردرات والشكاوى والريفيوهات والرسائل والمهرجانات والـ About |
| `super_admin` | كل حاجة + إنشاء/ترقية الأدمنز |

اضغط **Authorize** فوق وادخل الإيميل والباسورد عشان تجرب الـ endpoints المحمية.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed()
    yield


app = FastAPI(title=settings.PROJECT_NAME, description=DESCRIPTION, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

API = "/api/v1"
for r in (auth.router, menu.categories_router, menu.products_router, cart.router, orders.router,
          reviews.router, complaints.router, content.contact_router, content.festivals_router,
          content.about_router, content.home_router, admin.router):
    app.include_router(r, prefix=API)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
