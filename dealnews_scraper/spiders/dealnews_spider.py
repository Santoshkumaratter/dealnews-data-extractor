import scrapy
import re
import time
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

class DealnewsSpider(scrapy.Spider):
    name = "dealnews"
    allowed_domains = ["dealnews.com"]
    handle_httpstatus_list = [400, 403, 404]  # Handle these status codes explicitly
    
    def __init__(self):
        super().__init__()
        self.deals_extracted = 0
        self.start_time = time.time()
        self.max_deals = 100000  # Target: 100,000+ deals
    
    # Optimized start URLs - pagination will automatically handle 100k+ deals
    start_urls = [
        "https://www.dealnews.com/",
        "https://www.dealnews.com/?e=1",  # All deals
        "https://www.dealnews.com/?pf=1",  # Staff picks
        "https://www.dealnews.com/online-stores/",
        # Main category pages - pagination will crawl deep
        "https://www.dealnews.com/c142/Electronics/",
        "https://www.dealnews.com/c39/Computers/",
        "https://www.dealnews.com/c196/Home-Garden/",
        "https://www.dealnews.com/c202/Clothing-Accessories/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/",
        "https://www.dealnews.com/c298/Sports-Fitness/",
        "https://www.dealnews.com/c765/Health-Beauty/",
        "https://www.dealnews.com/c206/Travel-Entertainment/",
    ]

    def start_requests(self):
        """Start requests with proper error handling"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_http,
                meta={'dont_cache': True}
            )

    def errback_http(self, failure):
        """Handle HTTP errors"""
        self.logger.error(f"Request failed: {failure.request.url} - {failure.value}")

    def parse(self, response):
        """Main parsing method with IMPROVED DEAL EXTRACTION"""
        if response.status == 400:
            self.logger.warning(f"400 error for URL: {response.url} - stopping this branch")
            return
        if response.status == 404:
            self.logger.warning(f"404 error for URL: {response.url}")
            return
        
        if response.status == 403:
            self.logger.warning(f"403 error for URL: {response.url}")
            return
        
        self.logger.info(f"Parsing: {response.url}")
        
        # IMPROVED DEAL EXTRACTION - Try multiple strategies
        deals = []
        
        # Strategy 1: Look for deal links (most reliable)
        deal_links = response.css('a[href*="/deals/"], a[href*="/deal/"], a[href*="/d/"]')
        for link in deal_links:
            # Get parent container
            parent = link.xpath('./ancestor::*[contains(@class, "deal") or contains(@class, "item") or contains(@class, "card")][1]')
            if parent:
                deals.extend(parent)
            else:
                # Use the link itself as deal container
                deals.append(link.xpath('./..'))
        
        # Strategy 2: Data attributes
        data_deals = response.css('[data-deal-id], [data-rec-id], [data-deal], [data-id*="deal"]')
        deals.extend(data_deals)
        
        # Strategy 3: Common deal container classes
        container_selectors = [
            'article.deal', 'article[class*="deal"]',
            'div.deal-item', 'div[class*="deal-item"]',
            'div.deal-card', 'div[class*="deal-card"]',
            'div.deal-tile', 'div[class*="deal-tile"]',
            'div[class*="deal-container"]',
            'div[class*="deal-wrapper"]',
            'div[class*="deal-box"]',
            'div[class*="deal-content"]',
            'div[class*="deal-listing"]',
            'div[class*="deal-post"]',
            'div[class*="deal-entry"]',
            '.item[class*="deal"]',
            '.card[class*="deal"]',
            '.tile[class*="deal"]',
        ]
        
        for selector in container_selectors:
            found = response.css(selector)
            if found:
                deals.extend(found)
        
        # Strategy 4: Look for product/offer containers
        product_containers = response.css('[class*="product"], [class*="offer"], [class*="listing"]')
        for container in product_containers:
            # Check if it has deal-like content
            text = container.get()
            if text and ('deal' in text.lower() or '$' in text or 'off' in text.lower() or 'sale' in text.lower()):
                deals.append(container)
        
        # Strategy 5: Extract from JSON-LD structured data first (fastest)
        json_deals = response.css('script[type="application/ld+json"]::text').getall()
        if json_deals:
            import json
            for json_str in json_deals:
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict) and data.get('@type') in ['Offer', 'Product', 'ItemList']:
                        # Create a virtual deal container for JSON data
                        deals.append(response.css('body').xpath('./script[contains(text(), "@type")][1]'))
                except:
                    pass
        
        # Strategy 6: DealNews click-out links (very common on listing pages)
        click_links = response.css('a[href*="lw/click.html"]')
        for a in click_links:
            # Prefer nearest meaningful container
            parent = (
                a.xpath('./ancestor::article[1]') or
                a.xpath('./ancestor::*[contains(@class, "deal") or contains(@class, "offer") or contains(@class, "snippet") or contains(@class, "item") or contains(@class, "card")][1]')
            )
            if parent:
                deals.extend(parent)
            else:
                # Fallback to link's immediate parent
                deals.append(a.xpath('..'))
        
        # Remove duplicates
        seen = set()
        unique_deals = []
        for deal in deals:
            if deal:
                deal_html = deal.get() or ''
                deal_id = deal.css('::attr(data-deal-id)').get() or deal.css('::attr(data-rec-id)').get() or ''
                deal_url = deal.css('a::attr(href)').get() or ''
                
                # Create unique identifier
                unique_id = deal_id or deal_url or hash(deal_html[:200])
                if unique_id not in seen:
                    seen.add(unique_id)
                    unique_deals.append(deal)
        
        self.logger.info(f"Total unique deals found on {response.url}: {len(unique_deals)}")
        
        for deal in unique_deals:
            if self.deals_extracted >= self.max_deals:
                self.logger.info(f"Reached maximum deals limit: {self.max_deals}")
                return
            
            item = self.extract_deal_item(deal, response)
            if item:
                self.deals_extracted += 1
                yield item
                
                # Extract related data
                yield from self.extract_deal_images(deal, item)
                yield from self.extract_deal_categories(deal, item, response)
                yield from self.extract_related_deals(deal, item)
        
        # Handle pagination
        if len(unique_deals) == 0 and 'start=' in response.url:
            # Likely reached the end for this pagination stream (e.g., invalid/high start offset)
            self.logger.info(f"No deals found on {response.url}; stopping further pagination for this path")
            return
        yield from self.handle_pagination(response)
        
        # Log progress
        elapsed_time = time.time() - self.start_time
        rate = self.deals_extracted / elapsed_time if elapsed_time > 0 else 0
        self.logger.info(f"Progress: {self.deals_extracted} deals extracted in {elapsed_time:.1f}s (rate: {rate:.1f} deals/sec)")
        
        # Also extract deals from JSON-LD structured data (new DealNews format)
        yield from self.parse_json_ld_deals(response)

    def parse_json_ld_deals(self, response):
        """Extract deals from JSON-LD structured data (new DealNews format)"""
        import json
        
        # Look for JSON-LD structured data in script tags
        json_scripts = response.css('script[type="application/ld+json"]::text').getall()
        json_deals = []
        
        for script_content in json_scripts:
            try:
                data = json.loads(script_content)
                if isinstance(data, dict) and data.get('@type') == 'Offer':
                    json_deals.append(data)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Offer':
                            json_deals.append(item)
            except (json.JSONDecodeError, TypeError):
                continue
        
        self.logger.info(f"Found {len(json_deals)} JSON-LD deals on {response.url}")
        
        for deal_data in json_deals:
            if self.deals_extracted >= self.max_deals:
                self.logger.info(f"Reached maximum deals limit: {self.max_deals}")
                return
            
            item = self.extract_deal_from_json(deal_data, response)
            if item:
                self.deals_extracted += 1
                yield item
                
                # Extract related data
                yield from self.extract_deal_images_from_json(deal_data, item)
                yield from self.extract_deal_categories_from_json(deal_data, item, response)
                yield from self.extract_related_deals_from_json(deal_data, item)

    def extract_deal_from_json(self, deal_data, response):
        """Extract deal item from JSON-LD structured data"""
        import json
        try:
            item = DealnewsItem()
            
            # Extract basic information from JSON-LD
            json_url = deal_data.get('url', response.url)
            # Prefer stable id derived from absolute deal URL to maximize uniqueness
            if json_url:
                item['dealid'] = f"deal_{hash(json_url)}"
            else:
                item['dealid'] = deal_data.get('id', f"json_deal_{hash(str(deal_data))}")
            item['title'] = deal_data.get('name', '')
            item['detail'] = deal_data.get('description', '')  # Use 'detail' instead of 'description'
            item['price'] = deal_data.get('price', '')
            item['url'] = json_url
            
            # Extract category information
            category = deal_data.get('category', {})
            if isinstance(category, dict):
                item['category'] = category.get('name', '')
            
            # Extract availability information (store in detail field)
            availability = deal_data.get('availability', '')
            availability_starts = deal_data.get('availabilityStarts', '')
            availability_ends = deal_data.get('availabilityEnds', '')
            
            # Extract image information (store in images field)
            image = deal_data.get('image', {})
            if isinstance(image, dict):
                image_url = image.get('url', '')
            elif isinstance(image, str):
                image_url = image
            else:
                image_url = ''
            
            # Extract store information
            seller = deal_data.get('seller', {})
            if isinstance(seller, dict):
                item['store'] = seller.get('name', '')
            
            # Set default values for missing fields
            item['recid'] = ''
            item['deal'] = ''
            item['dealplus'] = ''
            item['promo'] = ''
            item['deallink'] = item['url']
            item['dealtext'] = item['detail']
            item['dealhover'] = ''
            item['staffpick'] = ''
            item['start_date'] = availability_starts
            item['raw_html'] = f'<div class="json-ld-deal">{json.dumps(deal_data)}</div>'
            
            # Store additional data in supported fields
            if image_url:
                item['images'] = [image_url]
            else:
                item['images'] = []
                
            # Store availability info in detail
            if availability or availability_starts or availability_ends:
                availability_info = f"Availability: {availability}"
                if availability_starts:
                    availability_info += f", Starts: {availability_starts}"
                if availability_ends:
                    availability_info += f", Ends: {availability_ends}"
                item['detail'] = f"{item['detail']}\n{availability_info}"
            
            # Extract filter variables
            filter_vars = self.extract_filter_variables_from_json(deal_data)
            item.update(filter_vars)
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error extracting deal from JSON: {e}")
            return None

    def extract_filter_variables_from_json(self, deal_data):
        """Extract filter variables from JSON-LD data"""
        filter_vars = {
            'offer_type': '',
            'condition': '',
            'events': '',
            'brand': '',
            'collection': '',
            'offer_status': '',
            'include_expired': False,
            'max_price': '',
            'popularity_rank': 0
        }
        
        # Extract offer type from category or description
        category = deal_data.get('category', {})
        if isinstance(category, dict):
            category_name = category.get('name', '').lower()
            if 'sale' in category_name or 'clearance' in category_name:
                filter_vars['offer_type'] = 'sale'
            elif 'coupon' in category_name or 'promo' in category_name:
                filter_vars['offer_type'] = 'coupon'
            elif 'rebate' in category_name:
                filter_vars['offer_type'] = 'rebate'
        
        # Extract brand from seller or category
        seller = deal_data.get('seller', {})
        if isinstance(seller, dict):
            seller_name = seller.get('name', '')
            if seller_name:
                filter_vars['brand'] = seller_name
        
        # Extract condition from description
        description = deal_data.get('description', '').lower()
        if 'new' in description:
            filter_vars['condition'] = 'new'
        elif 'used' in description or 'refurbished' in description:
            filter_vars['condition'] = 'used'
        elif 'open box' in description:
            filter_vars['condition'] = 'open_box'
        
        # Extract price for max_price
        price = deal_data.get('price', '')
        if price and '$' in price:
            try:
                price_num = float(price.replace('$', '').replace(',', ''))
                filter_vars['max_price'] = price_num
            except ValueError:
                pass
        
        return filter_vars

    def extract_deal_images_from_json(self, deal_data, item):
        """Extract deal images from JSON-LD data"""
        try:
            image = deal_data.get('image', {})
            if isinstance(image, dict) and image.get('url'):
                image_item = DealImageItem()
                image_item['dealid'] = item['dealid']
                image_item['imageurl'] = image['url']
                yield image_item
            elif isinstance(image, str) and image:
                image_item = DealImageItem()
                image_item['dealid'] = item['dealid']
                image_item['imageurl'] = image
                yield image_item
        except Exception as e:
            self.logger.error(f"Error extracting images from JSON: {e}")

    def extract_deal_categories_from_json(self, deal_data, item, response):
        """Extract deal categories from JSON-LD data"""
        try:
            category = deal_data.get('category', {})
            if isinstance(category, dict):
                if category.get('name'):
                    category_item = DealCategoryItem()
                    category_item['dealid'] = item['dealid']
                    category_item['category_name'] = category['name']
                    if category.get('url'):
                        category_item['category_url'] = category['url']
                    if category.get('@id'):
                        category_item['category_id'] = category['@id']
                    yield category_item
            elif isinstance(category, list):
                for cat in category:
                    if isinstance(cat, dict) and cat.get('name'):
                        category_item = DealCategoryItem()
                        category_item['dealid'] = item['dealid']
                        category_item['category_name'] = cat['name']
                        if cat.get('url'):
                            category_item['category_url'] = cat['url']
                        if cat.get('@id'):
                            category_item['category_id'] = cat['@id']
                        yield category_item
        except Exception as e:
            self.logger.error(f"Error extracting categories from JSON: {e}")

    def extract_related_deals_from_json(self, deal_data, item):
        """Extract related deals from JSON-LD data"""
        # JSON-LD doesn't typically contain related deals, so this is a placeholder
        # Return empty generator
        if False:
            yield

    def extract_deal_item(self, deal, response):
        """Extract main deal item with IMPROVED SELECTORS"""
        try:
            # Skip navigation/menu items that are not real deals
            deal_html = deal.get()
            skip_patterns = [
                'nav-menu-', 'menu-item', 'class="menu-item"',
                'About Us', 'Contact', 'Sign In', 'Register',
                'Back to Classic', 'Holiday Hours', 'Return Policy',
                'Price Match', 'Student Discount', 'Free Trial',
                'Promo Code', 'Coupon Code', 'Gift Card'
            ]
            
            # Skip if this looks like a navigation item
            for pattern in skip_patterns:
                if pattern in deal_html and 'deal-item' not in deal_html and 'data-deal-id' not in deal_html:
                    return None
            
            item = DealnewsItem()
            
            # Basic deal information - improved dealid generation (prefer absolute deal link)
            dealid = deal.css('::attr(data-deal-id)').get() or deal.css('::attr(id)').get()
            # We'll compute deallink first to derive a stable dealid if needed
            link = deal.css('a::attr(href)').get()
            if link:
                try:
                    # Make absolute
                    link = response.urljoin(link)
                except Exception:
                    pass
            # If no provided dealid, derive from absolute link; else fallback to content hash
            if not dealid:
                if link:
                    dealid = f"deal_{hash(link)}"
                else:
                    deal_text = deal.css('::text').get() or ''
                    dealid = f"deal_{hash((response.url + deal_text)[:200])}"

            item['dealid'] = dealid
            item['recid'] = deal.css('::attr(data-rec-id)').get() or ''
            item['url'] = response.url
            
            # IMPROVED Title extraction with UPDATED DealNews selectors
            title_selectors = [
                # DealNews specific (current site structure)
                '.deal-title::text',
                '.deal-name::text',
                '.deal-headline::text',
                '.deal-text::text',
                '.deal-description::text',
                '.deal-summary::text',
                # Current site selectors
                '.deal-title-text::text',
                '.deal-title-text::text',
                '.deal-content h3::text',
                '.deal-content h4::text',
                '.deal-content .title::text',
                # Click-out link text often carries the product/deal line
                'a[href*="lw/click.html"]::text',
                # Generic fallbacks
                '.title::text', 
                'h1::text',
                'h2::text',
                'h3::text',
                'h4::text',
                'h5::text',
                'h6::text',
                '.product-title::text',
                '.item-title::text',
                '.listing-title::text',
                '.post-title::text',
                '.entry-title::text',
                # Link text (more targeted)
                'a[href*="/deals/"]::text',
                'a[href*="/deal/"]::text',
                # Other possibilities
                '.name::text',
                '.headline::text',
                '.text::text',
                '.description::text',
                '.summary::text',
                '.content::text'
            ]
            
            for selector in title_selectors:
                title = deal.css(selector).get()
                if title and title.strip() and len(title.strip()) > 5:
                    item['title'] = title.strip()
                    break
            else:
                # Fallbacks: aria-label/title attributes or nearby snippet text
                attr_title = deal.css('[aria-label]::attr(aria-label), [title]::attr(title)').get()
                para = deal.css('p::text').get()
                item['title'] = (attr_title or para or 'No title found').strip()
            
            # IMPROVED Price extraction with UPDATED selectors
            price_selectors = [
                # DealNews specific (current site)
                '.deal-price::text',
                '.price::text',
                '.sale-price::text',
                '.current-price::text',
                '.deal-amount::text',
                '.deal-cost::text',
                # Current site structure
                '.price-amount::text',
                '.price-value::text',
                '.price-text::text',
                '.price-current::text',
                '.deal-price-value::text',
                # With spans (current structure)
                'span[class*="price"]::text',
                'span[class*="cost"]::text',
                'span[class*="amount"]::text',
                '.price span::text',
                '.deal-price span::text',
                # With divs (current structure)
                'div[class*="price"]::text',
                'div[class*="cost"]::text',
                'div[class*="amount"]::text',
                '.price div::text',
                # Generic fallbacks
                '.cost::text',
                '.amount::text',
                '.value::text',
                # Look for price patterns
                'span:contains("$")::text',
                'div:contains("$")::text',
                # Very generic
                '*::text'  # Last resort - scan all text for price patterns
            ]
            
            for selector in price_selectors:
                price = deal.css(selector).get()
                if price and ('$' in price or 'USD' in price or 'price' in price.lower()):
                    item['price'] = price.strip()
                    break
            else:
                item['price'] = ''
            
            # IMPROVED Store extraction
            store_selectors = [
                # DealNews specific
                '.store::text',
                '.merchant::text',
                '.retailer::text',
                '.vendor::text',
                '.deal-store::text',
                '.deal-merchant::text',
                # Generic
                '.store-name::text',
                '.merchant-name::text',
                '.retailer-name::text',
                '.vendor-name::text',
                # With spans
                'span[class*="store"]::text',
                'span[class*="merchant"]::text',
                'span[class*="retailer"]::text',
                'span[class*="vendor"]::text'
            ]
            
            for selector in store_selectors:
                store = deal.css(selector).get()
                if store and store.strip():
                    item['store'] = store.strip()
                    break
            else:
                item['store'] = ''
            
            # Extract category from deal element
            category_selectors = [
                '.category::text',
                '.deal-category::text',
                '.breadcrumb::text',
                '.deal-breadcrumb::text',
                '.category-name::text',
                '.cat::text',
                '.section::text',
                '.department::text'
            ]
            
            url_category = self.extract_category_from_url(response.url)
            category_value = ''
            for selector in category_selectors:
                    category = deal.css(selector).get()
                    if category and category.strip():
                        category_value = category.strip()
                        break
            if not category_value and url_category:
                category_value = url_category
            item['category'] = category_value

            # Extract categories from page-level breadcrumbs and tags
            page_categories = []
            # Extract from page breadcrumbs
            page_breadcrumbs = response.css('.breadcrumb a, .breadcrumbs a, [class*="breadcrumb"] a')
            for breadcrumb in page_breadcrumbs:
                cat_name = breadcrumb.css('::text').get()
                cat_url = breadcrumb.css('::attr(href)').get()
                if cat_name and cat_name.strip():
                    page_categories.append({
                        'category_name': cat_name.strip(),
                        'category_url': response.urljoin(cat_url) if cat_url else '',
                        'category_id': re.search(r'/c(\d+)/', cat_url).group(1) if cat_url and re.search(r'/c(\d+)/', cat_url) else ''
                    })
            
            # Extract from page tags/filters
            page_tags = response.css('.tag a, .filter a, [class*="tag"] a, [class*="filter"] a')
            for tag in page_tags:
                tag_name = tag.css('::text').get()
                tag_url = tag.css('::attr(href)').get()
                if tag_name and tag_name.strip():
                    page_categories.append({
                        'category_name': tag_name.strip(),
                        'category_title': tag_name.strip(),
                        'category_url': response.urljoin(tag_url) if tag_url else ''
                    })
            
            # Store categories for pipeline
            if page_categories:
                item['categories'] = page_categories
            elif item['category']:
                item['categories'] = [{'category_name': item['category']}]
            else:
                item['categories'] = []
            
            # Deal text and other fields
            item['deal'] = deal.css('.deal-text::text').get() or deal.css('.deal-description::text').get() or ''
            item['dealplus'] = deal.css('.deal-plus::text').get() or ''
            item['promo'] = deal.css('.promo::text').get() or deal.css('.promotion::text').get() or ''
            # Use the absolute deal link if available
            item['deallink'] = link or ''
            item['dealtext'] = deal.css('.deal-description::text').get() or deal.css('.deal-summary::text').get() or ''
            item['dealhover'] = deal.css('::attr(title)').get() or ''
            item['published'] = deal.css('.published::text').get() or deal.css('.date::text').get() or ''
            item['popularity'] = deal.css('.popularity::text').get() or deal.css('.rating::text').get() or ''
            item['staffpick'] = deal.css('.staff-pick::text').get() or deal.css('.featured::text').get() or ''
            item['detail'] = deal.css('.deal-detail::text').get() or deal.css('.details::text').get() or ''
            item['raw_html'] = deal.get()
            
            # Extract filter variables from deal content
            self.extract_filter_variables(item, deal, response)
            
            # Populate images and related deals on main item for pipeline usage
            try:
                item['images'] = [u for u in deal.css('img::attr(src)').getall() if u]
            except Exception:
                item['images'] = []
            try:
                item['related_deals'] = deal.css('.related-deals a::attr(href), .related a::attr(href), .similar a::attr(href)').getall()
            except Exception:
                item['related_deals'] = []
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error extracting deal item: {e}")
            return None

    def extract_category_from_url(self, url):
        """Extract category from URL"""
        if not url:
            return ''
        
        # Extract category from URL patterns
        if '/cat/' in url:
            parts = url.split('/cat/')
            if len(parts) > 1:
                category_part = parts[1].split('/')[0]
                return category_part.replace('-', ' ').title()
        elif '/c' in url:
            # Extract from /c123/Category/ pattern
            parts = url.split('/c')
            if len(parts) > 1:
                category_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else ''
                return category_part.replace('-', ' ').title()
        
        return ''
    
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

    def extract_deal_images(self, deal, item):
        """Extract deal images"""
        images = deal.css('img::attr(src)').getall()
        for img_url in images:
            if img_url:
                image_item = DealImageItem()
                image_item['dealid'] = item['dealid']
                image_item['imageurl'] = img_url
                yield image_item

    def extract_deal_categories(self, deal, item, response):
        """Extract deal categories from breadcrumbs, tags, and links"""
        # Extract from breadcrumbs (e.g., "All Deals > Automotive > Amazon")
        breadcrumbs = deal.css('.breadcrumb a, .breadcrumbs a, [class*="breadcrumb"] a')
        for breadcrumb in breadcrumbs:
            category_name = breadcrumb.css('::text').get()
            category_url = breadcrumb.css('::attr(href)').get()
            if category_name and category_name.strip():
                category_item = DealCategoryItem()
                category_item['dealid'] = item['dealid']
                category_item['category_name'] = category_name.strip()
                if category_url:
                    category_url = response.urljoin(category_url)
                    category_item['category_url'] = category_url
                    # Extract category ID from URL if present (e.g., /c142/Electronics/)
                    match = re.search(r'/c(\d+)/', category_url)
                    if match:
                        category_item['category_id'] = match.group(1)
                yield category_item
        
        # Extract from tags/filters (e.g., "Amazon Prime Day", "Staff Pick", "Popularity: 5/5")
        tags = deal.css('.tag a, .filter a, [class*="tag"] a, [class*="filter"] a, .label a')
        for tag in tags:
            tag_name = tag.css('::text').get()
            tag_url = tag.css('::attr(href)').get()
            if tag_name and tag_name.strip():
                category_item = DealCategoryItem()
                category_item['dealid'] = item['dealid']
                category_item['category_name'] = tag_name.strip()
                category_item['category_title'] = tag_name.strip()
                if tag_url:
                    tag_url = response.urljoin(tag_url)
                    category_item['category_url'] = tag_url
                yield category_item
        
        # Also extract from text-based categories/tags
        category_texts = deal.css('.category::text, .tag::text, .label::text').getall()
        for text in category_texts:
            text = text.strip()
            if text and len(text) > 1:
                category_item = DealCategoryItem()
                category_item['dealid'] = item['dealid']
                category_item['category_name'] = text
                yield category_item

    def extract_related_deals(self, deal, item):
        """Extract related deals"""
        related_links = deal.css('.related-deals a::attr(href), .related a::attr(href), .similar a::attr(href)').getall()
        for link in related_links:
            if link:
                related_item = RelatedDealItem()
                related_item['dealid'] = item['dealid']
                related_item['relatedurl'] = link
                yield related_item

    def handle_pagination(self, response):
        """Handle pagination and infinite scroll for DealNews - OPTIMIZED for 100k+ deals"""
        # Stop paginating on non-200 responses
        if response.status != 200:
            self.logger.info(f"Skipping pagination due to status {response.status} for {response.url}")
            return
        if self.deals_extracted >= self.max_deals:
            return
        
        self.logger.info(f"Handling pagination for: {response.url}")
        
        # Extract current start parameter
        current_start = 0
        if 'start=' in response.url:
            match = re.search(r'start=(\d+)', response.url)
            if match:
                current_start = int(match.group(1))
        
        # Generate ONLY the immediate next page to avoid flooding requests
        next_start = current_start + 20
        if next_start > current_start:
            # Build next page URL
            if '?' in response.url:
                if 'start=' in response.url:
                    next_url = re.sub(r'start=\d+', f'start={next_start}', response.url)
                else:
                    next_url = f"{response.url}&start={next_start}"
            else:
                next_url = f"{response.url}?start={next_start}"
            
            if self.is_valid_dealnews_url(next_url):
                yield response.follow(next_url, self.parse, errback=self.errback_http, dont_filter=False)
                return  # Do not expand further via HTML links in the same response
        
        # Also look for pagination links in HTML
        pagination_patterns = [
            'a[href*="?start="]',
            'a[href*="&start="]',
            '.pagination a::attr(href)',
            '.pager a::attr(href)',
            '.page-numbers a::attr(href)',
            'a[class*="next"]::attr(href)',
            'a[class*="page"]::attr(href)',
        ]
        
        for pattern in pagination_patterns:
            links = response.css(pattern).getall()
            for link in links[:50]:  # Limit to avoid too many requests
                if link and 'start=' in link and self.is_valid_dealnews_url(link):
                    yield response.follow(link, self.parse, errback=self.errback_http, dont_filter=False)
        
        # Look for "Load More" or "Show More" buttons - avoid generic selectors
        load_more_selectors = [
            'button[data-url*="start="]',  # DealNews specific pattern
            '.load-more[href*="start="]',
            '.show-more[href*="start="]',
            '.pagination-load-more[href*="start="]',
            # Be more specific to avoid 404s
            'a[href*="start="]:not([href*="javascript"]):not([href*="mailto"])'
        ]
        
        load_more_found = 0
        for selector in load_more_selectors:
            load_more_buttons = response.css(selector)
            for button in load_more_buttons[:50]:  # Limit load more buttons
                data_url = button.css('::attr(data-url)').get() or button.css('::attr(href)').get()
                if data_url and 'start=' in data_url:
                    self.logger.info(f"Found load more button: {data_url}")
                    yield response.follow(data_url, self.parse, errback=self.errback_http)
                    load_more_found += 1
        
        # Also look for traditional pagination links - but only with start= pattern
        pagination_links = response.css('.pagination a[href*="start="]::attr(href), .pager a[href*="start="]::attr(href)').getall()
        valid_pagination_links = 0
        for link in pagination_links[:50]:  # Limit pagination links
            if link and 'start=' in link and not any(x in link for x in ['page=', 'offset=', 'p=']):
                self.logger.info(f"Found pagination link: {link}")
                yield response.follow(link, self.parse, errback=self.errback_http)
                valid_pagination_links += 1
        
        # Look for "Load More" or infinite scroll endpoints - only with start= pattern
        load_more_data = response.css('button[data-url*="start="]::attr(data-url)').getall()
        valid_load_more_data = 0
        for data_url in load_more_data[:3]:  # Much more reasonable limit
            if data_url and 'start=' in data_url:
                self.logger.info(f"Found load more data: {data_url}")
                yield response.follow(data_url, self.parse, errback=self.errback_http)
                valid_load_more_data += 1
        
        self.logger.info(f"Pagination summary - AJAX pagination: {pagination_found}, Load more buttons: {load_more_found}, Pagination links: {valid_pagination_links}, Load more data: {valid_load_more_data}")

    def extract_filter_variables(self, item, deal, response):
        """Extract filter variables from deal content and URL"""
        # Extract offer type from deal text
        deal_text = (item.get('deal', '') + ' ' + item.get('dealplus', '') + ' ' + item.get('detail', '')).lower()
        
        # Offer type extraction
        if any(word in deal_text for word in ['free shipping', 'free delivery']):
            item['offer_type'] = 'Free Shipping'
        elif any(word in deal_text for word in ['coupon', 'discount code', 'promo code']):
            item['offer_type'] = 'Coupon'
        elif any(word in deal_text for word in ['rebate', 'cashback', 'cash back']):
            item['offer_type'] = 'Rebate'
        elif any(word in deal_text for word in ['clearance', 'sale', 'off']):
            item['offer_type'] = 'Sale'
        else:
            item['offer_type'] = ''
        
        # Condition extraction
        if any(word in deal_text for word in ['new', 'brand new']):
            item['condition'] = 'New'
        elif any(word in deal_text for word in ['used', 'pre-owned', 'second hand']):
            item['condition'] = 'Used'
        elif any(word in deal_text for word in ['refurbished', 'refurb']):
            item['condition'] = 'Refurbished'
        else:
            item['condition'] = 'New'  # Default to new
        
        # Events extraction
        if any(word in deal_text for word in ['black friday', 'cyber monday', 'prime day']):
            item['events'] = 'Black Friday'
        elif any(word in deal_text for word in ['christmas', 'holiday', 'xmas']):
            item['events'] = 'Holiday'
        elif any(word in deal_text for word in ['back to school', 'school']):
            item['events'] = 'Back to School'
        else:
            item['events'] = ''
        
        # Offer status extraction
        if any(word in deal_text for word in ['limited time', 'expires', 'ending soon']):
            item['offer_status'] = 'Limited'
        elif any(word in deal_text for word in ['expired', 'ended', 'no longer available']):
            item['offer_status'] = 'Expired'
        else:
            item['offer_status'] = 'Active'  # Default to active
        
        # Include expired (default to No)
        item['include_expired'] = 'No'
        
        # Brand extraction from title
        title = item.get('title', '').lower()
        brands = ['apple', 'samsung', 'nike', 'adidas', 'sony', 'microsoft', 'google', 'amazon', 'walmart', 'target', 'best buy']
        for brand in brands:
            if brand in title:
                item['brand'] = brand.title()
                break
        else:
            item['brand'] = ''
        
        # Collection extraction from URL
        item['collection'] = self.extract_collection_from_url(response.url)
        
        # Start date and max price (extract from URL params or set defaults)
        item['start_date'] = ''
        item['max_price'] = ''
        item['popularity_rank'] = ''

    def is_valid_dealnews_url(self, url):
        """Check if URL is a valid DealNews URL"""
        if not url:
            return False
        
        # Convert relative URLs to absolute
        if url.startswith('/'):
            url = f"https://www.dealnews.com{url}"
        
        # Check if it's a DealNews URL
        if 'dealnews.com' not in url:
            return False
        
        # Skip certain patterns
        skip_patterns = [
            'javascript:',
            'mailto:',
            '#',
            'tel:',
            'ftp:',
            '.pdf',
            '.jpg',
            '.png',
            '.gif',
            '.css',
            '.js'
        ]
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True

    def closed(self, reason):
        """Called when spider closes"""
        elapsed_time = time.time() - self.start_time
        rate = self.deals_extracted / elapsed_time if elapsed_time > 0 else 0
        
        self.logger.info(f"Spider closed. Reason: {reason}")
        self.logger.info(f"Final stats: {self.deals_extracted} deals extracted in {elapsed_time:.1f} seconds")
        self.logger.info(f"Average rate: {rate:.1f} deals per second")
