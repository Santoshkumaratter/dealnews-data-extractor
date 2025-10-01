#!/usr/bin/env python3
"""
Setup script to create the DealNews database and table in Laradock MySQL
Run this once before running the scraper
"""

import mysql.connector
import os
from dotenv import load_dotenv

def setup_database():
    """Create database and table in Laradock MySQL"""
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'autocommit': True
    }
    
    try:
        print("[OK] Connecting to Laradock MySQL...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("[OK] Connected to Laradock MySQL successfully!")
        
        # Create database
        database_name = os.getenv('MYSQL_DATABASE', 'dealnews')
        print(f"[OK] Creating database '{database_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"[OK] Database '{database_name}' created/verified!")
        
        # Use the database
        cursor.execute(f"USE {database_name}")
        
        # Create normalized tables
        print("[OK] Creating normalized tables...")
        
        # 1. Main deals table
        create_deals_table = """
        CREATE TABLE IF NOT EXISTS deals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50) UNIQUE,
            recid VARCHAR(50),
            url TEXT,
            title TEXT,
            price VARCHAR(100),
            promo TEXT,
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
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 2. Stores table (normalized)
        create_stores_table = """
        CREATE TABLE IF NOT EXISTS stores (
            id INT AUTO_INCREMENT PRIMARY KEY,
            store_name VARCHAR(100) UNIQUE,
            store_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_store_name (store_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 3. Categories table (normalized)
        create_categories_table = """
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category_name VARCHAR(100) UNIQUE,
            category_url TEXT,
            category_title VARCHAR(200),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_category_name (category_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 4. Brands table (normalized)
        create_brands_table = """
        CREATE TABLE IF NOT EXISTS brands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            brand_name VARCHAR(100) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_brand_name (brand_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 5. Collections table (normalized)
        create_collections_table = """
        CREATE TABLE IF NOT EXISTS collections (
            id INT AUTO_INCREMENT PRIMARY KEY,
            collection_name VARCHAR(100) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_collection_name (collection_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 6. Deal images table
        create_deal_images_table = """
        CREATE TABLE IF NOT EXISTS deal_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50),
            imageurl TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_dealid (dealid),
            FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 7. Deal categories junction table (many-to-many)
        create_deal_categories_table = """
        CREATE TABLE IF NOT EXISTS deal_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50),
            category_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_deal_category (dealid, category_id),
            INDEX idx_dealid (dealid),
            INDEX idx_category_id (category_id),
            FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 8. Related deals table
        create_related_deals_table = """
        CREATE TABLE IF NOT EXISTS related_deals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50),
            related_dealid VARCHAR(50),
            related_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_dealid (dealid),
            INDEX idx_related_dealid (related_dealid),
            FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 9. Filter variables table (all the filters from the image)
        create_filter_variables_table = """
        CREATE TABLE IF NOT EXISTS deal_filters (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50),
            start_date DATE,
            max_price DECIMAL(10,2),
            category_id INT,
            store_id INT,
            brand_id INT,
            offer_type VARCHAR(50),
            popularity_rank INT,
            collection_id INT,
            condition_type VARCHAR(50),
            events VARCHAR(100),
            offer_status VARCHAR(50),
            include_expired BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_dealid (dealid),
            INDEX idx_offer_type (offer_type),
            INDEX idx_condition_type (condition_type),
            INDEX idx_offer_status (offer_status),
            FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
            FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # Execute all table creation statements
        tables_to_create = [
            ("deals", create_deals_table),
            ("stores", create_stores_table),
            ("categories", create_categories_table),
            ("brands", create_brands_table),
            ("collections", create_collections_table),
            ("deal_images", create_deal_images_table),
            ("deal_categories", create_deal_categories_table),
            ("related_deals", create_related_deals_table),
            ("deal_filters", create_filter_variables_table)
        ]
        
        for table_name, create_sql in tables_to_create:
            cursor.execute(create_sql)
            print(f"[OK] {table_name} table created/verified!")
        
        # Check if tables exist and show structure
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"[OK] Available tables: {[table[0] for table in tables]}")
        
        # Show structure of main tables
        for table_name in ["deals", "stores", "categories", "deal_filters"]:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            print(f"[OK] {table_name} table has {len(columns)} columns")
        
        print("\n[SUCCESS] Database setup completed successfully!")
        print(f"[OK] Database: {database_name}")
        print(f"[OK] Host: {config['host']}:{config['port']}")
        print(f"[OK] User: {config['user']}")
        
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL Error: {err}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("[OK] Database connection closed")
    
    return True

if __name__ == "__main__":
    print("[OK] DealNews Database Setup for Laradock")
    print("=" * 50)
    
    success = setup_database()
    
    if success:
        print("\n[SUCCESS] Setup completed! You can now run:")
        print("   docker-compose up scraper")
    else:
        print("\n[ERROR] Setup failed! Please check your Laradock MySQL connection.")
        exit(1)
