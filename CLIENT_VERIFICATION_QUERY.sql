-- ============================================================================
-- CLIENT VERIFICATION QUERY
-- Shows exactly what data from your PDF requirements is saved where
-- ============================================================================

-- View 1: Complete Deal Information with All Related Data
-- This shows one deal with all its images, categories, and related deals
SELECT 
    '=== MAIN DEAL INFORMATION (deals table) ===' as section,
    d.dealid as 'Deal ID',
    d.recid as 'Rec ID',
    d.url as 'URL',
    d.title as 'Title',
    d.price as 'Price',
    d.promo as 'Promo Code',
    d.category as 'Category',
    d.store as 'Store',
    d.deal as 'Deal',
    d.dealplus as 'Deal Plus',
    d.deallink as 'Deal Link',
    d.dealtext as 'Deal Text',
    d.dealhover as 'Deal Hover',
    d.published as 'Published',
    d.popularity as 'Popularity',
    d.staffpick as 'Staff Pick',
    LEFT(d.detail, 100) as 'Detail (first 100 chars)',
    LENGTH(d.raw_html) as 'Raw HTML Size (bytes)',
    d.created_at as 'Created At',
    d.updated_at as 'Updated At'
FROM deals d
ORDER BY d.created_at DESC
LIMIT 1;

-- View 2: Images for a Deal (deal_images table)
SELECT 
    '=== DEAL IMAGES (deal_images table) ===' as section,
    di.dealid as 'Deal ID',
    di.imageurl as 'Image URL',
    di.created_at as 'Created At'
FROM deal_images di
WHERE di.dealid = (SELECT dealid FROM deals ORDER BY created_at DESC LIMIT 1)
LIMIT 5;

-- View 3: Categories for a Deal (deal_categories table)
SELECT 
    '=== DEAL CATEGORIES (deal_categories table) ===' as section,
    dc.dealid as 'Deal ID',
    dc.category_name as 'Category Name',
    dc.category_id as 'Category ID',
    dc.category_url as 'Category URL',
    dc.category_title as 'Category Title',
    dc.created_at as 'Created At'
FROM deal_categories dc
WHERE dc.dealid = (SELECT dealid FROM deals ORDER BY created_at DESC LIMIT 1)
LIMIT 5;

-- View 4: Related Deals for a Deal (related_deals table)
SELECT 
    '=== RELATED DEALS (related_deals table) ===' as section,
    rd.dealid as 'Deal ID',
    rd.relatedurl as 'Related Deal URL',
    rd.created_at as 'Created At'
FROM related_deals rd
WHERE rd.dealid = (SELECT dealid FROM deals ORDER BY created_at DESC LIMIT 1)
LIMIT 5;

-- ============================================================================
-- SUMMARY STATISTICS
-- ============================================================================

SELECT 
    '=== DATABASE SUMMARY ===' as section,
    (SELECT COUNT(*) FROM deals) as 'Total Deals',
    (SELECT COUNT(*) FROM deal_images) as 'Total Images',
    (SELECT COUNT(DISTINCT dealid) FROM deal_images) as 'Deals with Images',
    (SELECT COUNT(*) FROM deal_categories) as 'Total Categories',
    (SELECT COUNT(DISTINCT dealid) FROM deal_categories) as 'Deals with Categories',
    (SELECT COUNT(*) FROM related_deals) as 'Total Related Deals',
    (SELECT COUNT(DISTINCT dealid) FROM related_deals) as 'Deals with Related Deals';

-- ============================================================================
-- FIELD COVERAGE CHECK
-- ============================================================================

SELECT 
    '=== FIELD COVERAGE ===' as section,
    'dealid' as field_name,
    COUNT(*) as total,
    COUNT(dealid) as filled,
    ROUND(COUNT(dealid) * 100.0 / COUNT(*), 1) as coverage_percent
FROM deals
UNION ALL
SELECT 'title', COUNT(*), COUNT(title), ROUND(COUNT(title) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'url', COUNT(*), COUNT(url), ROUND(COUNT(url) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'store', COUNT(*), COUNT(store), ROUND(COUNT(store) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'category', COUNT(*), COUNT(category), ROUND(COUNT(category) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'deal', COUNT(*), COUNT(deal), ROUND(COUNT(deal) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'dealplus', COUNT(*), COUNT(dealplus), ROUND(COUNT(dealplus) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'deallink', COUNT(*), COUNT(deallink), ROUND(COUNT(deallink) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'published', COUNT(*), COUNT(published), ROUND(COUNT(published) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'popularity', COUNT(*), COUNT(popularity), ROUND(COUNT(popularity) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'staffpick', COUNT(*), COUNT(staffpick), ROUND(COUNT(staffpick) * 100.0 / COUNT(*), 1) FROM deals
UNION ALL
SELECT 'detail', COUNT(*), COUNT(detail), ROUND(COUNT(detail) * 100.0 / COUNT(*), 1) FROM deals;





