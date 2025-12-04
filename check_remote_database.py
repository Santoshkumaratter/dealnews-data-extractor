#!/usr/bin/env python3
"""
Check remote database and show all databases and tables
Usage: python3 check_remote_database.py --host 107.172.13.162 --user root --password YOUR_PASSWORD
"""
import os
import sys
import mysql.connector
import argparse
from dotenv import load_dotenv

load_dotenv()

def check_database(host=None, user=None, password=None, database='dealnews'):
    """Check database existence and show all databases"""
    mysql_host = host or os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = user or os.getenv('MYSQL_USER', 'root')
    mysql_password = password or os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = database or os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print("=" * 60)
    print("Remote Database Connection Check")
    print("=" * 60)
    print(f"Host: {mysql_host}:{mysql_port}")
    print(f"User: {mysql_user}")
    print(f"Database: {mysql_database}")
    print()
    
    try:
        # Connect without specifying database first
        print("Connecting to MySQL server...")
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connection_timeout=10
        )
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        print()
        
        # Show all databases
        print("📊 All Databases on Server:")
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        for (db_name,) in databases:
            marker = "✅" if db_name == mysql_database else "  "
            print(f"   {marker} {db_name}")
        print()
        
        # Check if target database exists
        cursor.execute("SHOW DATABASES LIKE %s", (mysql_database,))
        db_exists = cursor.fetchone()
        
        if not db_exists:
            print(f"❌ Database '{mysql_database}' does NOT exist!")
            print()
            print("To create the database, run:")
            print(f"   python3 init_database.py --host {mysql_host} --user {mysql_user} --password YOUR_PASSWORD")
            print()
            cursor.close()
            conn.close()
            return False
        
        print(f"✅ Database '{mysql_database}' exists!")
        print()
        
        # Connect to the database
        cursor.execute(f"USE {mysql_database}")
        
        # Show all tables
        print(f"📋 Tables in '{mysql_database}' database:")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        if tables:
            total_deals = 0
            total_images = 0
            total_categories = 0
            total_related = 0
            
            for (table_name,) in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table_name}: {count:,} rows")
                
                if table_name == 'deals':
                    total_deals = count
                elif table_name == 'deal_images':
                    total_images = count
                elif table_name == 'deal_categories':
                    total_categories = count
                elif table_name == 'related_deals':
                    total_related = count
            print()
            
            print("📊 Summary:")
            print(f"   Total Deals: {total_deals:,}")
            print(f"   Total Images: {total_images:,}")
            print(f"   Total Categories: {total_categories:,}")
            print(f"   Total Related Deals: {total_related:,}")
            print()
        else:
            print("   ❌ No tables found!")
            print()
            print("To create tables, run:")
            print(f"   python3 init_database.py --host {mysql_host} --user {mysql_user} --password YOUR_PASSWORD")
        print()
        
        # Show sample data
        if tables and total_deals > 0:
            print("📊 Sample Deals (First 5):")
            cursor.execute("SELECT dealid, title, store, category, created_at FROM deals ORDER BY created_at DESC LIMIT 5")
            deals = cursor.fetchall()
            if deals:
                for dealid, title, store, category, created_at in deals:
                    title_short = (title[:50] + '...') if title and len(title) > 50 else (title or 'N/A')
                    store_str = store or 'N/A'
                    category_str = category or 'N/A'
                    print(f"   - {dealid}: {title_short}")
                    print(f"     Store: {store_str}, Category: {category_str}, Created: {created_at}")
            else:
                print("   ⚠️  No deals found in database")
            print()
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        print()
        print("🌐 To access in phpMyAdmin:")
        print(f"   URL: http://{mysql_host}:8081/index.php?route=/database/structure&db={mysql_database}")
        print(f"   Or: http://{mysql_host}:8081/index.php?route=/sql&db={mysql_database}")
        print()
        print("📝 Quick SQL Query to view deals:")
        print(f"   SELECT * FROM deals LIMIT 10;")
        print()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        print()
        print("Possible issues:")
        print("   1. Database server is not running")
        print("   2. Wrong host/port/user/password")
        print("   3. Firewall blocking connection")
        print("   4. MySQL user doesn't have access from this IP")
        print()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check remote MySQL database')
    parser.add_argument('--host', type=str, help='MySQL host (default: from .env or localhost)')
    parser.add_argument('--user', type=str, help='MySQL user (default: from .env or root)')
    parser.add_argument('--password', type=str, help='MySQL password (default: from .env or root)')
    parser.add_argument('--database', type=str, default='dealnews', help='Database name (default: dealnews)')
    
    args = parser.parse_args()
    
    success = check_database(
        host=args.host,
        user=args.user,
        password=args.password,
        database=args.database
    )
    sys.exit(0 if success else 1)

