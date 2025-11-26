import os
import time
import mysql.connector
import logging
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem

class NormalizedMySQLPipeline:
    """MySQL pipeline that stores all deal data in normalized tables.
    
    Tables:
    - deals: Main deal information
    - deal_images: Multiple images per deal (unique constraint on dealid+imageurl)
    - deal_categories: Multiple categories per deal
    - related_deals: Multiple related deals per deal (unique constraint on dealid+relatedurl)
    """
    
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
            
            # Test connection first
            try:
                test_conn = mysql.connector.connect(
                    host=mysql_host,
                    port=mysql_port,
                    user=mysql_user,
                    password=mysql_password,
                    database=mysql_database,
                    connection_timeout=10
                )
                test_conn.close()
                spider.logger.info("✅ MySQL connection test successful")
            except mysql.connector.Error as conn_err:
                spider.logger.error(f"❌ MySQL connection failed: {conn_err}")
                spider.logger.info("Disabling MySQL pipeline - data will only be exported to JSON/CSV")
                spider.logger.info("To enable MySQL: 1) Start MySQL server, 2) Update .env with correct credentials")
                self.mysql_enabled = False
                return

            # If connection test passed, create main connection
            self.conn = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                use_pure=True,
                connection_timeout=60,
                autocommit=True,
                pool_name='dealnews_pool',
                pool_size=5,
                pool_reset_session=True
            )
            
            self.cursor = self.conn.cursor()
            spider.logger.info("✅ Normalized MySQL connection successful")
            
            # Create all tables
            self.create_all_tables()
            
            # Check if we should clear existing data
            clear_data = os.getenv('CLEAR_DATA', 'false').lower() in ('1', 'true', 'yes')
            if clear_data:
                spider.logger.info("🔄 CLEAR_DATA=true - Clearing all existing data...")
                self.clear_all_data()
                spider.logger.info("✅ All existing data cleared")
            
            # Initialize counters
            self.deals_saved = 0
            self.images_saved = 0
            self.categories_saved = 0
            self.related_deals_saved = 0
            
        except Exception as e:
            spider.logger.error(f"❌ Unexpected error in pipeline setup: {e}")
            spider.logger.info("Disabling MySQL pipeline - data will only be exported to JSON/CSV")
            self.mysql_enabled = False
    
    def create_all_tables(self):
        """Create all normalized tables if they don't exist."""
        try:
            # Read SQL file or create tables directly
            sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mysql-init', '01_create_deals.sql')
            if os.path.exists(sql_file):
                with open(sql_file, 'r') as f:
                    sql_commands = f.read()
                    # Split by semicolon and execute each command
                    for command in sql_commands.split(';'):
                        command = command.strip()
                        if command:
                            try:
                                self.cursor.execute(command)
                            except mysql.connector.Error as e:
                                if "already exists" not in str(e).lower():
                                    print(f"[WARNING] {e}")
            else:
                # Fallback: create tables directly
                self.create_tables_directly()
            
            print("[OK] All tables created/verified")
            print("[SUCCESS] Database schema ready!")
            
        except Exception as e:
            print(f"[ERROR] Failed to create tables: {e}")
            raise
    
    def create_tables_directly(self):
        """Create tables directly if SQL file is not available."""
        # Main deals table
        create_deals_table = """
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
        self.cursor.execute(create_deals_table)
        
        # Deal images table (unique constraint prevents duplicates)
        create_images_table = """
        CREATE TABLE IF NOT EXISTS deal_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50) NOT NULL,
            imageurl TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_deal_image (dealid, imageurl(255)),
            INDEX idx_dealid (dealid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.cursor.execute(create_images_table)
        
        # Deal categories table (multiple categories per deal)
        # Unique constraint on (dealid, category_name) prevents duplicate categories per deal
        create_categories_table = """
        CREATE TABLE IF NOT EXISTS deal_categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50) NOT NULL,
            category_id VARCHAR(100),
            category_name VARCHAR(255),
            category_url TEXT,
            category_title VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_deal_category (dealid, category_name(255)),
            INDEX idx_dealid (dealid),
            INDEX idx_category_name (category_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.cursor.execute(create_categories_table)
        
        # Related deals table (unique constraint prevents duplicates)
        create_related_table = """
        CREATE TABLE IF NOT EXISTS related_deals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50) NOT NULL,
            relatedurl TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_related_deal (dealid, relatedurl(255)),
            INDEX idx_dealid (dealid)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        self.cursor.execute(create_related_table)

    def clear_all_data(self):
        """Clear all data from all tables"""
        try:
            # Clear all tables (no foreign keys, so order doesn't matter)
            self.cursor.execute("TRUNCATE TABLE related_deals")
            self.cursor.execute("TRUNCATE TABLE deal_categories")
            self.cursor.execute("TRUNCATE TABLE deal_images")
            self.cursor.execute("TRUNCATE TABLE deals")
            self.conn.commit()
        except Exception as e:
            print(f"[ERROR] Failed to clear data: {e}")
            raise

    def close_spider(self, spider):
        if self.mysql_enabled:
            spider.logger.info(f"📊 Final stats:")
            spider.logger.info(f"   Deals saved: {self.deals_saved:,}")
            spider.logger.info(f"   Images saved: {self.images_saved:,}")
            spider.logger.info(f"   Categories saved: {self.categories_saved:,}")
            spider.logger.info(f"   Related deals saved: {self.related_deals_saved:,}")
            
            if hasattr(self, 'cursor'):
                self.cursor.close()
            if hasattr(self, 'conn'):
                self.conn.close()
            spider.logger.info("🔌 MySQL connection closed")

    def process_item(self, item, spider):
        if not self.mysql_enabled:
            return item
            
        try:
            if isinstance(item, DealnewsItem):
                return self.process_deal_item(item, spider)
            elif isinstance(item, DealImageItem):
                return self.process_image_item(item, spider)
            elif isinstance(item, DealCategoryItem):
                return self.process_category_item(item, spider)
            elif isinstance(item, RelatedDealItem):
                return self.process_related_deal_item(item, spider)
        except Exception as e:
            spider.logger.error(f"❌ Error processing item: {e}")
            
        return item

    def process_deal_item(self, item, spider):
        """Process main deal item and save to deals table"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                dealid = item.get('dealid', '')
                title = item.get('title', '').strip()
                
                if not dealid:
                    spider.logger.debug("Skipping deal without dealid")
                    return item
                
                # Skip obvious non-deal placeholders
                if dealid.startswith('dealnewsjs') or dealid.startswith('simpleslider'):
                    spider.logger.debug(f"Skipping placeholder dealid: {dealid}")
                    return item
                
                url = item.get('url', '').strip()
                if not url or (url == 'https://www.dealnews.com/' and not dealid):
                    spider.logger.debug(f"Skipping deal {dealid} with invalid URL: {url}")
                    return item
                
                if (not title or title == 'No title found') and not (item.get('deallink') or url):
                    spider.logger.debug(f"Skipping empty item for dealid {dealid}")
                    return item
                
                # Save to deals table
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
                    raw_html = VALUES(raw_html),
                    updated_at = NOW()
                """
                
                # Clean HTML entities from category field and truncate if needed
                category_value = (item.get('category', '') or '').strip()
                # Decode HTML entities (e.g., &amp; -> &, &nbsp; -> space, &gt; -> >)
                if category_value:
                    import html
                    import re
                    category_value = html.unescape(category_value)
                    # Also replace &nbsp; with space (html.unescape doesn't handle all cases)
                    category_value = category_value.replace('&nbsp;', ' ').replace('\xa0', ' ')
                    # Clean up multiple spaces
                    category_value = re.sub(r'\s+', ' ', category_value).strip()
                    # Truncate to 255 characters to fit VARCHAR(255)
                    category_value = category_value[:255]
                
                deal_values = (
                    dealid,
                    item.get('recid', '') or '',
                    url,
                    title,
                    item.get('price', '') or '',
                    item.get('promo', '') or '',
                    category_value,
                    item.get('store', '') or '',
                    item.get('deal', '') or '',
                    item.get('dealplus', '') or '',
                    item.get('deallink', '') or url,
                    item.get('dealtext', '') or item.get('detail', '') or '',
                    item.get('dealhover', '') or '',
                    item.get('published', '') or '',
                    item.get('popularity', '') or '',
                    item.get('staffpick', '') or '',
                    item.get('detail', '') or '',
                    item.get('raw_html', '')[:50000] if item.get('raw_html') else ''  # Limit raw_html size
                )
                
                self.cursor.execute(deal_sql, deal_values)
                self.deals_saved += 1
                
                # Also save images, categories, and related deals from the main item if present
                images_list = item.get('images', [])
                if images_list:
                    spider.logger.debug(f"Saving {len(images_list)} images for deal {dealid}")
                    for img_url in images_list:
                        if img_url and img_url.strip():
                            self.save_image(dealid, img_url.strip(), spider)
                else:
                    spider.logger.debug(f"No images found for deal {dealid}")
                
                categories_list = item.get('categories', [])
                if categories_list:
                    spider.logger.debug(f"Saving {len(categories_list)} categories for deal {dealid}")
                    for cat in categories_list:
                        if isinstance(cat, dict):
                            self.save_category(dealid, cat, spider)
                        elif isinstance(cat, str) and cat.strip():
                            self.save_category(dealid, {'category_name': cat.strip()}, spider)
                else:
                    # At least save the main category from item if available
                    main_category = item.get('category', '').strip()
                    if main_category:
                        spider.logger.debug(f"Saving main category '{main_category}' for deal {dealid}")
                        self.save_category(dealid, {'category_name': main_category}, spider)
                    else:
                        spider.logger.debug(f"No categories found for deal {dealid}")
                
                related_deals_list = item.get('related_deals', [])
                if related_deals_list:
                    spider.logger.debug(f"Saving {len(related_deals_list)} related deals for deal {dealid}")
                    for rel_url in related_deals_list:
                        if rel_url and rel_url.strip():
                            self.save_related_deal(dealid, rel_url.strip(), spider)
                else:
                    spider.logger.debug(f"No related deals found for deal {dealid}")
                
                if self.deals_saved % 100 == 0:
                    spider.logger.info(f"✅ Saved {self.deals_saved:,} deals, {self.images_saved:,} images, {self.categories_saved:,} categories, {self.related_deals_saved:,} related deals")
                
                break  # Success, exit retry loop
                
            except mysql.connector.Error as err:
                spider.logger.error(f"❌ MySQL error saving deal (attempt {attempt + 1}/{max_retries}): {err}")
                if attempt < max_retries - 1:
                    time.sleep(2)
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
                    time.sleep(2)
                else:
                    spider.logger.error(f"❌ Failed to save deal after {max_retries} attempts")
            
        return item

    def process_image_item(self, item, spider):
        """Process deal image item"""
        dealid = item.get('dealid', '')
        imageurl = item.get('imageurl', '').strip()
        
        if dealid and imageurl:
            self.save_image(dealid, imageurl, spider)
        
        return item

    def process_category_item(self, item, spider):
        """Process deal category item"""
        dealid = item.get('dealid', '')
        if dealid:
            cat_data = {
                'category_name': item.get('category_name', ''),
                'category_url': item.get('category_url', ''),
                'category_title': item.get('category_title', ''),
                'category_id': item.get('category_id', '')
            }
            self.save_category(dealid, cat_data, spider)
        
        return item

    def process_related_deal_item(self, item, spider):
        """Process related deal item"""
        dealid = item.get('dealid', '')
        relatedurl = item.get('relatedurl', '').strip()
        
        if dealid and relatedurl:
            self.save_related_deal(dealid, relatedurl, spider)
        
        return item

    def save_image(self, dealid, imageurl, spider):
        """Save image with unique constraint (handles duplicates)"""
        if not dealid or not imageurl or not imageurl.strip():
            return
        
        try:
            # Make image URL absolute if relative
            if not imageurl.startswith('http'):
                # Try to construct absolute URL (will be handled by spider if needed)
                pass
            
            image_sql = """
            INSERT INTO deal_images (dealid, imageurl, created_at)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE created_at = created_at
            """
            self.cursor.execute(image_sql, (dealid, imageurl.strip()))
            self.images_saved += 1
            spider.logger.debug(f"✅ Saved image for deal {dealid}: {imageurl[:50]}...")
        except mysql.connector.Error as err:
            # Ignore duplicate key errors (expected)
            if "Duplicate entry" not in str(err):
                spider.logger.warning(f"❌ Error saving image for deal {dealid}: {err}")

    def save_category(self, dealid, cat_data, spider):
        """Save category with unique constraint (handles duplicates)"""
        try:
            category_name = (cat_data.get('category_name', '') or '').strip()
            if not category_name:
                return  # Skip empty categories
            
            # Clean HTML entities from category name
            import html
            category_name = html.unescape(category_name)
            # Also replace &nbsp; with space (html.unescape doesn't handle all cases)
            category_name = category_name.replace('&nbsp;', ' ').replace('\xa0', ' ')
            # Clean up multiple spaces
            import re
            category_name = re.sub(r'\s+', ' ', category_name).strip()
            # Truncate to 255 characters
            category_name = category_name[:255]
            
            category_sql = """
            INSERT INTO deal_categories (dealid, category_id, category_name, category_url, category_title, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE 
                category_id = VALUES(category_id),
                category_url = VALUES(category_url),
                category_title = VALUES(category_title),
                created_at = created_at
            """
            self.cursor.execute(category_sql, (
                dealid,
                cat_data.get('category_id', '') or '',
                category_name,
                cat_data.get('category_url', '') or '',
                cat_data.get('category_title', '') or ''
            ))
            self.categories_saved += 1
            spider.logger.debug(f"✅ Saved category '{category_name}' for deal {dealid}")
        except mysql.connector.Error as err:
            # Ignore duplicate key errors (expected due to unique constraint)
            if "Duplicate entry" not in str(err):
                spider.logger.warning(f"❌ Error saving category for deal {dealid}: {err}")

    def save_related_deal(self, dealid, relatedurl, spider):
        """Save related deal with unique constraint (handles duplicates)"""
        if not dealid or not relatedurl or not relatedurl.strip():
            return
        
        try:
            related_sql = """
            INSERT INTO related_deals (dealid, relatedurl, created_at)
            VALUES (%s, %s, NOW())
            ON DUPLICATE KEY UPDATE created_at = created_at
            """
            self.cursor.execute(related_sql, (dealid, relatedurl.strip()))
            self.related_deals_saved += 1
            spider.logger.debug(f"✅ Saved related deal for deal {dealid}: {relatedurl[:50]}...")
        except mysql.connector.Error as err:
            # Ignore duplicate key errors (expected)
            if "Duplicate entry" not in str(err):
                spider.logger.warning(f"❌ Error saving related deal for deal {dealid}: {err}")
