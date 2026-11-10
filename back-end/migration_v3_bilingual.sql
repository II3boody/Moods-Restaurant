-- Arabic + English content support.  Run ONCE in Neon -> SQL Editor (safe to re-run).
-- Only ADDS nullable columns: existing rows are untouched, no data is deleted or rewritten.
-- Run this BEFORE deploying the new backend code.
-- (Alternative: `python -m app.migrate_bilingual` does exactly the same thing.)

BEGIN;

ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_ar        VARCHAR(100);
ALTER TABLE categories ADD COLUMN IF NOT EXISTS description_ar TEXT;

ALTER TABLE products   ADD COLUMN IF NOT EXISTS name_ar        VARCHAR(150);
ALTER TABLE products   ADD COLUMN IF NOT EXISTS description_ar TEXT;
ALTER TABLE products   ADD COLUMN IF NOT EXISTS details_ar     TEXT;

ALTER TABLE bundles    ADD COLUMN IF NOT EXISTS name_ar        VARCHAR(150);
ALTER TABLE bundles    ADD COLUMN IF NOT EXISTS description_ar TEXT;

COMMIT;

-- About page: NO migration needed. It is stored as JSON in site_content; story_ar / mission_ar
-- simply appear the first time an admin sends them via PUT/PATCH /api/v1/about.

-- OPTIONAL: Arabic names for the 5 seeded categories (only fills empty values, never overwrites).
-- UPDATE categories SET name_ar = 'ساندويتشات' WHERE name = 'Sandwiches' AND name_ar IS NULL;
-- UPDATE categories SET name_ar = 'وجبات'      WHERE name = 'Meals'      AND name_ar IS NULL;
-- UPDATE categories SET name_ar = 'إضافات'     WHERE name = 'Sides'      AND name_ar IS NULL;
-- UPDATE categories SET name_ar = 'حلويات'     WHERE name = 'Desserts'   AND name_ar IS NULL;
-- UPDATE categories SET name_ar = 'سيامي'      WHERE name = 'Seyami'     AND name_ar IS NULL;
