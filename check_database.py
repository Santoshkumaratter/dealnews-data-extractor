#!/usr/bin/env python3
"""
Check if database exists and show all databases and tables
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def check_database():
    """Check database existence and show all databases"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print("=" * 60)
    print("Database Connection Check")
    print("=" * 60)
    print(f"Host: {mysql_host}:{mysql_port}")
    print(f"User: {mysql_user}")
    print(f"Database: {mysql_database}")
    print()
    
    try:
        # Connect without specifying database first
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connection_timeout=10
        )
        cursor = conn.cursor()
        
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
            for (table_name,) in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table_name}: {count:,} rows")
        else:
            print("   ❌ No tables found!")
            print()
            print("To create tables, run:")
            print(f"   python3 init_database.py --host {mysql_host} --user {mysql_user} --password YOUR_PASSWORD")
        print()
        
        # Show sample data
        if tables:
            print("📊 Sample Data:")
            cursor.execute("SELECT dealid, title, store, category FROM deals LIMIT 5")
            deals = cursor.fetchall()
            if deals:
                print("   Sample Deals:")
                for dealid, title, store, category in deals:
                    print(f"      - {dealid}: {title[:50]}... (Store: {store}, Category: {category})")
            else:
                print("   ⚠️  No deals found in database")
            print()
        
        cursor.close()
        conn.close()
        
        print("=" * 60)
        print("✅ Database check complete!")
        print("=" * 60)
        print()
        print("To access in phpMyAdmin:")
        print(f"   URL: http://{mysql_host}:8081/index.php?route=/database/structure&db={mysql_database}")
        print(f"   Or: http://{mysql_host}:8081/index.php?route=/sql&db={mysql_database}")
        print()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        print()
        print("Possible issues:")
        print("   1. Database server is not running")
        print("   2. Wrong host/port/user/password")
        print("   3. Firewall blocking connection")
        print()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)

