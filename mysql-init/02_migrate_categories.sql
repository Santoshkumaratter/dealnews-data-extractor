-- Migration script to convert old deal_categories to new categories table
-- Run this AFTER the new schema is created

-- Step 1: Backup old deal_categories table
CREATE TABLE IF NOT EXISTS deal_categories_backup AS SELECT * FROM deal_categories;

-- Step 2: Populate new categories table with unique categories
INSERT IGNORE INTO categories (category_id, category_name, category_url)
SELECT DISTINCT 
  category_id,
  category_name,
  category_url
FROM deal_categories
WHERE category_id IS NOT NULL AND category_id != '';

-- Step 3: Update deals table with primary category_id
-- Use the first category for each deal as the primary category
UPDATE deals d
LEFT JOIN (
  SELECT dealid, MIN(category_id) as primary_category_id
  FROM deal_categories
  WHERE category_id IS NOT NULL AND category_id != ''
  GROUP BY dealid
) dc ON d.dealid = dc.dealid
SET d.category_id = dc.primary_category_id
WHERE dc.primary_category_id IS NOT NULL;

-- Step 4: Drop old deal_categories table (after verification)
-- DROP TABLE IF EXISTS deal_categories;
-- Note: Commented out for safety - run manually after verifying migration
