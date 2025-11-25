#!/usr/bin/env python3
"""
Initialize MySQL database and create the deals table.
This script should be run before scraping to ensure the table exists.
"""
import os
import sys
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def create_database_and_table():
    """Create database and table if they don't exist"""
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print(f"Connecting to MySQL at {mysql_host}:{mysql_port} as {mysql_user}...")
    
    try:
        # Connect without database first to create it if needed
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            connection_timeout=10
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {mysql_database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ Database '{mysql_database}' created/verified")
        
        # Use the database
        cursor.execute(f"USE {mysql_database}")
        
        # Read and execute SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'mysql-init', '01_create_deals.sql')
        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                sql_commands = f.read()
                # Split by semicolon and execute each command
                for command in sql_commands.split(';'):
                    command = command.strip()
                    if command and not command.startswith('--'):
                        try:
                            cursor.execute(command)
                        except mysql.connector.Error as e:
                            if "already exists" not in str(e).lower():
                                print(f"[WARNING] {e}")
            conn.commit()
            print("✅ All tables created/verified (deals, deal_images, deal_categories, related_deals)")
        else:
            print(f"⚠️  SQL file not found: {sql_file}")
            print("   Creating tables directly...")
            # Fallback: create main table only
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS deals (
                id INT AUTO_INCREMENT PRIMARY KEY,
                dealid VARCHAR(50) UNIQUE NOT NULL,
                recid VARCHAR(50),
                url TEXT,
                title TEXT,
                price VARCHAR(100),
                promo TEXT,
                category VARCHAR(255),
                store VARCHAR(100),
                deal TEXT,
                dealplus TEXT,
                deallink TEXT,
                dealtext TEXT,
                dealhover TEXT,
                published VARCHAR(100),
                popularity VARCHAR(50),
                staffpick VARCHAR(10),
                detail TEXT,
                raw_html LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_dealid (dealid),
                INDEX idx_created_at (created_at),
                INDEX idx_store (store),
                INDEX idx_category (category)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            cursor.execute(create_table_sql)
            conn.commit()
            print("✅ Table 'deals' created/verified")
        
        # Check all table counts
        tables = ['deals', 'deal_images', 'deal_categories', 'related_deals']
        print("\n📊 Table Statistics:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count:,} rows")
            except mysql.connector.Error as e:
                print(f"   {table}: not found or error - {e}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database initialization complete!")
        print(f"   Database: {mysql_database}")
        print(f"   Tables: deals, deal_images, deal_categories, related_deals")
        print(f"   Ready for scraping!\n")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_database_and_table()
    sys.exit(0 if success else 1)

