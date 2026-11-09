import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routers import admin, auth, cart, complaints, content, menu, orders, reviews

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

app = FastAPI(title=settings.PROJECT_NAME, description=DESCRIPTION, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# فولدر الصور للتطوير المحلي بس (فايل سيستم Vercel read-only)
if not os.getenv("VERCEL"):
    Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

API = "/api/v1"
for r in (auth.router, menu.categories_router, menu.products_router, cart.router, orders.router,
          reviews.router, complaints.router, content.contact_router, content.festivals_router,
          content.about_router, content.home_router, admin.router):
    app.include_router(r, prefix=API)


@app.get("/", tags=["Health"])
def root():
    return {"message": "MOODS API is running", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
