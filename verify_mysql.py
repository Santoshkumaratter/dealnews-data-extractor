#!/usr/bin/env python3
"""
Verify MySQL database and show deal counts and sample data.
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

def verify_database():
    """Verify database and show statistics"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print("=" * 60)
    print("MySQL Database Verification")
    print("=" * 60)
    print()
    
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connection_timeout=10
        )
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'deals'")
        if not cursor.fetchone():
            print("❌ Table 'deals' does not exist!")
            print("   Run: python3 init_database.py")
            return False
        
        # Get total counts for all tables
        cursor.execute("SELECT COUNT(*) FROM deals")
        total_deals = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deal_images")
        total_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM deal_categories")
        total_categories = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM related_deals")
        total_related = cursor.fetchone()[0]
        
        print(f"📊 Database Statistics:")
        print(f"   Total Deals: {total_deals:,}")
        print(f"   Total Images: {total_images:,}")
        print(f"   Total Categories: {total_categories:,}")
        print(f"   Total Related Deals: {total_related:,}")
        print()
        
        if total_deals == 0:
            print("⚠️  No deals found in database.")
            print("   Run: python3 run_scraper.py")
            return False
        
        
        # Get counts by category
        print("📈 Deals by Category (Top 10):")
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM deals 
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category 
            ORDER BY count DESC 
            LIMIT 10
        """)
        category_data = cursor.fetchall()
        if category_data:
            print(tabulate(category_data, headers=['Category', 'Count'], tablefmt='grid'))
        else:
            print("   No categories found")
        print()
        
        # Get counts by store
        print("🏪 Deals by Store (Top 10):")
        cursor.execute("""
            SELECT store, COUNT(*) as count 
            FROM deals 
            WHERE store IS NOT NULL AND store != ''
            GROUP BY store 
            ORDER BY count DESC 
            LIMIT 10
        """)
        store_data = cursor.fetchall()
        if store_data:
            print(tabulate(store_data, headers=['Store', 'Count'], tablefmt='grid'))
        else:
            print("   No stores found")
        print()
        
        # Get sample deals
        print("📋 Sample Deals (First 10):")
        cursor.execute("""
            SELECT dealid, title, price, store, category, created_at
            FROM deals
            ORDER BY created_at DESC
            LIMIT 10
        """)
        sample_data = cursor.fetchall()
        if sample_data:
            print(tabulate(
                sample_data, 
                headers=['Deal ID', 'Title', 'Price', 'Store', 'Category', 'Created At'],
                tablefmt='grid',
                maxcolwidths=[15, 40, 15, 20, 20, 20]
            ))
        print()
        
        # Check if we reached 100,000 deals
        if total_count >= 100000:
            print("✅ SUCCESS: Reached target of 100,000+ deals!")
        else:
            print(f"⚠️  Current count: {total_count:,} (Target: 100,000+)")
            print("   Continue scraping to reach target.")
        print()
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        return False
    except ImportError:
        print("⚠️  tabulate module not found. Showing basic output...")
        # Fallback to basic output
        return verify_database_basic()
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_database_basic():
    """Basic verification without tabulate"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connection_timeout=10
        )
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM deals")
        total_count = cursor.fetchone()[0]
        
        print(f"📊 Total Deals: {total_count:,}")
        
        if total_count >= 100000:
            print("✅ SUCCESS: Reached target of 100,000+ deals!")
        else:
            print(f"⚠️  Current count: {total_count:,} (Target: 100,000+)")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)

