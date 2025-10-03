#!/usr/bin/env python3
"""
Test script for the main DealNews spider
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider
from dealnews_scraper.settings import *

def test_main_spider():
    """Test the main spider with updated settings"""
    
    # Override settings for testing
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 2,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'INFO',
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        },
        'DOWNLOADER_MIDDLEWARES': {
            'dealnews_scraper.middlewares.ProxyMiddleware': None,
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': 400,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
        },
        'FEEDS': {
            'main_spider_test_output.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 2,
            }
        }
    }
    
    # Test with only a few URLs
    test_urls = [
        "https://www.dealnews.com/",
        "https://www.dealnews.com/online-stores/",
        "https://www.dealnews.com/c142/Electronics/",
    ]
    
    # Create a test spider class
    class TestMainSpider(DealnewsSpider):
        name = "test_main_dealnews"
        start_urls = test_urls
        max_deals = 50  # Limit for testing
        
        def __init__(self):
            super().__init__()
            self.max_deals = 50
    
    # Run the test
    process = CrawlerProcess(custom_settings)
    process.crawl(TestMainSpider)
    process.start()

if __name__ == "__main__":
    test_main_spider()
