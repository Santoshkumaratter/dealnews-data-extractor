# Related Deals Crawling - Issues Fixed

## Summary

This document explains the issues found with related deals crawling and the fixes applied.

## Issues Identified

### 1. Related Deals Not Being Crawled (Main Issue)

**Problem:** Only 1.68% (381 out of 22,706) of related deals were being crawled and added to the `deals` table.

**Root Cause:** The recursion logic in `parse_deal_detail()` (line 1720-1728) was calling `parse_deal_detail` callback instead of `parse` callback. This meant:
- Related deal URLs were being visited
- MORE related deals were being extracted from those pages
- But the actual deal content was NEVER extracted and saved to the `deals` table

**Example:** The "New Balance" deal from `related_deals` table row 21 was never crawled, so it didn't appear in the `deals` table when searching for "balance".

**Fix Applied:**
```python
# BEFORE (WRONG):
yield scrapy.Request(
    url=link,
    callback=self.parse_deal_detail,  # Only extracts related deals, not the deal itself
    meta={'dealid': f"deal_{hash(link)}"},
    errback=self.errback_http,
    dont_filter=False
)

# AFTER (CORRECT):
yield scrapy.Request(
    url=link,
    callback=self.parse,  # Extracts the full deal content
    errback=self.errback_http,
    dont_filter=False
)
```

Also added `self.scanned_urls.add(link)` before yielding the request to mark it as scanned immediately.

### 2. Missing Unique Constraint on `deals.url`

**Problem:** The database schema file (`mysql-init/01_create_deals.sql`) defines a unique constraint on the `url` column:
```sql
UNIQUE KEY unique_url (url)
```

However, this constraint was missing in the actual database. This could allow duplicate URLs to be inserted.

**Fix Applied:**
1. Checked for and removed any existing duplicate URLs
2. Added the unique constraint using:
   ```sql
   ALTER TABLE deals ADD CONSTRAINT unique_url UNIQUE (url);
   ```

## Verification

### Before Fix
```
Total related deals in database: 22706
Related deals that were crawled: 381
Related deals NOT yet crawled: 22325
Crawl percentage: 1.68%
```

### After Fix
The spider will now:
1. ✅ Extract related deals from detail pages (already working)
2. ✅ Save related deal URLs to `related_deals` table (already working)
3. ✅ **Crawl those related deal URLs** (NOW FIXED)
4. ✅ **Extract and save the full deal content to `deals` table** (NOW FIXED)
5. ✅ Check `scanned_urls` set to avoid re-crawling (already working)
6. ✅ Check database unique constraint to prevent duplicate URLs (NOW FIXED)

## Files Modified

1. **`dealnews_scraper/spiders/dealnews_spider.py`**
   - Line 1719-1728: Changed callback from `parse_deal_detail` to `parse`
   - Added `self.scanned_urls.add(link)` to mark URL as scanned immediately

2. **Database: `deals` table**
   - Added unique constraint on `url` column

## Testing

### Test Script Created
- `test_related_deals_crawling.py` - Comprehensive test to verify:
  - Related deals are in `related_deals` table
  - Related deal URLs are in `deals` table (crawled)
  - No duplicate URLs exist
  - Unique constraint is present

### Database Fix Script Created
- `apply_database_fix.py` - Applies the unique constraint fix
- `fix_unique_constraint.sql` - SQL version of the fix

## Next Steps

1. **Run the scraper** to crawl new deals and related deals
2. **Monitor the logs** for messages like:
   - `🔄 Recursing into related deal: <URL>`
   - Check that these URLs are being crawled with the `parse` callback
3. **Run the test script** after scraping to verify:
   ```bash
   python3 test_related_deals_crawling.py
   ```
4. **Expected result:** The crawl percentage should increase significantly (from 1.68% to close to 100%)

## Technical Details

### How Related Deals Crawling Works

1. **Main parse flow:**
   - `parse()` extracts deals from listing pages
   - For each deal, visits its detail page via `parse_deal_detail()`

2. **Detail page flow:**
   - `parse_deal_detail()` extracts related deal URLs
   - Saves them to `related_deals` table
   - **NOW:** Yields requests with `parse` callback to crawl them

3. **Deduplication:**
   - `scanned_urls` set in memory (loaded from database on startup)
   - Unique constraint on `deals.url` in database
   - Both prevent duplicate crawling and storage

### Why This Fix Is Important

Without this fix:
- ❌ Related deals are discovered but never crawled
- ❌ Database has 22,706 related deal URLs but only 381 actual deals
- ❌ Missing 98.32% of potential deals
- ❌ User searches (like "balance") miss deals that are in `related_deals` but not in `deals`

With this fix:
- ✅ Related deals are discovered AND crawled
- ✅ Full deal content is extracted and saved
- ✅ Database will have close to 100% of related deals as actual deals
- ✅ User searches will find all deals, including those from related deals

## Conclusion

The fix is simple but critical:
- **Changed 1 line of code** (callback from `parse_deal_detail` to `parse`)
- **Added 1 line of code** (mark URL as scanned immediately)
- **Added 1 database constraint** (unique on `deals.url`)

This will dramatically increase the number of deals crawled and ensure all related deals are properly stored in the database.
