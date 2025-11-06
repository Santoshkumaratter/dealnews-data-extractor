# DealNews Scraper

A production-ready Scrapy-based web scraper for extracting deals from dealnews.com. Optimized to extract 100,000+ deals with full data normalization into MySQL.

## Features

- ✅ Scrapy framework with webshare.io proxy support
- ✅ Complete data normalization (deals, images, categories, related deals)
- ✅ Robust parsing with CSS/XPath selectors + raw HTML snapshot for audit
- ✅ Proxy middleware with retry/backoff, rotating UA, AutoThrottle, 429 handling
- ✅ Daily cron job setup for automated runs
- ✅ Dockerized with docker-compose (scraper, MySQL, phpMyAdmin)
- ✅ CSV/JSON exports for debugging
- ✅ Unit tests for parser

## Quick Start - Final Setup Instructions

### Step 1: Setup Environment

```bash
# Copy environment file
cp env.example .env

# Edit .env file with your MySQL credentials
# Set MYSQL_PASSWORD=your_password (or leave empty if no password)
# Set DISABLE_PROXY=true for local testing (or configure webshare.io proxy)
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Initialize Database (REQUIRED - Run First!)

```bash
python3 init_database.py
```

This creates:
- `dealnews` database
- `deals` table (main deal information)
- `deal_images` table (multiple images per deal)
- `deal_categories` table (multiple categories per deal)
- `related_deals` table (related deals per deal)

**⚠️ IMPORTANT: Always run this step first before scraping!**

### Step 4: Run Scraper (100,000+ Deals)

```bash
# Run the scraper (target: 100,000+ deals, optimized for speed)
python3 run_scraper.py
```

**Expected Time:** 2-4 hours for 100,000+ deals (depending on network speed)

**Progress Monitoring:**
- Check progress: `python3 verify_mysql.py`
- View logs: `tail -f logs/scraper_run.log`

### Step 5: Verify Results

```bash
# Check database statistics
python3 verify_mysql.py
```

This will show:
- Total deals saved
- Total images
- Total categories
- Total related deals
- Top categories and stores

### Step 6: Setup Daily Cron Job (Optional)

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

This sets up a daily cron job to run at 2:00 AM.

## Quick Commands Summary

```bash
# 1. Initialize database (run first!)
python3 init_database.py

# 2. Run scraper (100k+ deals)
python3 run_scraper.py

# 3. Check progress
python3 verify_mysql.py

# 4. View logs
tail -f logs/scraper_run.log
```

## Database Schema

### Tables

#### `deals` - Main deal information
- `id` - Auto-increment primary key
- `dealid` - Unique deal identifier (VARCHAR(50), UNIQUE)
- `recid` - Recommendation ID
- `url` - Source URL
- `title` - Deal title
- `price` - Deal price
- `promo` - Promo code/information
- `category` - Primary category (single value)
- `store` - Store name (e.g., "Amazon")
- `deal` - Deal text (e.g., "Up to 80% off")
- `dealplus` - Additional deal info (e.g., "free shipping w/ Prime")
- `deallink` - Direct deal link
- `dealtext` - Deal description text
- `dealhover` - Hover text
- `published` - Publication timestamp
- `popularity` - Popularity rating (e.g., "5/5")
- `staffpick` - Staff pick status
- `detail` - Full deal description
- `raw_html` - Raw HTML snapshot for audit
- `created_at` - Record creation timestamp
- `updated_at` - Record update timestamp

#### `deal_images` - Multiple images per deal
- `id` - Auto-increment primary key
- `dealid` - Foreign key to deals.dealid
- `imageurl` - Image URL (TEXT)
- `created_at` - Record creation timestamp
- **Unique constraint**: `(dealid, imageurl)` - prevents duplicate images

#### `deal_categories` - Multiple categories per deal
- `id` - Auto-increment primary key
- `dealid` - Foreign key to deals.dealid
- `category_id` - Category ID (e.g., "142" from URL /c142/)
- `category_name` - Category name (e.g., "Electronics", "Amazon Prime Day")
- `category_url` - Category URL
- `category_title` - Category title
- `created_at` - Record creation timestamp

#### `related_deals` - Related deals per deal
- `id` - Auto-increment primary key
- `dealid` - Foreign key to deals.dealid
- `relatedurl` - Related deal URL (TEXT)
- `created_at` - Record creation timestamp
- **Unique constraint**: `(dealid, relatedurl)` - prevents duplicate related deals

## Sample Queries

### Get all deals with images

```sql
SELECT d.*, COUNT(di.id) as image_count
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
GROUP BY d.id
ORDER BY d.created_at DESC
LIMIT 10;
```

### Get deals with all categories

```sql
SELECT d.dealid, d.title, d.store, 
       GROUP_CONCAT(dc.category_name SEPARATOR ', ') as categories
FROM deals d
LEFT JOIN deal_categories dc ON d.dealid = dc.dealid
GROUP BY d.dealid, d.title, d.store
LIMIT 10;
```

### Get deals by store with image count

```sql
SELECT d.store, COUNT(DISTINCT d.dealid) as deal_count,
       COUNT(DISTINCT di.id) as total_images
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
WHERE d.store IS NOT NULL AND d.store != ''
GROUP BY d.store
ORDER BY deal_count DESC
LIMIT 10;
```

### Get deals with related deals

```sql
SELECT d.dealid, d.title, COUNT(rd.id) as related_count
FROM deals d
LEFT JOIN related_deals rd ON d.dealid = rd.dealid
GROUP BY d.dealid, d.title
HAVING related_count > 0
ORDER BY related_count DESC
LIMIT 10;
```

### Get all images for a specific deal

```sql
SELECT di.*
FROM deal_images di
WHERE di.dealid = 'your_deal_id'
ORDER BY di.created_at;
```

### Get all categories for a specific deal

```sql
SELECT dc.*
FROM deal_categories dc
WHERE dc.dealid = 'your_deal_id'
ORDER BY dc.category_name;
```

### Search deals by category

```sql
SELECT DISTINCT d.*
FROM deals d
JOIN deal_categories dc ON d.dealid = dc.dealid
WHERE dc.category_name LIKE '%Electronics%'
ORDER BY d.created_at DESC
LIMIT 20;
```

### Get deals with staff picks

```sql
SELECT d.*, COUNT(di.id) as image_count
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
WHERE d.staffpick IS NOT NULL AND d.staffpick != ''
GROUP BY d.id
ORDER BY d.created_at DESC
LIMIT 10;
```

## Configuration

Edit `.env` file to configure:

### MySQL Settings
- `MYSQL_HOST` - MySQL host (default: localhost)
- `MYSQL_PORT` - MySQL port (default: 3306)
- `MYSQL_USER` - MySQL user (default: root)
- `MYSQL_PASSWORD` - MySQL password
- `MYSQL_DATABASE` - Database name (default: dealnews)

### Scrapy Settings
- `DOWNLOAD_DELAY` - Delay between requests (default: 0.05)
- `CONCURRENT_REQUESTS` - Concurrent requests (default: 100)
- `CONCURRENT_REQUESTS_PER_DOMAIN` - Per-domain concurrency (default: 50)
- `AUTOTHROTTLE_ENABLED` - Enable AutoThrottle (default: true)
- `AUTOTHROTTLE_TARGET_CONCURRENCY` - Target concurrency (default: 30.0)

### Proxy Settings (webshare.io)
- `PROXY_HOST` - Proxy host (default: p.webshare.io)
- `PROXY_PORT` - Proxy port (default: 80)
- `PROXY_USER` - Proxy username
- `PROXY_PASS` - Proxy password
- `DISABLE_PROXY` - Disable proxy for local testing (default: true)

### Feature Flags
- `DISABLE_MYSQL` - Disable MySQL storage (default: false)
- `CLEAR_DATA` - Clear existing data before scraping (default: false)

## Docker Setup

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop all services
docker-compose down
```

### Services

- **MySQL**: Port 3306
- **phpMyAdmin**: Port 8081 (http://localhost:8081)
- **Scraper**: Runs on startup

## Output

- **MySQL Database**: All deals saved to normalized tables
- **JSON Export**: `exports/deals.json` (if DISABLE_MYSQL=true)
- **CSV Export**: `exports/deals.csv` (if DISABLE_MYSQL=true)
- **Logs**: `logs/scraper_run.log`

## Running Tests

```bash
python3 -m pytest tests/
# or
python3 tests/test_parser.py
```

## Performance

- **Target**: 100,000+ deals
- **Expected Time**: 2-4 hours for 100,000+ deals (depending on network speed)
- **Concurrency**: 64 concurrent requests (optimized for speed)
- **Rate Limiting**: AutoThrottle enabled with configurable delays
- **Proxy Rotation**: Automatic via webshare.io middleware
- **Retry Logic**: Automatic retry with exponential backoff
- **Pagination**: Automatic deep pagination to reach 100k+ deals

## Requirements

- Python 3.9+
- MySQL 8.0+ (running and accessible)
- See `requirements.txt` for Python dependencies

## Troubleshooting

### MySQL Connection Error
- Verify MySQL is running: `mysql -u root -p`
- Check credentials in `.env` file
- Ensure MySQL user has permissions to create databases

### No Deals Scraped
- Check internet connection
- Verify dealnews.com is accessible
- Check scraper logs in console output
- Try reducing `CONCURRENT_REQUESTS` in `.env` if getting blocked

### Proxy Issues
- Verify webshare.io credentials in `.env`
- Set `DISABLE_PROXY=true` for local testing
- Check proxy logs in scraper output

## Files Structure

```
dealnews-data-extractor/
├── dealnews_scraper/          # Scrapy project
│   ├── spiders/               # Spiders
│   ├── items.py               # Item definitions
│   ├── middlewares.py         # Proxy middleware
│   ├── normalized_pipeline.py # MySQL pipeline
│   └── settings.py            # Scrapy settings
├── mysql-init/                # Database initialization
│   └── 01_create_deals.sql    # Table creation script
├── tests/                     # Unit tests
│   └── test_parser.py         # Parser tests
├── exports/                   # JSON/CSV exports
├── logs/                      # Log files
├── docker-compose.yml         # Docker configuration
├── init_database.py           # Database initialization script
├── run_scraper.py             # Scraper runner
├── verify_mysql.py            # Verification script
├── run_full_test.py           # Full test script
├── setup_cron.sh              # Cron setup script
└── README.md                  # This file
```

## License

This project is for educational and commercial use.
