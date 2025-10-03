# Scrapy settings for dealnews_scraper project

BOT_NAME = 'dealnews_scraper'

SPIDER_MODULES = ['dealnews_scraper.spiders']
NEWSPIDER_MODULE = 'dealnews_scraper.spiders'

ROBOTSTXT_OBEY = False

# Fix Scrapy deprecation warning
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Balanced settings for reliability and speed - more conservative to avoid blocks
DOWNLOAD_DELAY = 2.0  # Increased from 1.0 to 2.0 seconds
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3  # Increased from 2 to 3 seconds
AUTOTHROTTLE_MAX_DELAY = 20  # Increased from 15 to 20 seconds
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Reduced from 1.5 to 1.0
# Randomize delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True

# Additional reliability controls
RETRY_ENABLED = True
RETRY_TIMES = 3
DOWNLOAD_TIMEOUT = 30
CONCURRENT_REQUESTS = 8  # Reduced from 10 to 8
CONCURRENT_REQUESTS_PER_DOMAIN = 3  # Reduced from 5 to 3

DOWNLOADER_MIDDLEWARES = {
    # Enable improved custom middleware
    'dealnews_scraper.middlewares.ProxyMiddleware': 350,
    # Enable default user agent middleware
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
    # Custom error handling is already built into our ProxyMiddleware
}

# Add browser-like headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

# Set a user agent to avoid being blocked
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# User agent rotation to avoid blocking
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

# Enable user agent rotation
RANDOM_UA_PER_DOMAIN = True

# Handle various HTTP responses properly
HTTPERROR_ALLOWED_CODES = [429, 403, 404, 301, 302, 503]
RETRY_HTTP_CODES = [500, 503, 504, 408, 429, 403]  # Keep 403 in retry codes
RETRY_PRIORITY_ADJUST = -1

# Custom retry settings for different error types
RETRY_TIMES_PER_STATUS = {
    403: 5,  # More retries for 403 errors with UA rotation
    429: 3,  # Fewer retries for rate limiting
    503: 3,  # Fewer retries for server errors
}

# Skip 404 errors to avoid infinite retries
SKIP_404_ERRORS = True

ITEM_PIPELINES = {
    'dealnews_scraper.normalized_pipeline.NormalizedMySQLPipeline': 300,
}

FEED_EXPORT_ENCODING = 'utf-8'

# Export settings for JSON and CSV
FEEDS = {
    'exports/deals.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
    },
    'exports/deals.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    }
}
