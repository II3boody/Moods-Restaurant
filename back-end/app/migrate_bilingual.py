"""Safe, idempotent schema update for Arabic/English content.

    python -m app.migrate_bilingual

- Adds ONLY new nullable columns (name_ar, description_ar, details_ar). No data is touched or deleted.
- Safe to run many times: a column that already exists is skipped.
- Works on PostgreSQL (Neon) and SQLite.
- Run it BEFORE deploying the new code (old code simply ignores the extra columns).
"""
from sqlalchemy import inspect, text

import app.models  # noqa: F401  (registers the tables)
from app.core.database import Base, engine

NEW_COLUMNS = {
    "categories": [("name_ar", "VARCHAR(100)"), ("description_ar", "TEXT")],
    "products": [("name_ar", "VARCHAR(150)"), ("description_ar", "TEXT"), ("details_ar", "TEXT")],
    "bundles": [("name_ar", "VARCHAR(150)"), ("description_ar", "TEXT")],
}


def run() -> None:
    Base.metadata.create_all(bind=engine)  # only creates tables that don't exist yet
    inspector = inspect(engine)
    with engine.begin() as conn:  # one transaction: all or nothing
        for table, columns in NEW_COLUMNS.items():
            existing = {c["name"] for c in inspector.get_columns(table)}
            for name, ddl in columns:
                if name in existing:
                    print(f"skip   {table}.{name} (already exists)")
                else:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
                    print(f"added  {table}.{name}")
    print("Bilingual schema is up to date. About content needs no migration (stored as JSON).")


if __name__ == "__main__":
    run()
