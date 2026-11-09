# MOODS Restaurant & Cafe — Backend (FastAPI)

## التشغيل
```bash
python -m venv venv
source venv/bin/activate        # ويندوز: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # وغيّر SECRET_KEY وباسورد السوبر أدمن
uvicorn app.main:app --reload
```
- الدوكيومنتيشن (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json  ← تقدر تولّد منه Types للـ Next.js

أول تشغيل بيعمل الجداول + السوبر أدمن (من `.env`) + الأقسام والمنتجات من الموقع القديم + محتوى About مبدئي.

## الأدوار
| Role | يعمل إيه |
|---|---|
| customer | تسجيل، لوجين، كارت، أوردرز، ريفيو، شكاوى |
| admin | منيو، أوردرز، شكاوى، ريفيوهات، رسائل Contact، Festivals، About، إيقاف العملاء |
| super_admin | كل اللي فوق + إنشاء/ترقية/تنزيل الأدمنز |

## الصفحات ← الـ Endpoints (كلهم تحت `/api/v1`)
| صفحة الفرونت | Endpoints |
|---|---|
| Home | `GET /home` (popular + categories + festivals + reviews + about في request واحد) |
| Products / Menu | `GET /categories`, `GET /products?category_id=&search=&popular=&page=`, `GET /products/{id}` |
| Login | `POST /auth/login` (form: username=email, password) ← `access_token` + `refresh_token` |
| Register | `POST /auth/register` |
| Forgot password | `POST /auth/forgot-password` |
| Reset password | `POST /auth/reset-password` (token من اللينك: `/reset-password?token=...`) |
| Profile | `GET/PATCH /auth/me`, `POST /auth/change-password` |
| Cart | `GET /cart`, `POST /cart/items`, `PATCH /cart/items/{product_id}`, `DELETE /cart/items/{product_id}`, `DELETE /cart` |
| Order | `POST /orders`, `GET /orders/me`, `GET /orders/{id}`, `POST /orders/{id}/cancel` |
| Review | `GET /reviews`, `POST /reviews` (بيظهر بعد موافقة الأدمن) |
| Complaint | `POST /complaints`, `GET /complaints/me` |
| Contact | `POST /contact` (public) |
| About | `GET /about` |
| Festival | `GET /festivals` (الخصم الأعلى النشط بيتطبق أوتوماتيك على الكارت والأوردر) |

### لوحة الأدمن
`GET /admin/stats`, `GET /admin/users`, `PATCH /admin/users/{id}/active`,
CRUD على `/categories` `/products` `/festivals`, `PUT /about`,
`GET /orders` + `PATCH /orders/{id}/status`, `GET /complaints` + `PATCH /complaints/{id}`,
`GET /reviews/admin/all` + `PATCH /reviews/{id}/approve`, `GET /contact` + `PATCH /contact/{id}/read`,
`POST /products/{id}/image` (رفع صورة).

### سوبر أدمن
`POST /admin/users` (إنشاء أدمن)، `PATCH /admin/users/{id}/role`.

## الـ Auth في Next.js
ابعت `Authorization: Bearer <access_token>`. لما يرجع 401 استخدم `POST /auth/refresh` بالـ refresh_token.

## ملاحظات
- Reset password: لو SMTP مش متظبط اللينك بيتطبع في الكونسول.
- الداتابيز SQLite للتطوير. للبروودكشن غيّر `DATABASE_URL` لـ PostgreSQL، ويفضل تضيف Alembic للـ migrations.
- الأسعار بتتخزن Numeric ومبنية على `OrderItem` snapshot عشان تغيير السعر بعدين ميغيرش الأوردرات القديمة.
- التست: `pytest -q`


## تحديث v2: أقسام فرعية، عروض، أكتر طلباً
- **أقسام فرعية:** `POST /categories` بـ `parent_id`. الشجرة جاهزة من `GET /categories/tree`. فلترة المنتجات بالقسم الأب بتشمل الفرعي.
- **المنتج:** `details` (تفاصيل طويلة) + `description` + `is_popular` + `is_recommended` + `is_available`. التعديل بـ `PATCH /products/{id}`، رفع الصورة بـ `POST /products/{id}/image` (متخزنة في الداتابيز، 2MB كحد أقصى).
- **أكتر طلباً:** `GET /products/best-sellers?days=30`، محسوبة أوتوماتيك من الأوردرات.
- **العروض (باكدجات):** `/bundles` (admin يعمل برجر + بطاطس بسعر واحد). العميل بيضيفها للكارت بـ `bundle_id`.
- **الكارت:** التعديل والحذف بقى بـ `item_id` مش `product_id`.
- **Home:** `categories` (الأب بس وبـ `show_on_home`)، `popular_products`، `recommended_products`، `best_sellers`، `offers`، `festivals`، `latest_reviews`، `about`.
- **ترقية الداتابيز الموجودة على Neon:** شغّل `python -m app.seed` ثم محتوى `migration_v2.sql` في SQL Editor.
