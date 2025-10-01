# Scrapy settings for dealnews_scraper project

BOT_NAME = 'dealnews_scraper'

SPIDER_MODULES = ['dealnews_scraper.spiders']
NEWSPIDER_MODULE = 'dealnews_scraper.spiders'

ROBOTSTXT_OBEY = False
# Super fast settings for maximum speed
DOWNLOAD_DELAY = 0.1
AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Randomize delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True

# Additional reliability controls
RETRY_ENABLED = True
RETRY_TIMES = 6
DOWNLOAD_TIMEOUT = 15
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

DOWNLOADER_MIDDLEWARES = {
    # Use custom user-agent rotation inside ProxyMiddleware
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'dealnews_scraper.middlewares.ProxyMiddleware': 410,
    # Ensure HttpProxyMiddleware is enabled so request.meta['proxy'] is respected
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 420,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
}

# Set a user agent to avoid being blocked
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Handle 429 responses properly
HTTPERROR_ALLOWED_CODES = [429]
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408, 429]
RETRY_PRIORITY_ADJUST = -1

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
