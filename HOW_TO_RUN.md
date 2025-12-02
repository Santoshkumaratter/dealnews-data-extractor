# 🚀 Scraper Kaise Run Karein (100,000+ Deals)

## Step 1: Environment Setup

```bash
# Terminal mein project folder mein jao
cd /Users/apple/Documents/dealnews-data-extractor

# .env file check karo (agar nahi hai to banayein)
cp env.example .env

# .env file edit karo (agar MySQL password different hai)
# nano .env  ya  open .env
```

**Important:** `.env` file mein MySQL credentials check karo:
- `MYSQL_PASSWORD=root` (agar aapka password different hai to change karo)
- `MYSQL_DATABASE=dealnews`
- `DISABLE_PROXY=true` (proxy use nahi karna)

## Step 2: Dependencies Install Karein

```bash
# Python packages install karo
pip3 install -r requirements.txt
```

## Step 3: Database Initialize Karein (IMPORTANT - Pehle ye karo!)

```bash
# Database aur tables create karega
python3 init_database.py
```

**Ye step zaroori hai** - ye database aur tables create karega.

## Step 4: Scraper Run Karein (100,000+ Deals)

```bash
# Scraper start karo
python3 run_scraper.py
```

**Expected Time:** 2-4 hours for 100,000+ deals

**Progress dekho:**
- Terminal mein live progress dikhega
- Logs: `logs/scraper_run.log` file mein save honge

## Step 5: Progress Check Karein (Optional - Scraper chalte hue)

**Nayi terminal window kholo aur ye command run karo:**

```bash
# Real-time progress check
python3 verify_mysql.py
```

Ye dikhayega:
- Kitne deals save ho chuke hain
- Kitne images, categories, related deals
- Top categories aur stores

## Step 6: Results Verify Karein (Scraper complete hone ke baad)

```bash
# Final statistics
python3 verify_mysql.py
```

## Quick Commands Summary

```bash
# 1. Database setup (pehle ye karo!)
python3 init_database.py

# 2. Scraper run karo (100k+ deals)
python3 run_scraper.py

# 3. Progress check (scraper chalte hue)
python3 verify_mysql.py

# 4. Logs dekho
tail -f logs/scraper_run.log
```

## Troubleshooting

### MySQL Connection Error
```bash
# MySQL running hai ya nahi check karo
mysql -u root -p

# Agar MySQL nahi chal raha:
# macOS: brew services start mysql
# Linux: sudo systemctl start mysql
```

### Scraper Slow Chal Raha Hai
- Normal hai - 100,000+ deals ke liye 2-4 hours lag sakte hain
- Progress check karte raho: `python3 verify_mysql.py`

### Scraper Stop Ho Gaya
- Koi error check karo: `tail -f logs/scraper_run.log`
- Phir se run karo: `python3 run_scraper.py`
- Scraper automatically resume karega (duplicate deals save nahi honge)

## Expected Output

Scraper complete hone ke baad:
- ✅ 100,000+ deals MySQL database mein
- ✅ Har deal ke multiple images
- ✅ Har deal ke multiple categories
- ✅ Related deals links

**Total time:** 2-4 hours (network speed ke hisab se)

