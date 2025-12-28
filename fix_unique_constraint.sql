-- Add unique constraint on deals.url to prevent duplicate URLs
-- This ensures that each URL can only appear once in the deals table

-- First, check if there are any duplicate URLs and remove them
-- Keep only the first occurrence of each URL
DELETE d1 FROM deals d1
INNER JOIN deals d2 
WHERE d1.id > d2.id AND d1.url = d2.url AND d1.url IS NOT NULL;

-- Now add the unique constraint
ALTER TABLE deals
ADD CONSTRAINT unique_url UNIQUE (url);

-- Verify the constraint was added
SHOW CREATE TABLE deals;
