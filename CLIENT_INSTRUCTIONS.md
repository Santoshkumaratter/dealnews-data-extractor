# DealNews Scraper - Client Instructions

## 📋 Overview

This scraper will extract **100,000+ deals** from dealnews.com and save them to a normalized MySQL database.

**Expected Time:** 2-4 hours  
**Target Deals:** 100,000+ deals  
**Database:** MySQL (normalized across 4 tables)

---

## 🚀 Setup & Run Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy environment file
cp env.example .env

# Edit .env file with your MySQL credentials
# Set MYSQL_PASSWORD=your_password (or leave empty if no password)
# Set DISABLE_PROXY=true for local testing
```

### Step 3: Initialize Database (REQUIRED - Run First!)
```bash
python3 init_database.py
```

**This creates:**
- `dealnews` database
- `deals` table (main deal information)
- `deal_images` table (multiple images per deal)
- `deal_categories` table (multiple categories per deal)
- `related_deals` table (related deals per deal)

**⚠️ IMPORTANT: Always run this step first before scraping!**

### Step 4: Run Scraper
```bash
python3 run_scraper.py
```

**This will:**
- Start scraping deals from dealnews.com
- Extract 100,000+ deals
- Save all data to MySQL database
- Take approximately 2-4 hours to complete

### Step 5: Verify Results
```bash
python3 verify_mysql.py
```

**This will show:**
- Total deals saved
- Total images
- Total categories
- Total related deals
- Top categories and stores

---

## ⏱️ Expected Performance

| Metric | Value |
|--------|-------|
| **Total Deals** | 100,000+ deals |
| **Expected Time** | 2-4 hours |
| **Speed** | ~25-50 deals/second |
| **Concurrency** | 64 concurrent requests |
| **Database Tables** | 4 normalized tables |

---

## 📊 What Will Be Saved

### 1. Deals Table
- **100,000+ deal records** with:
  - Deal ID, URL, Title, Price
  - Store, Category, Promo codes
  - Deal description, Popularity, Staff picks
  - Published date, Raw HTML (for audit)

### 2. Deal Images Table
- **Multiple images per deal**
- Unique constraint prevents duplicate images
- Estimated: 200,000+ images

### 3. Deal Categories Table
- **Multiple categories per deal**
- Categories from breadcrumbs, tags, filters
- Category IDs, URLs, and titles
- Estimated: 300,000+ category records

### 4. Related Deals Table
- **Related deal URLs per deal**
- Unique constraint prevents duplicates
- Estimated: 150,000+ related deal links

---

## 📝 Quick Command Summary

```bash
# 1. Initialize database (REQUIRED - run first!)
python3 init_database.py

# 2. Run scraper (100k+ deals, 2-4 hours)
python3 run_scraper.py

# 3. Check progress (optional, in another terminal)
python3 verify_mysql.py

# 4. View logs (optional)
tail -f logs/scraper_run.log
```

---

## 🔍 Progress Monitoring

### Check Progress While Scraping
Open a new terminal and run:
```bash
python3 verify_mysql.py
```

This will show real-time statistics:
- Current number of deals saved
- Images, categories, related deals count
- Top categories and stores

### View Live Logs
```bash
tail -f logs/scraper_run.log
```

---

## ⚙️ Configuration

### Speed Optimization
The scraper is optimized for speed with:
- **64 concurrent requests** (high concurrency)
- **AutoThrottle enabled** (automatic rate adjustment)
- **Minimal delays** (0.1 seconds between requests)
- **Automatic pagination** (deep crawling)

### Proxy Support
- webshare.io proxy support (configure in `.env`)
- Automatic proxy rotation
- Retry logic with exponential backoff
- Set `DISABLE_PROXY=true` for local testing

---

## 📁 Database Structure

### Tables Created:
1. **deals** - Main deal information (100,000+ records)
2. **deal_images** - Multiple images per deal (200,000+ records)
3. **deal_categories** - Multiple categories per deal (300,000+ records)
4. **related_deals** - Related deals per deal (150,000+ records)

### Key Features:
- ✅ Unique constraints prevent duplicate images
- ✅ Unique constraints prevent duplicate related deals
- ✅ Multiple categories per deal (breadcrumbs, tags, filters)
- ✅ Full audit trail with raw_html field
- ✅ Proper indexing for performance

---

## 🛠️ Troubleshooting

### MySQL Connection Error
```bash
# Verify MySQL is running
mysql -u root -p

# Check credentials in .env file
cat .env
```

### No Deals Scraped
- Check internet connection
- Verify dealnews.com is accessible
- Check scraper logs: `tail -f logs/scraper_run.log`

### Slow Scraping
- Increase `CONCURRENT_REQUESTS` in `.env` (default: 64)
- Decrease `DOWNLOAD_DELAY` in `.env` (default: 0.1)
- Enable proxy if getting blocked

---

## 📞 Support

For issues or questions:
- Check `README.md` for full documentation
- Check `logs/scraper_run.log` for error logs
- Verify database tables: `python3 verify_mysql.py`

---

## ✅ Summary

**Commands to Run:**
1. `python3 init_database.py` (first time only)
2. `python3 run_scraper.py` (starts scraping)

**Expected Results:**
- **100,000+ deals** saved to database
- **2-4 hours** to complete
- **4 normalized tables** with all relationships

**Progress Check:**
- Run `python3 verify_mysql.py` to see current progress

---

**Ready to start? Run the commands above and the scraper will automatically extract 100,000+ deals!**

