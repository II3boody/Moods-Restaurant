"""ينقل الصور الموجودة لـ Cloudinary:

    python -m app.migrate_images

1) منتجات/عروض صورها متخزنة في الداتابيز  -> بترفعها على Cloudinary وبتفضّي العمود (يوفّر مساحة Neon).
2) منتجات الـ seed اللي صورها مسار قديم زي imgs/most_wanted/... -> بتجيبها من موقعك القديم (GitHub Pages).
آمن تشغّله أكتر من مرة: اللي اتنقل قبل كده بيتخطّاه.
"""
from urllib.parse import quote

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Bundle, Product
from app.services import media

OLD_SITE = "https://ii3boody.github.io/Moods-Resturat/"


def run() -> None:
    if not media.enabled():
        raise SystemExit("Set CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET in .env first")
    done = failed = 0
    with SessionLocal() as db:
        for model, folder in ((Product, "products"), (Bundle, "bundles")):
            for row in db.scalars(select(model)).all():
                label = f"{folder}#{row.id} {row.name}"
                try:
                    if row.image_data:  # مخزنة في الداتابيز
                        row.image = media.upload(row.image_data, folder)
                        row.image_data = row.image_type = None
                    elif row.image and not row.image.startswith(("http://", "https://", "/")):
                        row.image = media.upload(OLD_SITE + quote(row.image), folder)  # مسار قديم
                    else:
                        continue
                    db.commit()
                    done += 1
                    print(f"ok      {label}")
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    failed += 1
                    print(f"FAILED  {label}: {exc}")
    print(f"\nMigrated: {done}, failed: {failed}")
    if failed:
        print("اللي فشل ارفعه يدوي من POST /products/{id}/image")


if __name__ == "__main__":
    run()
