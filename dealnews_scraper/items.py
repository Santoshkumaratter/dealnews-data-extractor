import scrapy

class DealnewsItem(scrapy.Item):
    # Basic deal information
    dealid = scrapy.Field()
    recid = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    price = scrapy.Field()
    promo = scrapy.Field()
    category = scrapy.Field()
    
    # Store and vendor information
    store = scrapy.Field()
    
    # Deal details
    deal = scrapy.Field()  # e.g., "Up to 80% off"
    dealplus = scrapy.Field()  # e.g., "free shipping w/ Prime"
    
    # Deal link information
    deallink = scrapy.Field()
    dealtext = scrapy.Field()
    dealhover = scrapy.Field()
    
    # Timestamps
    published = scrapy.Field()
    created_at = scrapy.Field()
    
    # Ratings and picks
    popularity = scrapy.Field()
    staffpick = scrapy.Field()
    
    # Additional data
    detail = scrapy.Field()  # Full deal description
    raw_html = scrapy.Field()
    
    # Related deals and categories
    related_deals = scrapy.Field()  # List of related deal URLs
    categories = scrapy.Field()     # List of category objects
    images = scrapy.Field()         # List of image URLs
    
    # Filter variables from the image requirements
    offer_type = scrapy.Field()  # Free shipping, coupon, rebate, etc.
    collection = scrapy.Field()  # Collection name
    condition = scrapy.Field()   # New, used, refurbished, etc.
    events = scrapy.Field()      # Black Friday, Cyber Monday, etc.
    offer_status = scrapy.Field() # Active, Expired, Limited
    include_expired = scrapy.Field() # Yes/No
    brand = scrapy.Field()       # Brand name
    start_date = scrapy.Field()  # Start date filter
    max_price = scrapy.Field()   # Max price filter
    popularity_rank = scrapy.Field() # Popularity rank filter

class DealImageItem(scrapy.Item):
    dealid = scrapy.Field()
    imageurl = scrapy.Field()

class DealCategoryItem(scrapy.Item):
    dealid = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    category_title = scrapy.Field()

class RelatedDealItem(scrapy.Item):
    dealid = scrapy.Field()
    relatedurl = scrapy.Field()
