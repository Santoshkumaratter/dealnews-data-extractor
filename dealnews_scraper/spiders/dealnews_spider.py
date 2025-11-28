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
        self.detail_pages_visited = 0
        self.max_detail_pages = 5000  # Increased limit to get more related deals (was 1000)
    
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
                yield from self.extract_related_deals(deal, item, response)
                
                # Visit detail page for related deals (increased frequency to get more related deals)
                deallink = item.get('deallink') or item.get('url', '')
                if deallink and self.detail_pages_visited < self.max_detail_pages and '/deals/' in deallink:
                    # Visit detail page to get related deals (visit every 5th deal for better coverage)
                    if self.deals_extracted % 5 == 0:  # Visit every 5th deal's detail page (was 10th)
                        yield scrapy.Request(
                            url=deallink,
                            callback=self.parse_deal_detail,
                            meta={'dealid': item['dealid'], 'item': item},
                            errback=self.errback_http,
                            dont_filter=True
                        )
                        self.detail_pages_visited += 1
        
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
            
            # Extract deal text from title/description (look for "Up to X% off" patterns)
            deal_text = ''
            title_text = item.get('title', '')
            detail_text = item.get('detail', '')
            combined_text = f"{title_text} {detail_text}".lower()
            
            # Look for discount patterns in title or description
            import re
            # Pattern 1: Standard discount patterns
            deal_patterns = [
                r'Up to \d+% off',
                r'Up to \d+%',
                r'Save \d+%',
                r'\d+% off',
                r'\$\d+ off',
                r'\$\d+ gift card',
                r'\d+-\w+ deals?',  # e.g., "1-cent deals"
                r'\$\d+/\w+',  # e.g., "$5/item"
            ]
            
            # Try title first
            for pattern in deal_patterns:
                deal_match = re.search(pattern, title_text, re.IGNORECASE)
                if deal_match:
                    deal_text = deal_match.group(0)
                    break
            
            # If not found in title, try description
            if not deal_text:
                for pattern in deal_patterns:
                    deal_match = re.search(pattern, detail_text, re.IGNORECASE)
                    if deal_match:
                        deal_text = deal_match.group(0)
                        break
            
            # Special case: "1-cent" deals
            if not deal_text and ('1-cent' in title_text.lower() or '1 cent' in title_text.lower()):
                deal_text = '1-cent deals'
            
            # Special case: Gift card deals
            if not deal_text and ('gift card' in combined_text):
                gift_match = re.search(r'\$?\d+ gift card', title_text, re.IGNORECASE)
                if gift_match:
                    deal_text = gift_match.group(0)
            
            # Extract dealplus (free shipping, Prime, etc.)
            dealplus_text = ''
            # Check for free shipping patterns
            if 'free shipping' in combined_text:
                if 'prime' in combined_text or 'w/ prime' in combined_text or 'w/Prime' in combined_text:
                    dealplus_text = 'free shipping w/ Prime'
                elif 'w/ $' in combined_text or 'w/$' in combined_text:
                    # Extract minimum amount (e.g., "free shipping w/ $25")
                    amount_match = re.search(r'free shipping\s+w/?\s*\$?(\d+)', combined_text, re.IGNORECASE)
                    if amount_match:
                        dealplus_text = f"free shipping w/ ${amount_match.group(1)}"
                    else:
                        dealplus_text = 'free shipping'
                else:
                    dealplus_text = 'free shipping'
            elif ('prime' in combined_text and ('w/' in combined_text or 'w/ ' in combined_text)):
                dealplus_text = 'free shipping w/ Prime'
            elif 'w/ $' in combined_text or 'w/$' in combined_text:
                # Check for other shipping conditions
                amount_match = re.search(r'w/?\s*\$?(\d+)', combined_text, re.IGNORECASE)
                if amount_match:
                    dealplus_text = f"free shipping w/ ${amount_match.group(1)}"
            
            # Extract published timestamp from availabilityStarts
            published_text = ''
            if availability_starts:
                # Format: "2025-11-28T04:51:31-05:00" -> try to make it readable
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(availability_starts.replace('Z', '+00:00'))
                    # Calculate time ago
                    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
                    diff = now - dt
                    hours = int(diff.total_seconds() / 3600)
                    if hours < 1:
                        published_text = f"{item.get('store', '')} · just now"
                    elif hours < 24:
                        published_text = f"{item.get('store', '')} · {hours} hr{'s' if hours > 1 else ''} ago"
                    else:
                        days = hours // 24
                        published_text = f"{item.get('store', '')} · {days} day{'s' if days > 1 else ''} ago"
                except:
                    published_text = availability_starts
            
            # Extract popularity (check title, description, and JSON-LD name field)
            popularity_text = ''
            # Check in title first (sometimes it's in the title)
            if '/5' in title_text or 'popularity' in title_text.lower():
                pop_match = re.search(r'(Popularity:?\s*\d+/\d+|\d+/\d+)', title_text, re.IGNORECASE)
                if pop_match:
                    popularity_text = pop_match.group(1)
            
            # Check in description
            if not popularity_text and ('/5' in detail_text or 'popularity' in detail_text.lower()):
                pop_match = re.search(r'(Popularity:?\s*\d+/\d+|\d+/\d+)', detail_text, re.IGNORECASE)
                if pop_match:
                    popularity_text = pop_match.group(1)
            
            # Also check JSON-LD name field (sometimes popularity is in the name)
            json_name = deal_data.get('name', '')
            if not popularity_text and json_name and ('/5' in json_name or 'popularity' in json_name.lower()):
                pop_match = re.search(r'(Popularity:?\s*\d+/\d+|\d+/\d+)', json_name, re.IGNORECASE)
                if pop_match:
                    popularity_text = pop_match.group(1)
            
            # Extract staffpick (check description for "Staff Pick" or similar)
            staffpick_text = ''
            if 'staff pick' in combined_text or 'bought one' in combined_text:
                staffpick_text = 'Staff Pick'
            
            # Set fields
            item['recid'] = ''
            item['deal'] = deal_text
            item['dealplus'] = dealplus_text
            item['promo'] = ''
            item['deallink'] = item['url']
            item['dealtext'] = item['detail'][:200] if item['detail'] else ''  # First 200 chars of detail
            item['dealhover'] = item['title']  # Use title as hover text
            item['staffpick'] = staffpick_text
            item['published'] = published_text
            item['popularity'] = popularity_text
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
            # Try data-content-id first (new DealNews structure)
            dealid = deal.css('::attr(data-content-id)').get() or deal.css('::attr(data-deal-id)').get() or deal.css('::attr(id)').get()
            # Get actual deal URL from data-offer-url (new structure) or href
            link = deal.css('::attr(data-offer-url)').get() or deal.css('a::attr(href)').get()
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
            # Clean up dealid - remove "auto-id-" prefix if present
            if dealid and dealid.startswith('auto-id-'):
                # Use content-id or hash of link instead
                content_id = deal.css('::attr(data-content-id)').get()
                if content_id:
                    dealid = f"deal_{content_id}"
                elif link:
                    dealid = f"deal_{hash(link)}"

            item['dealid'] = dealid
            item['recid'] = deal.css('::attr(data-rec-id)').get() or ''
            item['url'] = response.url
            
            # IMPROVED Title extraction with UPDATED DealNews selectors
            title_selectors = [
                # New DealNews structure (priority)
                '.title-link::text',  # Actual deal title link
                '.title a::text',  # Title with link
                '.pitch .title::text',  # Title in pitch section
                '.pitch .title-link::text',  # Title link in pitch
                # DealNews specific (current site structure)
                '.deal-title::text',
                '.deal-name::text',
                '.deal-headline::text',
                '.deal-text::text',
                '.deal-description::text',
                '.deal-summary::text',
                # Current site selectors
                '.deal-title-text::text',
                '.deal-content h3::text',
                '.deal-content h4::text',
                '.deal-content .title::text',
                # Generic fallbacks (avoid .title::text as it matches "More Options" button)
                'h1::text',
                'h2::text',
                'h3::text',
                'h4::text',
                '.product-title::text',
                '.item-title::text',
                '.listing-title::text',
                '.post-title::text',
                '.entry-title::text',
                # Link text (more targeted)
                'a[href*="/deals/"]::text',
                'a[href*="/deal/"]::text',
                'a[href*="/products/"]::text',
                # Other possibilities
                '.name::text',
                '.headline::text',
                '.description::text',
                '.summary::text'
            ]
            
            for selector in title_selectors:
                title = deal.css(selector).get()
                if title and title.strip() and len(title.strip()) > 5:
                    # Skip common non-title text
                    if title.strip().lower() not in ['more options', 'more', 'less', 'buy now', 'shop now', 'read more']:
                        item['title'] = title.strip()
                        break
            else:
                # Fallbacks: aria-label/title attributes or nearby snippet text
                attr_title = deal.css('[aria-label*="details"], [aria-label*="Read More"]::attr(aria-label)').get()
                if not attr_title:
                    attr_title = deal.css('[title]::attr(title)').get()
                para = deal.css('.snippet.summary p::text, .summary p::text').get()
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
            
            # IMPROVED Store extraction - try JSON-LD first, then data attributes, then CSS
            store = ''
            # Try to extract from JSON-LD script tag
            json_ld_script = deal.css('script[type="application/ld+json"]::text').get()
            if json_ld_script:
                try:
                    import json
                    json_data = json.loads(json_ld_script)
                    # Check for seller in offers
                    if 'offers' in json_data and isinstance(json_data['offers'], list) and len(json_data['offers']) > 0:
                        seller = json_data['offers'][0].get('seller', {})
                        if isinstance(seller, dict):
                            store = seller.get('name', '')
                    # Also check direct seller
                    if not store and 'seller' in json_data:
                        seller = json_data['seller']
                        if isinstance(seller, dict):
                            store = seller.get('name', '')
                except:
                    pass
            
            # Try data-store attribute (store ID) - we can look it up or use key-attribute
            if not store:
                # Extract from key-attribute line (e.g., "Best Buy · 4 hrs ago")
                store_text = deal.css('.key-attribute::text').get()
                if store_text:
                    # Extract store name before "·" or "|"
                    store = store_text.split('·')[0].split('|')[0].strip()
            
            # Fallback to CSS selectors
            if not store:
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
                        store = store.strip()
                        break
                
                item['store'] = store or ''
            
            # Extract category from deal element - try JSON-LD first, then data attributes, then CSS
            category_value = ''
            # Try to extract from JSON-LD script tag
            json_ld_script = deal.css('script[type="application/ld+json"]::text').get()
            if json_ld_script:
                try:
                    import json
                    json_data = json.loads(json_ld_script)
                    # Check for category in offers
                    if 'offers' in json_data and isinstance(json_data['offers'], list) and len(json_data['offers']) > 0:
                        category_obj = json_data['offers'][0].get('category', {})
                        if isinstance(category_obj, dict):
                            category_value = category_obj.get('name', '')
                except:
                    pass
            
            # Fallback to URL category
            url_category = self.extract_category_from_url(response.url)
            if not category_value and url_category:
                category_value = url_category
            
            # Fallback to CSS selectors
            if not category_value:
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
                
                for selector in category_selectors:
                    category = deal.css(selector).get()
                    if category and category.strip():
                        category_value = category.strip()
                        break
            
            item['category'] = category_value

            # Extract ONLY deal-specific categories (within deal container, NOT page-level)
            # This prevents duplicate static data from being saved for every deal
            deal_categories = []
            
            # Extract category from URL if available (dynamic per page)
            if url_category:
                deal_categories.append({
                    'category_name': url_category,
                    'category_url': response.url,
                    'category_id': re.search(r'/c(\d+)/', response.url).group(1) if re.search(r'/c(\d+)/', response.url) else ''
                })
            
            # Extract deal-specific category from deal container only
            if category_value:
                deal_categories.append({
                    'category_name': category_value
                })
            
            # Store categories for pipeline (only deal-specific, no page-level static data)
            # Always include main category if available
            if not deal_categories and category_value:
                deal_categories.append({
                    'category_name': category_value
                })
            item['categories'] = deal_categories if deal_categories else []
            
            # IMPROVED Deal text extraction - look for patterns like "Up to 80% off"
            deal_text = ''
            # First, try to find text containing discount patterns
            all_text = deal.css('::text').getall()
            import re
            for text in all_text:
                if text and text.strip():
                    text_lower = text.lower().strip()
                    # Look for discount patterns: "Up to X% off", "X% off", "Save X%", etc.
                    # Use regex for more precise matching
                    deal_patterns = [
                        r'Up to \d+% off',
                        r'Up to \d+%',
                        r'Save \d+%',
                        r'\d+% off',
                        r'\$\d+ off',
                        r'\d+-\w+ deals?',  # e.g., "1-cent deals"
                    ]
                    for pattern in deal_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            deal_text = match.group(0).strip()
                            # Prefer shorter, more specific deal text
                            if len(deal_text) < 50:
                                break
                    if deal_text:
                        break
            
            # Fallback to CSS selectors
            if not deal_text:
                deal_text_selectors = [
                    '.deal-text::text',
                    '.deal-description::text',
                    '.discount::text',
                    '.savings::text',
                    '[class*="deal"]::text',
                    '[class*="discount"]::text',
                    '.promo-text::text',
                    '.offer-text::text'
                ]
                for selector in deal_text_selectors:
                    deal_text = deal.css(selector).get()
                    if deal_text and deal_text.strip():
                        deal_text = deal_text.strip()
                        # Validate it looks like a deal text
                        if '%' in deal_text or 'off' in deal_text.lower() or 'save' in deal_text.lower():
                            break
            item['deal'] = deal_text or ''
            
            # IMPROVED Dealplus extraction - look for "free shipping", "w/ Prime", etc.
            dealplus_text = ''
            import re
            # Check for free shipping patterns with amounts
            for text in all_text:
                if text and text.strip():
                    text_lower = text.lower().strip()
                    # Pattern 1: "free shipping w/ $25" or "free shipping w/$25"
                    if 'free shipping' in text_lower:
                        amount_match = re.search(r'free shipping\s+w/?\s*\$?(\d+)', text_lower)
                        if amount_match:
                            dealplus_text = f"free shipping w/ ${amount_match.group(1)}"
                            break
                        elif 'prime' in text_lower or 'w/ prime' in text_lower:
                            dealplus_text = 'free shipping w/ Prime'
                            break
                        else:
                            dealplus_text = 'free shipping'
                            break
                    # Pattern 2: "w/ Prime" or "w/Prime" (separate if, not elif)
                    if not dealplus_text and 'prime' in text_lower and ('w/' in text_lower or 'w/ ' in text_lower):
                        dealplus_text = 'free shipping w/ Prime'
                        break
            
            # Fallback to CSS selectors
            if not dealplus_text:
                dealplus_selectors = [
                    '.deal-plus::text',
                    '.shipping::text',
                    '.bonus::text',
                    '[class*="plus"]::text',
                    '[class*="shipping"]::text'
                ]
                for selector in dealplus_selectors:
                    dealplus_text = deal.css(selector).get()
                    if dealplus_text and dealplus_text.strip():
                        dealplus_text = dealplus_text.strip()
                        # Clean up the text
                        if 'free shipping' in dealplus_text.lower():
                            if 'prime' in dealplus_text.lower():
                                dealplus_text = 'free shipping w/ Prime'
                            else:
                                dealplus_text = 'free shipping'
                        break
            item['dealplus'] = dealplus_text or ''
            
            item['promo'] = deal.css('.promo::text').get() or deal.css('.promotion::text').get() or ''
            
            # Use the absolute deal link if available (prefer actual deal URL over click.html redirect)
            # If link is a click.html redirect, try to get the actual deal URL from JSON-LD or data-offer-url
            if link and 'lw/click.html' in link:
                # Try to get actual deal URL from JSON-LD
                json_ld_script = deal.css('script[type="application/ld+json"]::text').get()
                if json_ld_script:
                    try:
                        import json
                        json_data = json.loads(json_ld_script)
                        # Check for url in offers
                        if 'offers' in json_data and isinstance(json_data['offers'], list) and len(json_data['offers']) > 0:
                            offer_url = json_data['offers'][0].get('url', '')
                            if offer_url and '/deals/' in offer_url or '/products/' in offer_url:
                                link = offer_url
                        # Also check direct url
                        if 'lw/click.html' in link and 'url' in json_data:
                            if '/deals/' in json_data['url'] or '/products/' in json_data['url']:
                                link = json_data['url']
                    except:
                        pass
            item['deallink'] = link or ''
            
            # IMPROVED Dealtext and dealhover - extract from "Shop Now" button/link using XPath
            shop_now_link = deal.xpath('.//a[contains(text(), "Shop Now") or contains(text(), "Buy Now")]/@href').get()
            shop_now_text = deal.xpath('.//a[contains(text(), "Shop Now") or contains(text(), "Buy Now")]/text()').get()
            shop_now_title = deal.xpath('.//a[contains(text(), "Shop Now") or contains(text(), "Buy Now")]/@title').get()
            
            if shop_now_link:
                item['deallink'] = response.urljoin(shop_now_link) if shop_now_link else item['deallink']
            item['dealtext'] = shop_now_text or deal.css('.deal-description::text').get() or deal.css('.deal-summary::text').get() or ''
            item['dealhover'] = shop_now_title or deal.css('::attr(title)').get() or ''
            
            # IMPROVED Published timestamp - look for "Published X hr ago", "X hrs ago", etc.
            published_text = ''
            for text in all_text:
                if text and ('ago' in text.lower() or ('published' in text.lower() and 'hr' in text.lower())):
                    published_text = text.strip()
                    break
            
            # Fallback to CSS selectors
            if not published_text:
                published_selectors = [
                    '.published::text',
                    '.date::text',
                    '.timestamp::text',
                    '.time::text',
                    '[class*="published"]::text',
                    '[class*="date"]::text'
                ]
                for selector in published_selectors:
                    published_text = deal.css(selector).get()
                    if published_text and published_text.strip():
                        published_text = published_text.strip()
                        break
            item['published'] = published_text or ''
            
            # IMPROVED Popularity - look for "5/5", "Popularity: 5/5", etc.
            popularity_text = ''
            # First check all text for popularity patterns
            for text in all_text:
                if text and text.strip():
                    # Look for patterns like "5/5", "Popularity: 5/5", "Rating: 4/5"
                    pop_match = re.search(r'(Popularity:?\s*)?(\d+/\d+)', text, re.IGNORECASE)
                    if pop_match:
                        popularity_text = pop_match.group(2)  # Just the "5/5" part
                        break
            
            # Fallback to CSS selectors
            if not popularity_text:
                popularity_selectors = [
                    '.popularity::text',
                    '.rating::text',
                    '.score::text',
                    '[class*="popularity"]::text',
                    '[class*="rating"]::text',
                    '[data-popularity]::attr(data-popularity)',
                    '[data-rating]::attr(data-rating)'
                ]
                for selector in popularity_selectors:
                    pop_val = deal.css(selector).get()
                    if pop_val and pop_val.strip():
                        # Extract just the rating part (e.g., "5/5" from "Popularity: 5/5")
                        pop_match = re.search(r'(\d+/\d+)', pop_val)
                        if pop_match:
                            popularity_text = pop_match.group(1)
                        else:
                            popularity_text = pop_val.strip()
                        break
            item['popularity'] = popularity_text or ''
            
            # IMPROVED Staffpick - look for "Staff Pick", "Deals so good we bought one", etc.
            staffpick_text = ''
            for text in all_text:
                if text and ('staff pick' in text.lower() or 'bought one' in text.lower()):
                    staffpick_text = text.strip()
                    break
            
            # Fallback to CSS selectors
            if not staffpick_text:
                staffpick_selectors = [
                    '.staff-pick::text',
                    '.featured::text',
                    '[class*="staff"]::text',
                    '[class*="pick"]::text'
                ]
                for selector in staffpick_selectors:
                    staffpick_text = deal.css(selector).get()
                    if staffpick_text and staffpick_text.strip():
                        staffpick_text = staffpick_text.strip()
                        break
            item['staffpick'] = staffpick_text or ''
            
            # IMPROVED Detail - full description text
            detail_text = deal.css('.deal-detail::text').get() or deal.css('.details::text').get() or deal.css('.description::text').get() or ''
            # Also try to get full paragraph text
            if not detail_text:
                detail_paragraphs = deal.css('p::text').getall()
                if detail_paragraphs:
                    detail_text = ' '.join([p.strip() for p in detail_paragraphs if p.strip()])
            item['detail'] = detail_text or ''
            item['raw_html'] = deal.get()
            
            # Extract filter variables from deal content
            self.extract_filter_variables(item, deal, response)
            
            # Populate images and related deals on main item for pipeline usage
            try:
                # Try multiple image selectors to find deal images
                images = (
                    deal.css('img::attr(src)').getall() or
                    deal.css('img::attr(data-src)').getall() or  # Lazy-loaded images
                    deal.css('img::attr(data-lazy-src)').getall() or
                    deal.css('[class*="image"] img::attr(src)').getall() or
                    deal.css('[class*="deal"] img::attr(src)').getall()
                )
                # Filter out empty and invalid images
                item['images'] = [u.strip() for u in images if u and u.strip() and not u.startswith('data:')]
                if item['images']:
                    self.logger.debug(f"Found {len(item['images'])} images for deal {dealid}")
            except Exception as e:
                self.logger.debug(f"Error extracting images: {e}")
                item['images'] = []
            # Extract related deals from deal container (if available on listing pages)
            # Note: Related deals are typically only on detail pages, not listing pages
            try:
                # Try specific selectors for related/similar deals (not all deal links)
                related_links = (
                    deal.css('.related-deals a::attr(href), .related a::attr(href), .similar a::attr(href)').getall() or
                    deal.css('[class*="related"] a::attr(href), [class*="similar"] a::attr(href)').getall() or
                    []
                )
                # Filter out the current deal's own link and make absolute URLs
                current_link = link or item.get('deallink', '') or ''
                filtered_links = []
                for rl in related_links:
                    if rl and rl.strip() and rl != current_link:
                        # Make absolute URL
                        try:
                            if not rl.startswith('http'):
                                rl = response.urljoin(rl)
                            if '/deals/' in rl or '/deal/' in rl:
                                filtered_links.append(rl)
                        except:
                            pass
                item['related_deals'] = filtered_links
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
        """Extract deal images with multiple selectors"""
        # Try multiple image selectors
        images = (
            deal.css('img::attr(src)').getall() or
            deal.css('img::attr(data-src)').getall() or  # Lazy-loaded images
            deal.css('img::attr(data-lazy-src)').getall() or
            deal.css('[class*="image"] img::attr(src)').getall() or
            deal.css('[class*="deal"] img::attr(src)').getall()
        )
        
        seen_images = set()
        for img_url in images:
            if img_url and img_url.strip() and not img_url.startswith('data:'):
                img_url = img_url.strip()
                if img_url not in seen_images:
                    seen_images.add(img_url)
                image_item = DealImageItem()
                image_item['dealid'] = item['dealid']
                image_item['imageurl'] = img_url
                yield image_item

    def extract_deal_categories(self, deal, item, response):
        """Extract ONLY deal-specific categories from within the deal container (NOT page-level)"""
        # Extract category from URL (dynamic per page, but unique per deal's page context)
        url_category = self.extract_category_from_url(response.url)
        if url_category:
            category_item = DealCategoryItem()
            category_item['dealid'] = item['dealid']
            category_item['category_name'] = url_category
            category_item['category_url'] = response.url
            # Extract category ID from URL if present (e.g., /c142/Electronics/)
            match = re.search(r'/c(\d+)/', response.url)
            if match:
                category_item['category_id'] = match.group(1)
            yield category_item
        
        # Extract deal-specific category from deal container only (scoped to this deal)
        deal_category = deal.css('.category::text, .deal-category::text, .category-name::text').get()
        if deal_category and deal_category.strip():
            deal_category = deal_category.strip()
            # Filter out invalid categories
            invalid_categories = ['sponsored', 'expired', 'active', 'inactive', 'new', 'used', 'refurbished']
            if deal_category.lower() not in invalid_categories:
                category_item = DealCategoryItem()
                category_item['dealid'] = item['dealid']
                category_item['category_name'] = deal_category
                yield category_item
        
        # Extract deal-specific tags/labels within deal container only
        # Use scoped selectors to avoid page-level elements
        deal_tags = deal.css('.tag::text, .label::text, [class*="deal-tag"]::text, [class*="deal-label"]::text').getall()
        seen_tags = set()
        # Invalid category names to filter out (not real categories)
        invalid_categories = [
            'sponsored', 'expired', 'active', 'inactive', 'new', 'used', 'refurbished',
            'deal', 'sale', 'offer', 'buy', 'shop', 'more', 'less', 'read more',
            'staff pick', 'popular', 'featured', 'hot', 'trending', 'best seller',
            'limited time', 'ending soon', 'expires', 'ended', 'no longer available'
        ]
        for tag_text in deal_tags:
            tag_text = tag_text.strip() if tag_text else ''
            # Skip generic/static tags and invalid category names
            if (tag_text and len(tag_text) > 1 and 
                tag_text.lower() not in invalid_categories and
                not tag_text.lower().startswith('popularity') and
                not tag_text.lower().startswith('published')):
                if tag_text not in seen_tags:
                    seen_tags.add(tag_text)
                category_item = DealCategoryItem()
                category_item['dealid'] = item['dealid']
                category_item['category_name'] = tag_text
                yield category_item

    def extract_related_deals(self, deal, item, response):
        """Extract related deals from deal container (dynamic, deal-specific only)"""
        # Extract related deals from within deal container only
        related_links = (
            deal.css('.related-deals a::attr(href), .related a::attr(href), .similar a::attr(href)').getall() or
            deal.css('[class*="related"] a::attr(href), [class*="similar"] a::attr(href)').getall() or
            []
        )
        
        # Also try to extract from deal's main item if available
        if item.get('related_deals'):
            related_links.extend(item.get('related_deals', []))
        
        # Filter out duplicates and invalid links
        seen_links = set()
        current_deallink = item.get('deallink', '') or item.get('url', '')
        
        for link in related_links:
            if not link or not link.strip():
                continue
            
            # Make absolute URL
            try:
                if not link.startswith('http'):
                    link = response.urljoin(link)
            except:
                pass
            
            # Skip if it's the same as current deal's link
            if link == current_deallink or link in seen_links:
                continue
            
            # Only process valid deal URLs
            if '/deals/' in link or '/deal/' in link or 'dealnews.com' in link:
                seen_links.add(link)
                related_item = RelatedDealItem()
                related_item['dealid'] = item['dealid']
                related_item['relatedurl'] = link
                yield related_item

    def parse_deal_detail(self, response):
        """Parse individual deal detail page to extract related deals"""
        dealid = response.meta.get('dealid', '')
        item = response.meta.get('item', {})
        
        if not dealid:
            self.logger.warning(f"No dealid found in detail page response: {response.url}")
            return
        
        self.logger.info(f"🔍 Parsing detail page for deal {dealid}: {response.url}")
        
        # Extract related deals from detail page (more likely to have them)
        # Try multiple strategies to find related deals
        related_selectors = [
            '.related-deals a::attr(href)',
            '.related a::attr(href)',
            '.similar-deals a::attr(href)',
            '.similar a::attr(href)',
            '[class*="related"] a[href*="/deals/"]::attr(href)',
            '[class*="similar"] a[href*="/deals/"]::attr(href)',
            'section[class*="related"] a::attr(href)',
            'section[class*="similar"] a::attr(href)',
            # Also try common DealNews patterns
            '.recommended-deals a::attr(href)',
            '.you-may-also-like a::attr(href)',
            '[data-related] a::attr(href)',
            'aside a[href*="/deals/"]::attr(href)',  # Sidebar related deals
            # Try more generic patterns
            'article a[href*="/deals/"]::attr(href)',
            '.deal-item a[href*="/deals/"]::attr(href)',
        ]
        
        related_links = []
        seen_selectors = set()
        for selector in related_selectors:
            if selector in seen_selectors:
                continue
            seen_selectors.add(selector)
            links = response.css(selector).getall()
            if links:
                related_links.extend(links)
                self.logger.info(f"✅ Found {len(links)} related deals using selector: {selector}")
        
        # If no specific related deals found, try to find deals in sidebar or recommendations section
        if not related_links:
            # Look for deals in common recommendation sections
            sidebar_deals = response.css('aside a[href*="/deals/"]::attr(href), .sidebar a[href*="/deals/"]::attr(href)').getall()
            if sidebar_deals:
                related_links.extend(sidebar_deals[:5])  # Limit to 5 to avoid too many
                self.logger.info(f"✅ Found {len(sidebar_deals)} deals in sidebar")
        
        if not related_links:
            self.logger.debug(f"⚠️  No related deals found on detail page: {response.url}")
        
        # Yield related deal items
        seen_links = set()
        for link in related_links:
            if not link or not link.strip():
                continue
            
            # Make absolute URL
            try:
                if not link.startswith('http'):
                    link = response.urljoin(link)
            except:
                continue
            
            # Skip duplicates and current deal
            if link in seen_links or link == response.url:
                continue
            
            # Only process valid deal URLs
            if '/deals/' in link or '/deal/' in link:
                seen_links.add(link)
                related_item = RelatedDealItem()
                related_item['dealid'] = dealid
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
