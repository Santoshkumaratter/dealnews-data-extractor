import scrapy
import re
import time
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

class DealnewsSpider(scrapy.Spider):
    name = "dealnews"
    allowed_domains = ["dealnews.com"]
    handle_httpstatus_list = [403, 404]  # Handle these status codes explicitly
    
    def __init__(self):
        super().__init__()
        self.deals_extracted = 0
        self.start_time = time.time()
        self.max_deals = 1000000  # Maximum limit - 1,000,000+ deals for complete data extraction
    
    # CURRENT WORKING URLs - UPDATED 2025
    start_urls = [
        # Main pages - verified working
        "https://www.dealnews.com/",
        "https://www.dealnews.com/online-stores/",

        # Electronics - current working URLs
        "https://www.dealnews.com/c142/Electronics/",
        "https://www.dealnews.com/c147/Electronics/Audio-Components/Speakers/",
        "https://www.dealnews.com/c148/Electronics/Audio-Components/Home-Theater-Systems/",
        "https://www.dealnews.com/c155/Electronics/Audio-Components/Headphones/",
        "https://www.dealnews.com/c159/Electronics/TVs/",
        "https://www.dealnews.com/c159/Electronics/TVs/b1327/Vizio/",
        "https://www.dealnews.com/c159/Electronics/TVs/b30622/TCL/",
        "https://www.dealnews.com/c159/Electronics/TVs/f1409/4-K/",
        "https://www.dealnews.com/c159/Electronics/TVs/f1667/Smart-TV/",
        "https://www.dealnews.com/c168/Electronics/Cameras/Digital-Cameras/",
        "https://www.dealnews.com/c171/Electronics/Phones-Cell-Phones/",
        "https://www.dealnews.com/c189/Gaming-Toys/Computer-Games/PC-Games/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/f1158/Play-Station-4/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/f1546/Xbox-One/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/f1652/Nintendo-Switch/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/f1915/Play-Station-5/",
        "https://www.dealnews.com/c191/Gaming-Toys/Video-Games/f1918/Xbox-Series-S-X/",
        "https://www.dealnews.com/c299/Electronics/Camcorders/",
        "https://www.dealnews.com/c306/Electronics/Batteries/",
        "https://www.dealnews.com/c452/Electronics/Streaming-Media-Players/",
        "https://www.dealnews.com/c491/Electronics/Phones-Cell-Phones/Apple-iPhones/",
        "https://www.dealnews.com/c671/Electronics/Phones-Cell-Phones/Apple-iPhones/iPhone-Accessories/iPhone-Cases/",
        "https://www.dealnews.com/c672/Electronics/Phones-Cell-Phones/Android-Phones/",
        "https://www.dealnews.com/c673/Electronics/Phones-Cell-Phones/Android-Phones/Android-Phone-Accessories/",
        "https://www.dealnews.com/c837/Electronics/Portable-Speakers/",
        "https://www.dealnews.com/c914/Electronics/Wearable-Technology/Smart-Watches/",
        "https://www.dealnews.com/c914/Electronics/Wearable-Technology/Smart-Watches/b13/Apple/",
        "https://www.dealnews.com/c914/Electronics/Wearable-Technology/Smart-Watches/b28/Samsung/",
        "https://www.dealnews.com/c917/Electronics/Wearable-Technology/Fitness-Trackers/b36121/Fitbit/",
        
        # Computers - verified working URLs
        "https://www.dealnews.com/c39/Computers/",
        "https://www.dealnews.com/c39/Computers/t2/Coupons/",
        "https://www.dealnews.com/c41/Computers/Apple-Computers/",
        "https://www.dealnews.com/c48/Computers/Desktops/",
        "https://www.dealnews.com/c49/Computers/Laptops/",
        "https://www.dealnews.com/c49/Computers/Laptops/f15/Core-i5/",
        "https://www.dealnews.com/c49/Computers/Laptops/f31/Gaming/",
        "https://www.dealnews.com/c49/Computers/Laptops/s897/Costco/",
        "https://www.dealnews.com/c56/Computers/Storage/Hard-Drives/",
        "https://www.dealnews.com/c70/Computers/Peripherals/Input-Devices/",
        "https://www.dealnews.com/c75/Computers/Peripherals/Monitors/",
        "https://www.dealnews.com/c93/Computers/Upgrades-Components/",
        "https://www.dealnews.com/c108/Computers/Storage/Flash-Memory-Cards/",
        "https://www.dealnews.com/c124/Computers/Software/",
        "https://www.dealnews.com/c297/Computers/Storage/USB-Flash-Drives/",
        "https://www.dealnews.com/c572/Computers/iPad-Tablet/iPad-Accessories/",
        "https://www.dealnews.com/c577/Computers/iPad-Tablet/iPad-Apps/",
        "https://www.dealnews.com/c623/Computers/iPad-Tablet/Tablet-Accessories/",
        "https://www.dealnews.com/c732/Computers/Networking/Wireless-Networking/Routers/",
        
        # Home & Garden - verified working URLs
        "https://www.dealnews.com/c196/Home-Garden/",
        "https://www.dealnews.com/c196/Home-Garden/t2/Coupons/",
        "https://www.dealnews.com/c199/Home-Garden/Home-Furniture/",
        "https://www.dealnews.com/c200/Home-Garden/Decor/",
        "https://www.dealnews.com/c213/Home-Garden/Food-Drink/",
        "https://www.dealnews.com/c214/Home-Garden/Food-Drink/Groceries/",
        "https://www.dealnews.com/c304/Home-Garden/Appliances/",
        "https://www.dealnews.com/c360/Home-Garden/Bed-Bath/",
        "https://www.dealnews.com/c377/Home-Garden/Food-Drink/Restaurants/",
        "https://www.dealnews.com/c529/Home-Garden/Garden/BBQs-Grills/",
        "https://www.dealnews.com/c607/Home-Garden/Appliances/Household-Items/Air-Conditioners/",
        "https://www.dealnews.com/c642/Home-Garden/Kitchen/Small-Appliances/",
        "https://www.dealnews.com/c645/Home-Garden/Tools-Hardware/Hand-Tools/",
        "https://www.dealnews.com/c646/Home-Garden/Tools-Hardware/Power-Tools/",
        "https://www.dealnews.com/c647/Home-Garden/Tools-Hardware/Tool-Storage-Organization/",
        "https://www.dealnews.com/c648/Home-Garden/Tools-Hardware/Flashlights-Lighting/",
        "https://www.dealnews.com/c661/Home-Garden/Babies-Kids-Items/Diapers-Wipes/",
        "https://www.dealnews.com/c744/Home-Garden/Garden/Patio-Furniture/",
        "https://www.dealnews.com/c747/Home-Garden/Garden/Garden-Tools/",
        "https://www.dealnews.com/c810/Home-Garden/Light-Bulbs/",
        
        # Clothing & Accessories - verified working URLs
        "https://www.dealnews.com/c202/Clothing-Accessories/",
        "https://www.dealnews.com/c202/Clothing-Accessories/f1/Mens/",
        "https://www.dealnews.com/c202/Clothing-Accessories/f2/Womens/",
        "https://www.dealnews.com/c202/Clothing-Accessories/f5/Girls/",
        "https://www.dealnews.com/c202/Clothing-Accessories/t2/Coupons/",
        "https://www.dealnews.com/c227/Clothing-Accessories/Jewelry/",
        "https://www.dealnews.com/c280/Clothing-Accessories/Shoes/f1/Mens/f1107/Sandals/",
        "https://www.dealnews.com/c280/Clothing-Accessories/Shoes/f2/Womens/",
        "https://www.dealnews.com/c287/Clothing-Accessories/Luggage-Travel-Gear/",
        "https://www.dealnews.com/c436/Clothing-Accessories/Accessories/Watches/",
        "https://www.dealnews.com/c454/Clothing-Accessories/Accessories/Sunglasses/",
        "https://www.dealnews.com/c454/Clothing-Accessories/Accessories/Sunglasses/f1/Mens/",
        "https://www.dealnews.com/c481/Clothing-Accessories/Accessories/Handbags/",
        "https://www.dealnews.com/c487/Clothing-Accessories/Activewear/",
        "https://www.dealnews.com/c487/Clothing-Accessories/Activewear/f2/Womens/",
        "https://www.dealnews.com/c488/Clothing-Accessories/Intimates/f2/Womens/",
        "https://www.dealnews.com/c489/Clothing-Accessories/Coats/",
        "https://www.dealnews.com/c489/Clothing-Accessories/Coats/f1/Mens/",
        "https://www.dealnews.com/c490/Clothing-Accessories/Dresses/f2/Womens/",
        "https://www.dealnews.com/c515/Clothing-Accessories/Jeans/",
        "https://www.dealnews.com/c716/Clothing-Accessories/Shirts/f1/Mens/",
        "https://www.dealnews.com/c716/Clothing-Accessories/Shirts/f2/Womens/",
        "https://www.dealnews.com/c717/Clothing-Accessories/Shorts/f1/Mens/",
        "https://www.dealnews.com/c717/Clothing-Accessories/Shorts/f2/Womens/",
        "https://www.dealnews.com/c721/Clothing-Accessories/T-Shirts/f1/Mens/",
        "https://www.dealnews.com/c851/Clothing-Accessories/Luggage-Travel-Gear/Backpacks/",
        "https://www.dealnews.com/c866/Clothing-Accessories/Sweatshirts-Hoodies/",
        
        # Travel & Entertainment - verified working URLs
        "https://www.dealnews.com/c206/Travel-Entertainment/",
        "https://www.dealnews.com/c206/Travel-Entertainment/f1069/Caribbean/",
        "https://www.dealnews.com/c206/Travel-Entertainment/s857/Sams-Club/",
        "https://www.dealnews.com/c207/Travel-Entertainment/Airfare/",
        "https://www.dealnews.com/c629/Travel-Entertainment/Cruises/",
        
        # Health & Beauty - verified working URLs
        "https://www.dealnews.com/c798/Health-Beauty/Health/Supplements/",
        
        # Financial Services - verified working URLs
        "https://www.dealnews.com/c522/Financial-Services/Credit-Cards/",
        
        # Popular stores - verified working URLs
        "https://www.dealnews.com/s313/Amazon/",
        "https://www.dealnews.com/s1186/Nike/",
        "https://www.dealnews.com/s1669/Verizon-Fios/",
        "https://www.dealnews.com/s1764/Verizon/",
        "https://www.dealnews.com/s42512/lululemon/",
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
        if response.status == 404:
            self.logger.warning(f"404 error for URL: {response.url}")
            return
        
        if response.status == 403:
            self.logger.warning(f"403 error for URL: {response.url}")
            return
        
        self.logger.info(f"Parsing: {response.url}")
        
        # IMPROVED DEAL EXTRACTION - Multiple selectors for maximum coverage
        deals = []
        
        # Try multiple deal selectors to find ONLY REAL DEALS (not navigation)
        deal_selectors = [
            # DealNews specific selectors - UPDATED for current site
            '[data-deal-id]',  # Real deals have data-deal-id
            '[data-rec-id]',   # Real deals have data-rec-id
            '.deal-item',      # Main deal container
            '.deal-card',
            '.deal-tile',
            '.deal-container',
            '.deal-wrapper',
            '.deal-box',
            '.deal-content',
            '.deal-listing',
            '.deal-post',
            '.deal-entry',
            # More specific selectors for actual deals
            '.deal-item-wrapper',
            '.deal-item-container',
            '.deal-block',
            '.deal-grid-item',
            '.deal-list-item',
            # Look within main content areas (avoid navigation)
            'main [data-deal-id]',
            'main [data-rec-id]',
            'main .deal-item',
            '.main-content [data-deal-id]',
            '.main-content .deal-item',
            # Article-based selectors for deals
            'article[class*="deal"]:not([class*="nav"]):not([class*="menu"])',
            'div[class*="deal"]:not([class*="nav"]):not([class*="menu"])'
        ]
        
        for selector in deal_selectors:
            found_deals = response.css(selector)
            if found_deals:
                self.logger.info(f"Found {len(found_deals)} deals with selector: {selector}")
                deals.extend(found_deals)
            else:
                self.logger.debug(f"No deals found with selector: {selector}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_deals = []
        for deal in deals:
            deal_html = deal.get()
            if deal_html not in seen:
                seen.add(deal_html)
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
                yield from self.extract_deal_categories(deal, item)
                yield from self.extract_related_deals(deal, item)
        
        # Handle pagination
        yield from self.handle_pagination(response)
        
        # Log progress
        elapsed_time = time.time() - self.start_time
        rate = self.deals_extracted / elapsed_time if elapsed_time > 0 else 0
        self.logger.info(f"Progress: {self.deals_extracted} deals extracted in {elapsed_time:.1f}s (rate: {rate:.1f} deals/sec)")

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
                item['title'] = 'No title found'
            
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
            
            # IMPROVED Category extraction
            category_selectors = [
                # DealNews specific
                '.category::text',
                '.deal-category::text',
                '.breadcrumb::text',
                '.deal-breadcrumb::text',
                # Generic
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

            # Ensure categories list exists for pipeline normalization
            if item['category']:
                item['categories'] = [item['category']]
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

    def extract_deal_categories(self, deal, item):
        """Extract deal categories"""
        categories = deal.css('.category::text, .tag::text, .label::text, .breadcrumb::text').getall()
        for category in categories:
            text = category.strip()
            if text:
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
        """Handle pagination and infinite scroll for DealNews"""
        self.logger.info(f"Handling pagination for: {response.url}")
        
        # Look for DealNews-specific pagination patterns - updated for 2025
        ajax_pagination_patterns = [
            'a[href*="?start="]',  # DealNews current pattern
            'a[href*="&start="]',  # DealNews current pattern
            '.pagination a[href*="start="]',
            '.pager a[href*="start="]',
            '.page-numbers a[href*="start="]',
            # More specific patterns
            'a[href*="start="][href*="e=1"]',  # With category filter
            'a[href*="start="][href*="pf=1"]',  # With staff pick filter
        ]
        
        pagination_found = 0
        for pattern in ajax_pagination_patterns:
            pagination_links = response.css(pattern + '::attr(href)').getall()
            for link in pagination_links[:5]:  # Reduced to first 5 pagination links
                if link and self.is_valid_dealnews_url(link):
                    # Avoid old pagination patterns that cause 404s
                    if 'start=' in link and not any(x in link for x in ['page=', 'offset=', 'p=']):
                        self.logger.info(f"Found pagination link: {link}")
                        yield response.follow(link, self.parse, errback=self.errback_http)
                        pagination_found += 1
        
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
            for button in load_more_buttons[:3]:  # Reduced to first 3 load more buttons
                data_url = button.css('::attr(data-url)').get() or button.css('::attr(href)').get()
                if data_url and 'start=' in data_url:
                    self.logger.info(f"Found load more button: {data_url}")
                    yield response.follow(data_url, self.parse, errback=self.errback_http)
                    load_more_found += 1
        
        # Also look for traditional pagination links - but only with start= pattern
        pagination_links = response.css('.pagination a[href*="start="]::attr(href), .pager a[href*="start="]::attr(href)').getall()
        valid_pagination_links = 0
        for link in pagination_links[:5]:  # Much more reasonable limit
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
