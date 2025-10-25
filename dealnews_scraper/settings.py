# Scrapy settings for dealnews_scraper project

BOT_NAME = 'dealnews_scraper'

SPIDER_MODULES = ['dealnews_scraper.spiders']
NEWSPIDER_MODULE = 'dealnews_scraper.spiders'

ROBOTSTXT_OBEY = False

# Fix Scrapy deprecation warning
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# ULTRA-CONSERVATIVE settings for maximum reliability
DOWNLOAD_DELAY = 2.0  # Higher delay to avoid blocking
AUTOTHROTTLE_ENABLED = True  # Enable auto-throttling for reliability
AUTOTHROTTLE_START_DELAY = 3  # Start with 3 second delay
AUTOTHROTTLE_MAX_DELAY = 10  # Max 10 second delay
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0  # Very conservative concurrency
# Randomize delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True  # Enable randomization to avoid detection

# Ultra-conservative controls for maximum reliability
RETRY_ENABLED = True  # Enable retries for reliability
RETRY_TIMES = 3  # Reduced retries to avoid hammering
DOWNLOAD_TIMEOUT = 60  # Higher timeout for reliability
CONCURRENT_REQUESTS = 4  # Very conservative concurrent requests
CONCURRENT_REQUESTS_PER_DOMAIN = 2  # Very conservative domain concurrency
REACTOR_THREADPOOL_SIZE = 10  # Increase thread pool for better connection handling

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

# Handle various HTTP responses properly - allow more error codes
HTTPERROR_ALLOWED_CODES = [429, 403, 404, 301, 302, 503, 500]
RETRY_HTTP_CODES = [500, 503, 504, 408, 429]  # Remove 403 and 404 from retry to avoid loops
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
