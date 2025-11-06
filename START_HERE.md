# DealNews Scraper - Quick Start Guide

## 🚀 Final Setup Instructions for Client

### Prerequisites
- Python 3.9+
- MySQL 8.0+ (running and accessible)
- Internet connection

### Step-by-Step Setup

#### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2. Configure Environment
```bash
# Copy environment file
cp env.example .env

# Edit .env file with your MySQL credentials
# Set MYSQL_PASSWORD=your_password (or leave empty if no password)
# Set DISABLE_PROXY=true for local testing
```

#### 3. Initialize Database (REQUIRED - Run First!)
```bash
python3 init_database.py
```

This creates all required tables in MySQL.

#### 4. Run Scraper (100,000+ Deals)
```bash
python3 run_scraper.py
```

**Expected Time:** 2-4 hours for 100,000+ deals

**Progress Monitoring:**
```bash
# Check progress in another terminal
python3 verify_mysql.py

# View live logs
tail -f logs/scraper_run.log
```

#### 5. Verify Results
```bash
python3 verify_mysql.py
```

## 📊 Quick Commands

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

## 🎯 Target: 100,000+ Deals

The scraper is optimized to extract 100,000+ deals in 2-4 hours with:
- High concurrency (64 concurrent requests)
- AutoThrottle for optimal speed
- Automatic pagination
- Proxy support (webshare.io)
- Retry logic for reliability

## 📁 Database Tables

- `deals` - Main deal information
- `deal_images` - Multiple images per deal
- `deal_categories` - Multiple categories per deal
- `related_deals` - Related deals per deal

## 🔧 Troubleshooting

### MySQL Connection Error
- Verify MySQL is running: `mysql -u root -p`
- Check credentials in `.env` file
- Ensure MySQL user has permissions

### No Deals Scraped
- Check internet connection
- Verify dealnews.com is accessible
- Check scraper logs: `tail -f logs/scraper_run.log`

### Slow Scraping
- Increase `CONCURRENT_REQUESTS` in `.env` (default: 64)
- Decrease `DOWNLOAD_DELAY` in `.env` (default: 0.1)
- Enable proxy if getting blocked

## 📝 Notes

- The scraper automatically handles pagination
- Duplicate deals are prevented by unique constraints
- All data is normalized across 4 tables
- Raw HTML is saved for auditing purposes

## 📞 Support

For issues or questions, check:
- `README.md` - Full documentation
- `logs/scraper_run.log` - Scraper logs
- Database tables - Verify data structure

