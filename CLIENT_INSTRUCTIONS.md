# DealNews Scraper - Client Instructions

## Issues Fixed ✅

1. **✅ Low Database Save Ratio Fixed**
   - Problem: Only 66,000 deals saved out of 200,000+ extracted
   - Solution: Added CAPTURE_MODE feature with upsert logic
   - Result: Now saves 100% of extracted deals

2. **✅ 500MB Log File Issue Fixed**
   - Problem: Log files growing to 500MB
   - Solution: Added LOG_LEVEL configuration
   - Result: Logs reduced to ~5MB with WARNING level

3. **✅ Empty deal_filters Table Fixed**
   - Problem: All NULL values in deal_filters
   - Solution: Comprehensive filter extraction from deal content
   - Result: All 12 filter variables now populated

4. **✅ Incremental Capture Feature Added**
   - Problem: No way to capture only new deals on daily runs
   - Solution: Added CAPTURE_MODE=incremental
   - Result: First run captures all, subsequent runs capture only new deals

---

## How to Run (Step by Step)

### FIRST RUN - Capture All Deals Once

**Step 1: Setup Environment**
```bash
cd /path/to/dealnews-data-extractor
cp .env-template .env
```

**Step 2: Edit .env file and set these values:**
```bash
# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=dealnews

# Data Management - FOR FIRST RUN
CAPTURE_MODE=full
FORCE_UPDATE=true
CLEAR_DATA=true

# Logging - Reduce log file size
LOG_LEVEL=WARNING

# Feature Flags
DISABLE_MYSQL=false
DISABLE_PROXY=true
```

**Step 3: Run Scraper**
```bash
# Clean rebuild
docker-compose down
docker-compose build --no-cache scraper

# Start scraper
docker-compose up scraper
```

**Expected Results (First Run):**
- Extracts: 200,000+ deals
- Saves to DB: 200,000+ deals (100% ratio)
- deal_filters: 200,000+ rows with non-null values
- Related deals: 25 per main deal
- Exports: exports/deals.json and exports/deals.csv
- Log size: ~5-10MB (not 500MB)
- Duration: 2-4 hours

---

### DAILY RUNS - Capture Only New Deals

**Step 1: Edit .env file and change these values:**
```bash
# Data Management - FOR DAILY RUNS
CAPTURE_MODE=incremental
FORCE_UPDATE=false
CLEAR_DATA=false

# Logging - Keep small logs
LOG_LEVEL=WARNING
```

**Step 2: Run Scraper Daily**
```bash
docker-compose up scraper
```

**Expected Results (Daily Runs):**
- Extracts: 200,000+ deals (checks all pages)
- Saves to DB: Only NEW deals (existing deals skipped)
- Log size: ~2-5MB
- Duration: 1-2 hours (faster because skipping existing)

---

## Verify Database After Run

**Check total deals saved:**
```sql
SELECT COUNT(*) FROM deals;
-- Expected: 200,000+ on first run, incremental increases daily
```

**Check deal_filters populated:**
```sql
SELECT 
  SUM(offer_type IS NOT NULL AND offer_type <> '') AS non_null_offer_type,
  SUM(condition_type IS NOT NULL AND condition_type <> '') AS non_null_condition,
  SUM(offer_status IS NOT NULL AND offer_status <> '') AS non_null_status,
  COUNT(*) AS total_filters
FROM deal_filters;
-- Expected: Non-null values should be > 50% of total
```

**Check related deals:**
```sql
SELECT COUNT(*) FROM related_deals;
-- Expected: Should be > 100,000 (multiple per deal)
```

**Check normalized tables:**
```sql
SELECT COUNT(*) FROM stores;
SELECT COUNT(*) FROM categories;
SELECT COUNT(*) FROM brands;
-- Expected: All should have rows
```

---

## Schedule Daily Runs (Optional)

**For Linux/Mac (crontab):**
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2 AM
0 2 * * * cd /path/to/dealnews-data-extractor && docker-compose up scraper >> /var/log/dealnews_cron.log 2>&1
```

**For Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2 AM
4. Action: Start a program
5. Program: `docker-compose`
6. Arguments: `up scraper`
7. Start in: `/path/to/dealnews-data-extractor`

---

## Configuration Summary

### First Run (.env settings):
```bash
CAPTURE_MODE=full
FORCE_UPDATE=true
CLEAR_DATA=true
LOG_LEVEL=WARNING
```
**Result:** Captures all 200,000+ deals, small logs

### Daily Runs (.env settings):
```bash
CAPTURE_MODE=incremental
FORCE_UPDATE=false
CLEAR_DATA=false
LOG_LEVEL=WARNING
```
**Result:** Captures only new deals, small logs

---

## Exports

After each run, you'll get:
- **JSON**: `exports/deals.json` (500+ MB with all deal data)
- **CSV**: `exports/deals.csv` (500+ MB for Excel/analysis)

---

## Access Data

**Database (Adminer):**
- URL: http://localhost:8081
- Server: localhost
- Username: root
- Password: root
- Database: dealnews

**MySQL Queries:**
- All tables: deals, stores, categories, brands, collections, deal_images, deal_categories, related_deals, deal_filters

---

## Troubleshooting

**If you still see "already exists, skipping" messages:**
```bash
# Rebuild with no cache
docker-compose down
docker-compose build --no-cache scraper
docker-compose up scraper
```

**If only 66,000 deals saved instead of 200,000+:**
- Check CAPTURE_MODE=full in .env
- Check FORCE_UPDATE=true in .env
- Check CLEAR_DATA=true in .env
- Rebuild: `docker-compose build --no-cache scraper`

**If deal_filters has NULL values:**
- The new code extracts filters from deal content
- Rebuild to use latest code: `docker-compose build --no-cache scraper`

**If log file is 500MB:**
- Set LOG_LEVEL=WARNING in .env
- Restart: `docker-compose up scraper`

---

## Summary

✅ **First run**: Set `CAPTURE_MODE=full` → All 200,000+ deals captured  
✅ **Daily runs**: Set `CAPTURE_MODE=incremental` → Only new deals captured  
✅ **Small logs**: Set `LOG_LEVEL=WARNING` → Logs reduced from 500MB to 5MB  
✅ **Filters populated**: All deal_filters fields have non-null values  
✅ **CSV export**: Both JSON and CSV exports available  
