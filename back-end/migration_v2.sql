-- شغّله على Neon (SQL Editor) مرة واحدة، بعد ما تشغّل:  python -m app.seed
-- (python -m app.seed بيعمل الجداول الجديدة bundles و bundle_items)
-- آمن لو اتشغّل أكتر من مرة (IF NOT EXISTS)

ALTER TABLE categories ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES categories(id) ON DELETE SET NULL;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS show_on_home BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX IF NOT EXISTS ix_categories_parent_id ON categories(parent_id);

ALTER TABLE products ADD COLUMN IF NOT EXISTS details TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_recommended BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_data BYTEA;
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_type VARCHAR(50);

ALTER TABLE cart_items ALTER COLUMN product_id DROP NOT NULL;
ALTER TABLE cart_items ADD COLUMN IF NOT EXISTS bundle_id INTEGER REFERENCES bundles(id) ON DELETE CASCADE;
ALTER TABLE cart_items ADD CONSTRAINT uq_cart_user_bundle UNIQUE (user_id, bundle_id);

ALTER TABLE order_items ADD COLUMN IF NOT EXISTS bundle_id INTEGER REFERENCES bundles(id) ON DELETE SET NULL;
