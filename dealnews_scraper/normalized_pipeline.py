import os
import time
import mysql.connector
import logging
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem

class NormalizedMySQLPipeline:
    """Normalized pipeline for storing scraped items in normalized MySQL database tables."""
    
    def open_spider(self, spider):
        try:
            # Check if MySQL is disabled
            disable_mysql = os.getenv('DISABLE_MYSQL', 'false').lower() in ('1', 'true', 'yes')
            if disable_mysql:
                logging.info("MySQL pipeline disabled by DISABLE_MYSQL flag")
                spider.logger.info("MySQL pipeline disabled by DISABLE_MYSQL flag")
                self.mysql_enabled = False
                return
            
            self.mysql_enabled = True
            spider.logger.info("Normalized MySQL pipeline enabled - attempting connection...")
            
            # Get MySQL connection settings
            mysql_host = os.getenv('MYSQL_HOST', 'localhost')
            mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
            mysql_user = os.getenv('MYSQL_USER', 'root')
            mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
            mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
            
            spider.logger.info(f"Connecting to MySQL: {mysql_host}:{mysql_port} as {mysql_user} to database {mysql_database}")
            
            self.conn = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                use_pure=True,
                connection_timeout=60,  # Increased timeout
                autocommit=True,
                pool_name='dealnews_pool',
                pool_size=5,
                pool_reset_session=True
            )
            
            self.cursor = self.conn.cursor()
            spider.logger.info("✅ Normalized MySQL connection successful")
            
            # Create tables if they don't exist
            self.create_tables_if_not_exist()
            
            # Check if we should clear existing data
            clear_data = os.getenv('CLEAR_DATA', 'false').lower() in ('1', 'true', 'yes')
            if clear_data:
                spider.logger.info("🔄 CLEAR_DATA=true - Clearing all existing data...")
                self.clear_all_data()
                spider.logger.info("✅ All existing data cleared")
            
            # Initialize counters
            self.deals_saved = 0
            self.related_deals_saved = 0
            self.images_saved = 0
            self.categories_saved = 0
            
        except mysql.connector.Error as err:
            spider.logger.error(f"❌ MySQL connection failed: {err}")
            self.mysql_enabled = False
        except Exception as e:
            spider.logger.error(f"❌ Unexpected error: {e}")
            self.mysql_enabled = False
    
    def create_tables_if_not_exist(self):
        """Create all normalized tables if they don't exist"""
        try:
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
                category VARCHAR(100),
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
                UNIQUE KEY unique_deal_filter (dealid),
                FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
                FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL,
                FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
                FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # Execute all table creation statements
            tables = [
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
            
            for table_name, create_sql in tables:
                self.cursor.execute(create_sql)
                print(f"[OK] Table '{table_name}' created/verified")
            
            print("[SUCCESS] All 9 normalized tables created/verified successfully!")
            
        except Exception as e:
            print(f"[ERROR] Failed to create tables: {e}")
            raise

    def close_spider(self, spider):
        if self.mysql_enabled:
            spider.logger.info(f"📊 Final stats:")
            spider.logger.info(f"   Deals saved: {self.deals_saved}")
            spider.logger.info(f"   Related deals saved: {self.related_deals_saved}")
            spider.logger.info(f"   Images saved: {self.images_saved}")
            spider.logger.info(f"   Categories saved: {self.categories_saved}")
            
            if hasattr(self, 'cursor'):
                self.cursor.close()
            if hasattr(self, 'conn'):
                self.conn.close()
            spider.logger.info("🔌 Normalized MySQL connection closed")

    def process_item(self, item, spider):
        if not self.mysql_enabled:
            return item
            
        try:
            if isinstance(item, DealnewsItem):
                spider.logger.info(f"Processing main deal: {item.get('title', '')[:50]}...")
                return self.process_deal_item(item, spider)
            elif isinstance(item, DealImageItem):
                spider.logger.info(f"Processing deal image: {item.get('imageurl', '')[:50]}...")
                return self.process_image_item(item, spider)
            elif isinstance(item, DealCategoryItem):
                spider.logger.info(f"Processing deal category: {item.get('category_name', '')}")
                return self.process_category_item(item, spider)
            elif isinstance(item, RelatedDealItem):
                return self.process_related_deal_item(item, spider)
        except Exception as e:
            spider.logger.error(f"❌ Error processing item: {e}")
            
        return item

    def process_deal_item(self, item, spider):
        """Process main deal item and save to normalized tables"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                dealid = item.get('dealid', '')
                if not dealid:
                    spider.logger.warning("Skipping deal without dealid")
                    return item
                
                spider.logger.info(f"Processing deal {dealid}: {item.get('title', '')[:50]}...")
                
                # Check if deal already exists (unless force update is enabled)
                force_update = os.getenv('FORCE_UPDATE', 'false').lower() in ('1', 'true', 'yes')
                clear_data = os.getenv('CLEAR_DATA', 'false').lower() in ('1', 'true', 'yes')
                capture_mode = os.getenv('CAPTURE_MODE', 'incremental').lower()  # 'full' | 'incremental'
                
                if force_update or clear_data or capture_mode == 'full':
                    # Force update mode or clear data mode - delete existing deal first
                    self.cursor.execute("DELETE FROM deals WHERE dealid = %s", (dealid,))
                    self.cursor.execute("DELETE FROM deal_filters WHERE dealid = %s", (dealid,))
                    self.cursor.execute("DELETE FROM related_deals WHERE dealid = %s", (dealid,))
                    self.cursor.execute("DELETE FROM deal_images WHERE dealid = %s", (dealid,))
                    self.cursor.execute("DELETE FROM deal_categories WHERE dealid = %s", (dealid,))
                    spider.logger.info(f"Force update/clear mode: Re-scraping deal {dealid}")
                # else: no skip; proceed to upsert and process filters/relations
                
                # 1. Save to main deals table
                deal_sql = """
                INSERT INTO deals (dealid, recid, url, title, price, promo, category, store, deal, dealplus, 
                                 deallink, dealtext, dealhover, published, popularity, staffpick, 
                                 detail, raw_html, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE 
                    recid = VALUES(recid),
                    url = VALUES(url),
                    title = VALUES(title),
                    price = VALUES(price),
                    promo = VALUES(promo),
                    category = VALUES(category),
                    store = VALUES(store),
                    deal = VALUES(deal),
                    dealplus = VALUES(dealplus),
                    deallink = VALUES(deallink),
                    dealtext = VALUES(dealtext),
                    dealhover = VALUES(dealhover),
                    published = VALUES(published),
                    popularity = VALUES(popularity),
                    staffpick = VALUES(staffpick),
                    detail = VALUES(detail),
                    raw_html = VALUES(raw_html)
                """
                
                deal_values = (
                    dealid,
                    item.get('recid', ''),
                    item.get('url', ''),
                    item.get('title', ''),
                    item.get('price', ''),
                    item.get('promo', ''),
                    item.get('category', ''),
                    item.get('store', ''),
                    item.get('deal', ''),
                    item.get('dealplus', ''),
                    item.get('deallink', ''),
                    item.get('dealtext', ''),
                    item.get('dealhover', ''),
                    item.get('published', ''),
                    item.get('popularity', ''),
                    item.get('staffpick', ''),
                    item.get('detail', ''),
                    item.get('raw_html', '')[:10000] if item.get('raw_html') else ''  # Limit HTML size
                )
                
                self.cursor.execute(deal_sql, deal_values)
                affected_rows = self.cursor.rowcount
                self.deals_saved += 1
                spider.logger.info(f"✅ Successfully saved deal {dealid} to database (total saved: {self.deals_saved}, affected rows: {affected_rows})")
                
                # 2. Save store to stores table (normalized)
                store_name = item.get('store', '')
                if store_name:
                    self.save_store(store_name)
                    store_id = self.get_store_id(store_name)
                else:
                    store_id = None
                
                # 3. Save categories to categories table (normalized)
                categories = item.get('categories', [])
                if categories:
                    for category in categories:
                        if isinstance(category, dict):
                            cat_name = category.get('name', '')
                            cat_url = category.get('url', '')
                            cat_title = category.get('title', '')
                        else:
                            cat_name = str(category)
                            cat_url = ''
                            cat_title = ''
                        
                        if cat_name:
                            self.save_category(cat_name, cat_url, cat_title)
                            category_id = self.get_category_id(cat_name)
                            self.save_deal_category(dealid, category_id)
                
                # 4. Save brand to brands table (normalized)
                brand_name = item.get('brand', '')
                if brand_name:
                    self.save_brand(brand_name)
                    brand_id = self.get_brand_id(brand_name)
                else:
                    brand_id = None
                
                # 5. Save collection to collections table (normalized)
                collection_name = item.get('collection', '')
                if collection_name:
                    self.save_collection(collection_name)
                    collection_id = self.get_collection_id(collection_name)
                else:
                    collection_id = None
                
                # 6. Save filter variables to deal_filters table
                self.save_deal_filters(
                    dealid=dealid,
                    store_id=store_id,
                    brand_id=brand_id,
                    collection_id=collection_id,
                    offer_type=item.get('offer_type', ''),
                    condition_type=item.get('condition', ''),
                    events=item.get('events', ''),
                    offer_status=item.get('offer_status', ''),
                    include_expired=item.get('include_expired', 'No') == 'Yes',
                    category_id=self.get_category_id(item.get('category', '')),
                    start_date=item.get('start_date') or None,
                    max_price=item.get('max_price') or None,
                    popularity_rank=item.get('popularity_rank') or None
                )
                
                # 7. Save related deals
                related_deals = item.get('related_deals', [])
                if related_deals:
                    for related_url in related_deals[:25]:  # Save up to 25 related
                        self.save_related_deal(dealid, related_url)
                        self.related_deals_saved += 1
                
                spider.logger.info(f"Saved deal {dealid} with {len(related_deals)} related deals")
                break  # Success, exit retry loop
                
            except mysql.connector.Error as err:
                spider.logger.error(f"❌ MySQL error saving deal (attempt {attempt + 1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    spider.logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                    # Try to reconnect
                    try:
                        self.conn.reconnect()
                        self.cursor = self.conn.cursor()
                    except:
                        pass
                else:
                    spider.logger.error(f"❌ Failed to save deal after {max_retries} attempts")
            except Exception as e:
                spider.logger.error(f"❌ Error saving deal (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    spider.logger.info(f"Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    spider.logger.error(f"❌ Failed to save deal after {max_retries} attempts")
            
        return item

    def save_store(self, store_name):
        """Save store to stores table"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO stores (store_name) VALUES (%s)",
                (store_name,)
            )
        except Exception as e:
            pass  # Ignore duplicate errors

    def get_store_id(self, store_name):
        """Get store ID from stores table"""
        try:
            self.cursor.execute("SELECT id FROM stores WHERE store_name = %s", (store_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def save_category(self, category_name, category_url, category_title):
        """Save category to categories table"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO categories (category_name, category_url, category_title) VALUES (%s, %s, %s)",
                (category_name, category_url, category_title)
            )
        except Exception as e:
            pass  # Ignore duplicate errors

    def get_category_id(self, category_name):
        """Get category ID from categories table"""
        try:
            self.cursor.execute("SELECT id FROM categories WHERE category_name = %s", (category_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def save_deal_category(self, dealid, category_id):
        """Save deal-category relationship"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO deal_categories (dealid, category_id) VALUES (%s, %s)",
                (dealid, category_id)
            )
            self.categories_saved += 1
        except Exception as e:
            pass  # Ignore duplicate errors

    def save_brand(self, brand_name):
        """Save brand to brands table"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO brands (brand_name) VALUES (%s)",
                (brand_name,)
            )
        except Exception as e:
            pass  # Ignore duplicate errors

    def get_brand_id(self, brand_name):
        """Get brand ID from brands table"""
        try:
            self.cursor.execute("SELECT id FROM brands WHERE brand_name = %s", (brand_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def save_collection(self, collection_name):
        """Save collection to collections table"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO collections (collection_name) VALUES (%s)",
                (collection_name,)
            )
        except Exception as e:
            pass  # Ignore duplicate errors

    def get_collection_id(self, collection_name):
        """Get collection ID from collections table"""
        try:
            self.cursor.execute("SELECT id FROM collections WHERE collection_name = %s", (collection_name,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception:
            return None

    def save_deal_filters(self, dealid, store_id, brand_id, collection_id, 
                         offer_type, condition_type, events, offer_status, include_expired,
                         category_id=None, start_date=None, max_price=None, popularity_rank=None):
        """Save filter variables to deal_filters table"""
        try:
            # Convert boolean to int for MySQL
            include_expired_int = 1 if include_expired else 0
            
            self.cursor.execute("""
                INSERT INTO deal_filters (
                    dealid, start_date, max_price, category_id, store_id, brand_id, collection_id,
                    offer_type, popularity_rank, condition_type, events, offer_status, include_expired
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    start_date = VALUES(start_date),
                    max_price = VALUES(max_price),
                    category_id = VALUES(category_id),
                    store_id = VALUES(store_id),
                    brand_id = VALUES(brand_id),
                    collection_id = VALUES(collection_id),
                    offer_type = VALUES(offer_type),
                    popularity_rank = VALUES(popularity_rank),
                    condition_type = VALUES(condition_type),
                    events = VALUES(events),
                    offer_status = VALUES(offer_status),
                    include_expired = VALUES(include_expired)
            """, (
                dealid, start_date, max_price, category_id, store_id, brand_id, collection_id,
                offer_type, popularity_rank, condition_type, events, offer_status, include_expired_int
            ))
        except Exception as e:
            print(f"Error saving deal_filters: {e}")  # Debug output
            pass  # Ignore errors

    def save_related_deal(self, dealid, related_url):
        """Save related deal to related_deals table"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO related_deals (dealid, related_url) VALUES (%s, %s)",
                (dealid, related_url)
            )
        except Exception as e:
            pass  # Ignore duplicate errors

    def process_image_item(self, item, spider):
        """Process image item"""
        try:
            dealid = item.get('dealid', '')
            imageurl = item.get('imageurl', '')
            
            if dealid and imageurl:
                self.cursor.execute(
                    "INSERT IGNORE INTO deal_images (dealid, imageurl) VALUES (%s, %s)",
                    (dealid, imageurl)
                )
                self.images_saved += 1
        except Exception as e:
            spider.logger.error(f"❌ Error saving image: {e}")
            
        return item

    def process_category_item(self, item, spider):
        """Process category item"""
        return item  # Categories are handled in process_deal_item

    def process_related_deal_item(self, item, spider):
        """Process related deal item"""
        return item  # Related deals are handled in process_deal_item
    
    def close_spider(self, spider):
        """Close spider and run second pass to populate missing normalized data"""
        if self.mysql_enabled:
            try:
                # Run second pass to populate missing normalized data
                self.populate_missing_normalized_data(spider)
                
                spider.logger.info(f"✅ Final Statistics:")
                spider.logger.info(f"   Deals saved: {self.deals_saved}")
                spider.logger.info(f"   Related deals saved: {self.related_deals_saved}")
                spider.logger.info(f"   Images saved: {self.images_saved}")
                spider.logger.info(f"   Categories saved: {self.categories_saved}")
                
                self.cursor.close()
                self.conn.close()
                spider.logger.info("✅ MySQL connection closed")
            except Exception as e:
                spider.logger.error(f"❌ Error closing MySQL connection: {e}")
    
    def populate_missing_normalized_data(self, spider):
        """Second pass to populate missing normalized data from existing deals"""
        try:
            spider.logger.info("🔄 Running second pass to populate normalized tables...")
            
            # Get all deals that need normalized data
            self.cursor.execute("SELECT dealid, title, url, store FROM deals WHERE store IS NOT NULL AND store != ''")
            deals = self.cursor.fetchall()
            
            stores_populated = 0
            brands_populated = 0
            categories_populated = 0
            deal_categories_populated = 0
            related_deals_populated = 0
            collections_populated = 0
            
            for deal in deals:
                dealid, title, url, store = deal
                
                # Populate stores table
                if store and store != 'Unknown Store':
                    self.save_store(store)
                    stores_populated += 1
                
                # Extract and populate brand from title
                brand = self.extract_brand_from_title(title)
                if brand:
                    self.save_brand(brand)
                    brands_populated += 1
                
                # Extract and populate category from URL
                category = self.extract_category_from_url(url)
                if category:
                    self.save_category(category, url, category)
                    categories_populated += 1
                    
                    # Link deal to category by id
                    category_id = self.get_category_id(category)
                    if category_id:
                        self.save_deal_category(dealid, category_id)
                        deal_categories_populated += 1
                
                # Extract and populate collections
                collection = self.extract_collection_from_url(url)
                if collection:
                    self.save_collection(collection, url)
                    collections_populated += 1
                
                # Extract related deals from deal text
                related_deals = self.extract_related_deals_from_text(title + " " + (store or ""))
                for related_deal in related_deals:
                    self.save_related_deal(dealid, related_deal)
                    related_deals_populated += 1
            
            spider.logger.info(f"✅ Second pass completed:")
            spider.logger.info(f"   Stores populated: {stores_populated}")
            spider.logger.info(f"   Brands populated: {brands_populated}")
            spider.logger.info(f"   Categories populated: {categories_populated}")
            spider.logger.info(f"   Deal-Category links: {deal_categories_populated}")
            spider.logger.info(f"   Related deals: {related_deals_populated}")
            spider.logger.info(f"   Collections: {collections_populated}")
            
        except Exception as e:
            spider.logger.error(f"❌ Error in second pass: {e}")
    
    def extract_brand_from_title(self, title):
        """Extract brand from deal title"""
        if not title:
            return None
        
        # Common brand patterns
        brand_patterns = [
            'Apple', 'Samsung', 'Nike', 'Adidas', 'Sony', 'Microsoft', 'Google', 
            'Amazon', 'Walmart', 'Target', 'Best Buy', 'HP', 'Dell', 'Lenovo',
            'Canon', 'Nikon', 'Bose', 'JBL', 'LG', 'Panasonic', 'Philips',
            'Intel', 'AMD', 'NVIDIA', 'ASUS', 'Acer', 'MSI', 'Razer',
            'Corsair', 'Logitech', 'SteelSeries', 'HyperX', 'Kingston',
            'Western Digital', 'Seagate', 'SanDisk', 'Crucial'
        ]
        
        title_lower = title.lower()
        for brand in brand_patterns:
            if brand.lower() in title_lower:
                return brand
        
        return None
    
    def extract_category_from_url(self, url):
        """Extract category from deal URL"""
        if not url:
            return None
        
        # Extract category from URL patterns
        if '/cat/' in url:
            # Extract category from /cat/Category/Subcategory/ pattern
            parts = url.split('/cat/')
            if len(parts) > 1:
                category_part = parts[1].split('/')[0]
                # Convert to readable format
                category = category_part.replace('-', ' ').replace('_', ' ').title()
                return category
        
        return None
    
    def clear_all_data(self):
        """Clear all existing data from all tables"""
        try:
            # Clear all tables in correct order (respecting foreign key constraints)
            tables_to_clear = [
                'deal_filters',
                'deal_categories', 
                'related_deals',
                'deal_images',
                'deals',
                'stores',
                'categories',
                'brands',
                'collections'
            ]
            
            for table in tables_to_clear:
                self.cursor.execute(f"DELETE FROM {table}")
                self.cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")
            
        except Exception as e:
            pass  # Ignore errors during clearing
    
    def save_deal_category(self, dealid, category_id):
        """Save deal-category relationship by category_id"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO deal_categories (dealid, category_id) VALUES (%s, %s)",
                (dealid, category_id)
            )
        except Exception as e:
            pass  # Ignore duplicate errors
    
    def save_collection(self, collection_name, collection_url=None):
        """Save collection to collections table"""
        try:
            # Base schema uses only collection_name
            self.cursor.execute(
                "INSERT IGNORE INTO collections (collection_name) VALUES (%s)",
                (collection_name,)
            )
        except Exception:
            # Extended schema fallback
            try:
                self.cursor.execute(
                    "INSERT IGNORE INTO collections (collection_name, collection_url) VALUES (%s, %s)",
                    (collection_name, collection_url or '')
                )
            except Exception:
                pass
    
    def save_related_deal(self, dealid, related_deal_text):
        """Save related deal"""
        try:
            self.cursor.execute(
                "INSERT IGNORE INTO related_deals (dealid, related_deal_text) VALUES (%s, %s)",
                (dealid, related_deal_text)
            )
        except Exception as e:
            pass  # Ignore duplicate errors
    
    def extract_collection_from_url(self, url):
        """Extract collection from URL"""
        if not url:
            return None
        
        # Extract collection from URL patterns
        if '/s' in url:
            # Extract from /s123/Collection-Name/ pattern
            parts = url.split('/s')
            if len(parts) > 1:
                collection_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else ''
                return collection_part.replace('-', ' ').title()
        
        return None
    
    def extract_related_deals_from_text(self, text):
        """Extract related deals from text"""
        if not text:
            return []
        
        # Simple keyword-based related deal extraction
        related_keywords = [
            'similar', 'related', 'also', 'compare', 'alternative', 'other',
            'like this', 'see also', 'more deals', 'related deals'
        ]
        
        related_deals = []
        text_lower = text.lower()
        
        for keyword in related_keywords:
            if keyword in text_lower:
                # Extract surrounding text as related deal
                start = text_lower.find(keyword)
                if start != -1:
                    related_text = text[max(0, start-50):start+100]
                    if related_text.strip():
                        related_deals.append(related_text.strip())
        
        return related_deals[:3]  # Limit to 3 related deals
