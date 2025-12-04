# Client Database Access Guide

## 🔍 Check if Database Exists

Run this command to check the remote database:
```bash
python3 check_remote_database.py --host 107.172.13.162 --user YOUR_USER --password YOUR_PASSWORD
```

This will show:
- ✅ All databases on the server
- ✅ Whether `dealnews` database exists
- ✅ All tables and row counts
- ✅ Sample data

## 📊 Access Database in phpMyAdmin

### Step 1: Login to phpMyAdmin
1. Go to: **http://107.172.13.162:8081**
2. Enter MySQL credentials:
   - **Server:** 107.172.13.162:3306 (or leave default)
   - **Username:** (your MySQL username)
   - **Password:** (your MySQL password)
3. Click **"Go"** or press Enter

### Step 2: Select Database
1. In the **left sidebar**, look for **"dealnews"** database
2. If you don't see it, check the **"Databases"** tab at the top
3. Click on **"dealnews"** to select it

### Step 3: View Tables
You should see 4 tables:
- ✅ **`deals`** - Main deals table (67,791+ rows)
- ✅ **`deal_images`** - Deal images (133,824+ rows)
- ✅ **`deal_categories`** - Deal categories (185,457+ rows)
- ✅ **`related_deals`** - Related deals (0 rows - optional)

### Step 4: View Data
1. Click on **"deals"** table
2. Click **"Browse"** tab to see all deals
3. Or click **"SQL"** tab to run custom queries

## 🔗 Direct URL Access

### View Database Structure
```
http://107.172.13.162:8081/index.php?route=/database/structure&db=dealnews
```

### Run SQL Queries
```
http://107.172.13.162:8081/index.php?route=/sql&db=dealnews
```

### Browse Deals Table
```
http://107.172.13.162:8081/index.php?route=/table/browse&db=dealnews&table=deals
```

## 📝 Quick SQL Queries

### View All Deals
```sql
SELECT * FROM deals LIMIT 10;
```

### Count Total Deals
```sql
SELECT COUNT(*) as total_deals FROM deals;
```

### View Deal with Images and Categories
```sql
SELECT 
    d.dealid,
    d.title,
    d.store,
    d.deal,
    d.price,
    d.deallink,
    GROUP_CONCAT(DISTINCT di.imageurl) as images,
    GROUP_CONCAT(DISTINCT dc.category_name) as categories
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
LEFT JOIN deal_categories dc ON d.dealid = dc.dealid
WHERE d.dealid = '21792018'
GROUP BY d.dealid;
```

### View Deal URL (to open in browser)
```sql
SELECT dealid, title, deallink FROM deals WHERE dealid = '21792018';
```

Then copy the `deallink` and open it in your browser.

## 🚨 If Database Doesn't Exist

If you don't see the `dealnews` database:

1. **Create it using the script:**
```bash
python3 init_database.py --host 107.172.13.162 --user YOUR_USER --password YOUR_PASSWORD
```

2. **Or create manually in phpMyAdmin:**
   - Click **"New"** or **"Create database"**
   - Database name: **`dealnews`**
   - Collation: **`utf8mb4_general_ci`**
   - Click **"Create"**
   - Then run: `python3 init_database.py --host 107.172.13.162`

## ✅ Verification Checklist

- [ ] Can connect to phpMyAdmin
- [ ] See `dealnews` database in list
- [ ] See 4 tables: deals, deal_images, deal_categories, related_deals
- [ ] Can view deals data
- [ ] Can run SQL queries

## 📊 Expected Data Counts (from your last run)

- **Deals:** 67,791 rows
- **Images:** 133,824 rows
- **Categories:** 185,457 rows
- **Related Deals:** 0 rows (optional)

## 🔍 Troubleshooting

### Issue: Can't see database
**Solution:** Run `check_remote_database.py` to verify database exists

### Issue: Can't login to phpMyAdmin
**Solution:** Check MySQL username/password in your `.env` file

### Issue: Database exists but no tables
**Solution:** Run `init_database.py` to create tables

### Issue: Tables exist but no data
**Solution:** Run the scraper: `python3 run_scraper.py`

