# Scrapy settings for dealnews_scraper project

BOT_NAME = 'dealnews_scraper'

SPIDER_MODULES = ['dealnews_scraper.spiders']
NEWSPIDER_MODULE = 'dealnews_scraper.spiders'

ROBOTSTXT_OBEY = False

# Fix Scrapy deprecation warning
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# PERFORMANCE OPTIMIZATION: Reduce logging to improve speed
# Only log warnings and errors to minimize I/O overhead
LOG_LEVEL = os.getenv('LOG_LEVEL', 'WARNING')  # WARNING, ERROR, or CRITICAL for production
LOG_ENABLED = True
LOG_STDOUT = False  # Don't log to stdout, only to file
LOG_FILE = 'error.log'  # Single log file
LOG_FILE_APPEND = False  # Overwrite log file on each run to prevent huge files

# OPTIMIZED settings for ULTRA-FAST extraction (15-20 minutes)
import os
DOWNLOAD_DELAY = float(os.getenv('DOWNLOAD_DELAY', '0.1'))  # Minimal delay for speed
AUTOTHROTTLE_ENABLED = os.getenv('AUTOTHROTTLE_ENABLED', 'true').lower() == 'true'
AUTOTHROTTLE_START_DELAY = float(os.getenv('AUTOTHROTTLE_START_DELAY', '0.5'))
AUTOTHROTTLE_MAX_DELAY = float(os.getenv('AUTOTHROTTLE_MAX_DELAY', '3'))
AUTOTHROTTLE_TARGET_CONCURRENCY = float(os.getenv('AUTOTHROTTLE_TARGET_CONCURRENCY', '20.0'))  # Optimized concurrency
RANDOMIZE_DOWNLOAD_DELAY = True  # Enable randomization to avoid detection

# Optimized controls for maximum speed with reliability (100k+ deals in hours)
RETRY_ENABLED = True  # Enable retries for reliability
RETRY_TIMES = int(os.getenv('RETRY_TIMES', '3'))
DOWNLOAD_TIMEOUT = int(os.getenv('DOWNLOAD_TIMEOUT', '20'))  # Balanced timeout
CONCURRENT_REQUESTS = int(os.getenv('CONCURRENT_REQUESTS', '64'))  # High concurrency for speed
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.getenv('CONCURRENT_REQUESTS_PER_DOMAIN', '32'))  # High per domain
REACTOR_THREADPOOL_SIZE = 32  # Optimized thread pool

DOWNLOADER_MIDDLEWARES = {
    # Enable improved custom middleware (higher than RetryMiddleware so 407 handling wins)
    'dealnews_scraper.middlewares.ProxyMiddleware': 600,
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
HTTPERROR_ALLOWED_CODES = [400, 429, 403, 404, 301, 302, 503, 500]
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

# Disable exports when MySQL pipeline is enabled to maximize speed
if os.getenv('DISABLE_MYSQL', 'false').lower() in ('1', 'true', 'yes'):
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
else:
    FEEDS = {}
