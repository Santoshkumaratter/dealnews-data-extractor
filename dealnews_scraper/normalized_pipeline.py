import os
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
                connection_timeout=30,
                autocommit=True
            )
            
            self.cursor = self.conn.cursor()
            spider.logger.info("✅ Normalized MySQL connection successful")
            
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
        """Process main deal item and save to normalized tables"""
        try:
            dealid = item.get('dealid', '')
            if not dealid:
                spider.logger.warning("Skipping deal without dealid")
                return item
            
            # Check if deal already exists
            self.cursor.execute("SELECT id FROM deals WHERE dealid = %s", (dealid,))
            if self.cursor.fetchone():
                spider.logger.info(f"Deal {dealid} already exists, skipping")
                return item
            
            # 1. Save to main deals table
            deal_sql = """
            INSERT INTO deals (dealid, recid, url, title, price, promo, deal, dealplus, 
                             deallink, dealtext, dealhover, published, popularity, staffpick, 
                             detail, raw_html, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            deal_values = (
                dealid,
                item.get('recid', ''),
                item.get('url', ''),
                item.get('title', ''),
                item.get('price', ''),
                item.get('promo', ''),
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
            self.deals_saved += 1
            
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
                include_expired=item.get('include_expired', 'No') == 'Yes'
            )
            
            # 7. Save related deals
            related_deals = item.get('related_deals', [])
            if related_deals and len(related_deals) >= 3:  # Ensure 3+ related deals
                for related_url in related_deals[:10]:  # Limit to 10 related deals
                    self.save_related_deal(dealid, related_url)
                    self.related_deals_saved += 1
            
            spider.logger.info(f"✅ Saved deal {dealid} with {len(related_deals)} related deals")
            
        except mysql.connector.Error as err:
            spider.logger.error(f"❌ MySQL error saving deal: {err}")
        except Exception as e:
            spider.logger.error(f"❌ Error saving deal: {e}")
            
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
                         offer_type, condition_type, events, offer_status, include_expired):
        """Save filter variables to deal_filters table"""
        try:
            self.cursor.execute("""
                INSERT INTO deal_filters (dealid, store_id, brand_id, collection_id, 
                                        offer_type, condition_type, events, offer_status, include_expired)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (dealid, store_id, brand_id, collection_id, offer_type, 
                  condition_type, events, offer_status, include_expired))
        except Exception as e:
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
