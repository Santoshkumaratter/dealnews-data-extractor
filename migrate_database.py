#!/usr/bin/env python3
"""
Migrate database from old schema to new schema per client requirements.

Changes:
1. Add category_id column to deals table
2. Create new categories lookup table
3. Migrate data from deal_categories to categories
4. Update deals with category_id references
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def migrate_database():
    """Perform database migration"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print("=" * 60)
    print("Database Migration Script")
    print("=" * 60)
    print(f"Host: {mysql_host}:{mysql_port}")
    print(f"Database: {mysql_database}")
    print()
    
    try:
        # Connect to database
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            autocommit=False
        )
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        print()
        
        # Step 1: Check if migration is needed
        print("Step 1: Checking current schema...")
        cursor.execute("SHOW TABLES LIKE 'deal_categories'")
        has_old_table = cursor.fetchone() is not None
        
        cursor.execute("SHOW TABLES LIKE 'categories'")
        has_new_table = cursor.fetchone() is not None
        
        cursor.execute("SHOW COLUMNS FROM deals LIKE 'category_id'")
        has_category_id = cursor.fetchone() is not None
        
        print(f"  - Old deal_categories table exists: {has_old_table}")
        print(f"  - New categories table exists: {has_new_table}")
        print(f"  - deals.category_id column exists: {has_category_id}")
        print()
        
        if not has_old_table:
            print("⚠️  No deal_categories table found. Migration may not be needed.")
            print("   Running schema update only...")
        
        # Step 2: Add category_id to deals table if not exists
        if not has_category_id:
            print("Step 2: Adding category_id column to deals table...")
            cursor.execute("""
                ALTER TABLE deals 
                ADD COLUMN category_id VARCHAR(100) AFTER category,
                ADD INDEX idx_category_id (category_id)
            """)
            conn.commit()
            print("✅ Added category_id column to deals table")
        else:
            print("Step 2: Skipped - category_id column already exists")
        print()
        
        # Step 3: Create categories table if not exists
        if not has_new_table:
            print("Step 3: Creating categories lookup table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  category_id VARCHAR(100) UNIQUE NOT NULL,
                  category_name VARCHAR(255),
                  category_url TEXT,
                  category_description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                  INDEX idx_category_id (category_id),
                  INDEX idx_category_name (category_name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)
            conn.commit()
            print("✅ Created categories table")
        else:
            print("Step 3: Skipped - categories table already exists")
        print()
        
        # Step 4: Migrate data if old table exists
        if has_old_table:
            print("Step 4: Backing up deal_categories table...")
            cursor.execute("DROP TABLE IF EXISTS deal_categories_backup")
            cursor.execute("CREATE TABLE deal_categories_backup AS SELECT * FROM deal_categories")
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM deal_categories_backup")
            backup_count = cursor.fetchone()[0]
            print(f"✅ Backed up {backup_count:,} rows to deal_categories_backup")
            print()
            
            print("Step 5: Migrating unique categories to categories table...")
            cursor.execute("""
                INSERT IGNORE INTO categories (category_id, category_name, category_url)
                SELECT DISTINCT 
                  category_id,
                  category_name,
                  category_url
                FROM deal_categories
                WHERE category_id IS NOT NULL AND category_id != ''
            """)
            migrated = cursor.rowcount
            conn.commit()
            print(f"✅ Migrated {migrated:,} unique categories")
            print()
            
            print("Step 6: Updating deals table with category_id...")
            cursor.execute("""
                UPDATE deals d
                LEFT JOIN (
                  SELECT dealid, MIN(category_id) as primary_category_id
                  FROM deal_categories
                  WHERE category_id IS NOT NULL AND category_id != ''
                  GROUP BY dealid
                ) dc ON d.dealid = dc.dealid
                SET d.category_id = dc.primary_category_id
                WHERE dc.primary_category_id IS NOT NULL
            """)
            updated = cursor.rowcount
            conn.commit()
            print(f"✅ Updated {updated:,} deals with category_id")
            print()
            
            print("Step 7: Dropping old deal_categories table...")
            cursor.execute("DROP TABLE IF EXISTS deal_categories")
            conn.commit()
            print("✅ Dropped old deal_categories table")
            print()
        else:
            print("Steps 4-7: Skipped - no old deal_categories table to migrate")
            print()
        
        # Step 8: Verify migration
        print("Step 8: Verifying migration...")
        cursor.execute("SELECT COUNT(*) FROM categories")
        cat_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deals WHERE category_id IS NOT NULL")
        deals_with_cat = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deals")
        total_deals = cursor.fetchone()[0]
        
        print(f"  - Total categories: {cat_count:,}")
        print(f"  - Deals with category_id: {deals_with_cat:,}")
        print(f"  - Total deals: {total_deals:,}")
        print(f"  - Coverage: {(deals_with_cat/total_deals*100) if total_deals > 0 else 0:.1f}%")
        print()
        
        # Test join
        print("Step 9: Testing join query...")
        cursor.execute("""
            SELECT d.dealid, d.title, c.category_name
            FROM deals d
            JOIN categories c ON d.category_id = c.category_id
            LIMIT 5
        """)
        results = cursor.fetchall()
        if results:
            print("✅ Join query successful! Sample results:")
            for dealid, title, cat_name in results:
                title_short = (title[:50] + '...') if title and len(title) > 50 else (title or 'N/A')
                print(f"  - {dealid}: {title_short}")
                print(f"    Category: {cat_name}")
        else:
            print("⚠️  No results from join query (may be normal if no data yet)")
        print()
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  1. Update pipeline code to use new schema")
        print("  2. Test scraper with new schema")
        print("  3. Verify data integrity")
        print()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
