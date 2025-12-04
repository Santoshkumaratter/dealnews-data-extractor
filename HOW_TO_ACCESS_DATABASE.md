# How to Access Database in phpMyAdmin

## 🔍 Step 1: Check if Database Exists

Run this command to check all databases:
```bash
python3 check_database.py
```

This will show:
- All databases on the server
- Whether `dealnews` database exists
- All tables in the database
- Row counts for each table

## 📊 Step 2: Access phpMyAdmin

### Option 1: Direct Database URL
```
http://107.172.13.162:8081/index.php?route=/database/structure&db=dealnews
```

### Option 2: Navigate Manually
1. Go to: `http://107.172.13.162:8081`
2. Login with MySQL credentials:
   - **Server:** 107.172.13.162:3306
   - **Username:** (from your .env file)
   - **Password:** (from your .env file)
3. Click on **"dealnews"** database in the left sidebar
4. You should see 4 tables:
   - `deals` - Main deals table
   - `deal_images` - Deal images
   - `deal_categories` - Deal categories
   - `related_deals` - Related deals

## 🔍 Step 3: Verify Data

### Check Total Counts
```sql
SELECT COUNT(*) as total_deals FROM deals;
SELECT COUNT(*) as total_images FROM deal_images;
SELECT COUNT(*) as total_categories FROM deal_categories;
SELECT COUNT(*) as total_related FROM related_deals;
```

### View Sample Deals
```sql
SELECT dealid, title, store, category, deal, price 
FROM deals 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check for Duplicates
```sql
-- Check duplicate deals
SELECT dealid, COUNT(*) as count 
FROM deals 
GROUP BY dealid 
HAVING count > 1;

-- Check duplicate images
SELECT dealid, imageurl, COUNT(*) as count 
FROM deal_images 
GROUP BY dealid, imageurl 
HAVING count > 1;

-- Check duplicate categories
SELECT dealid, category_name, COUNT(*) as count 
FROM deal_categories 
GROUP BY dealid, category_name 
HAVING count > 1;
```

## 🚨 If Database Doesn't Exist

If you don't see the `dealnews` database:

1. **Create the database:**
```bash
python3 init_database.py --host 107.172.13.162 --user YOUR_USER --password YOUR_PASSWORD
```

2. **Or create manually in phpMyAdmin:**
   - Go to phpMyAdmin
   - Click "New" or "Create database"
   - Database name: `dealnews`
   - Collation: `utf8mb4_general_ci`
   - Click "Create"
   - Then run: `python3 init_database.py --host 107.172.13.162`

## 📋 Quick SQL Queries for Client

### Get All Deals with Images and Categories
```sql
SELECT 
    d.dealid,
    d.title,
    d.store,
    d.deal,
    d.dealplus,
    d.price,
    d.deallink,
    d.published,
    d.popularity,
    d.staffpick,
    GROUP_CONCAT(DISTINCT di.imageurl) as images,
    GROUP_CONCAT(DISTINCT dc.category_name) as categories
FROM deals d
LEFT JOIN deal_images di ON d.dealid = di.dealid
LEFT JOIN deal_categories dc ON d.dealid = dc.dealid
GROUP BY d.dealid
LIMIT 10;
```

### Get Deal by ID
```sql
SELECT * FROM deals WHERE dealid = '21792018';
```

### Get All Images for a Deal
```sql
SELECT * FROM deal_images WHERE dealid = '21792018';
```

### Get All Categories for a Deal
```sql
SELECT * FROM deal_categories WHERE dealid = '21792018';
```

## 🔗 View Deal URL

To view a deal in browser, use the `deallink` field:
```sql
SELECT dealid, title, deallink FROM deals WHERE dealid = '21792018';
```

Then open the `deallink` URL in your browser.

## 📝 Notes

- Database name: **`dealnews`**
- All data is stored in MySQL at: **107.172.13.162:3306**
- phpMyAdmin URL: **http://107.172.13.162:8081**
- Tables are created automatically when you run `init_database.py`

