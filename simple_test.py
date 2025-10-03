#!/usr/bin/env python3
"""
Simple test script without custom middleware
"""

import scrapy
from scrapy.crawler import CrawlerProcess

class SimpleDealnewsSpider(scrapy.Spider):
    name = "simple_dealnews"
    allowed_domains = ["dealnews.com"]
    start_urls = [
        "https://www.dealnews.com/",
        "https://www.dealnews.com/online-stores/",
    ]
    
    def parse(self, response):
        self.logger.info(f"Successfully parsed: {response.url}")
        self.logger.info(f"Response status: {response.status}")
        self.logger.info(f"Response size: {len(response.text)} bytes")
        
        # Extract some basic information
        title = response.css('title::text').get()
        if title:
            self.logger.info(f"Page title: {title.strip()}")
        
        # Look for deal elements
        deals = response.css('.content-card, .deal-card, .offer-card, .product-card')
        self.logger.info(f"Found {len(deals)} potential deal elements")
        
        return {
            'url': response.url,
            'status': response.status,
            'title': title.strip() if title else '',
            'deal_count': len(deals),
            'response_size': len(response.text)
        }

def test_simple_scraper():
    """Test with minimal configuration"""
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'RETRY_TIMES': 2,
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'INFO',
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'DOWNLOADER_MIDDLEWARES': {},  # Disable all custom middlewares
        'FEEDS': {
            'simple_test_output.json': {
                'format': 'json',
                'encoding': 'utf8',
                'store_empty': False,
                'indent': 2,
            }
        }
    }
    
    process = CrawlerProcess(custom_settings)
    process.crawl(SimpleDealnewsSpider)
    process.start()

if __name__ == "__main__":
    test_simple_scraper()
