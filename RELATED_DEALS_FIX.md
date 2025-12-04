# Related Deals Extraction Fix

## ✅ Fixed Issues

### Problem
Related deals were not being captured from DealNews detail pages (e.g., `https://www.dealnews.com/.../21791913.html`).

### Root Causes
1. **Wrong URL extraction**: `item['url']` was set to listing page URL, not deal detail page URL
2. **Wrong URL used for detail page visits**: Code was using `deallink` (external merchant URL) instead of DealNews detail page URL
3. **Limited selectors**: Related deals extraction didn't have enough selectors for DealNews detail pages

## 🔧 Changes Made

### 1. Fixed Detail Page URL Extraction (Line ~698)
**Before:**
```python
item['url'] = response.url  # This was the listing page URL
```

**After:**
```python
# Extract DealNews detail page URL from deal container
deal_detail_url = None
detail_url_selectors = [
    'a[href*=".html"]::attr(href)',  # Links ending in .html (DealNews detail pages)
    '.title-link::attr(href)',  # Title link
    '.deal-title a::attr(href)',  # Deal title link
    'a[href*="/deals/"]::attr(href)',  # Deal links
    'h2 a::attr(href), h3 a::attr(href)',  # Headings with links
]

for selector in detail_url_selectors:
    url = deal.css(selector).get()
    if url:
        if not url.startswith('http'):
            url = response.urljoin(url)
        # Check if it's a DealNews detail page
        if '.html' in url and 'dealnews.com' in url:
            deal_detail_url = url
            break

item['url'] = deal_detail_url or response.url  # Fallback to listing page
```

### 2. Fixed Detail Page Visit Logic (Line ~241)
**Before:**
```python
deallink = item.get('deallink') or item.get('url', '')  # Using external merchant URL
if '/lw/click.html' in deallink:
    # Try to get actual URL...
```

**After:**
```python
# Visit detail page for related deals (use DealNews detail page URL)
deal_detail_url = item.get('url', '')  # This is now the DealNews detail page URL
if deal_detail_url and self.detail_pages_visited < self.max_detail_pages:
    # Only visit if it's a DealNews detail page
    if '.html' in deal_detail_url and 'dealnews.com' in deal_detail_url:
        # Visit every deal's detail page to get all related deals
        yield scrapy.Request(
            url=deal_detail_url,
            callback=self.parse_deal_detail,
            meta={'dealid': item['dealid'], 'item': item},
            errback=self.errback_http,
            dont_filter=True
        )
        self.detail_pages_visited += 1
```

### 3. Improved Related Deals Extraction (Line ~1437)
**Added more selectors for DealNews detail pages:**
```python
related_selectors = [
    # DealNews specific patterns - look for .html links (detail pages)
    'a[href*=".html"]::attr(href)',  # All links ending in .html
    '.related-deals a[href*=".html"]::attr(href)',
    '.related-items a[href*=".html"]::attr(href)',
    '.similar-deals a[href*=".html"]::attr(href)',
    'section[class*="related"] a[href*=".html"]::attr(href)',
    'aside a[href*=".html"]::attr(href)',  # Sidebar deals
    '.recommended a[href*=".html"]::attr(href)',
    '.deal-list a[href*=".html"]::attr(href)',
    # ... and more
]
```

### 4. Improved URL Validation (Line ~1497)
**Before:**
```python
if '/deals/' in link or '/deal/' in link:
```

**After:**
```python
# Only process valid DealNews deal URLs
is_dealnews_deal = (
    ('.html' in link and 'dealnews.com' in link) or  # DealNews detail page
    ('/deals/' in link and 'dealnews.com' in link) or  # DealNews deals listing
    ('/deal/' in link and 'dealnews.com' in link)  # Alternative deal pattern
)

if is_dealnews_deal:
    # Save related deal
```

## 📊 Expected Results

After these fixes:
- ✅ DealNews detail page URLs are correctly extracted
- ✅ Detail pages are visited for all deals (not just every 3rd)
- ✅ Related deals are extracted from detail pages using improved selectors
- ✅ Related deals are saved to `related_deals` table

## 🧪 Testing

To test the fix:
1. Run the scraper: `python3 run_scraper.py`
2. Check related deals in database:
   ```sql
   SELECT COUNT(*) FROM related_deals;
   SELECT * FROM related_deals WHERE dealid = '21791913' LIMIT 10;
   ```

## 📝 Notes

- Detail pages are now visited for **every deal** (changed from every 3rd deal)
- This will increase the number of requests but ensures all related deals are captured
- The `max_detail_pages` limit (5000) still applies to prevent excessive requests

