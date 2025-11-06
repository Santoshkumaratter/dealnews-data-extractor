#!/usr/bin/env python3
"""
Unit tests for DealNews parser
"""
import unittest
from scrapy.http import HtmlResponse
from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider

class TestDealnewsParser(unittest.TestCase):
    """Test parser functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.spider = DealnewsSpider()
    
    def test_extract_category_from_url(self):
        """Test category extraction from URL"""
        # Test with category ID
        url1 = "https://www.dealnews.com/c142/Electronics/"
        category1 = self.spider.extract_category_from_url(url1)
        self.assertIn("Electronics", category1)
        
        # Test with category path
        url2 = "https://www.dealnews.com/c39/Computers/"
        category2 = self.spider.extract_category_from_url(url2)
        self.assertIn("Computers", category2)
        
        # Test with no category
        url3 = "https://www.dealnews.com/"
        category3 = self.spider.extract_category_from_url(url3)
        self.assertEqual(category3, '')
    
    def test_extract_collection_from_url(self):
        """Test collection extraction from URL"""
        # Test with store/collection
        url1 = "https://www.dealnews.com/s313/Amazon/"
        collection1 = self.spider.extract_collection_from_url(url1)
        self.assertIsNotNone(collection1)
        self.assertIn("Amazon", collection1)
        
        # Test with no collection
        url2 = "https://www.dealnews.com/"
        collection2 = self.spider.extract_collection_from_url(url2)
        self.assertIsNone(collection2)
    
    def test_is_valid_dealnews_url(self):
        """Test URL validation"""
        # Valid URLs
        self.assertTrue(self.spider.is_valid_dealnews_url("https://www.dealnews.com/deals/123"))
        self.assertTrue(self.spider.is_valid_dealnews_url("/deals/123"))
        
        # Invalid URLs
        self.assertFalse(self.spider.is_valid_dealnews_url("javascript:void(0)"))
        self.assertFalse(self.spider.is_valid_dealnews_url("mailto:test@example.com"))
        self.assertFalse(self.spider.is_valid_dealnews_url("#anchor"))
        self.assertFalse(self.spider.is_valid_dealnews_url("https://example.com"))
    
    def test_parse_simple_deal(self):
        """Test parsing a simple deal HTML"""
        html = """
        <div data-deal-id="test123" class="deal-item">
            <h3 class="deal-title">Test Deal</h3>
            <span class="price">$99.99</span>
            <span class="store">Amazon</span>
            <div class="deal-description">Great deal on test product</div>
        </div>
        """
        response = HtmlResponse(url="https://www.dealnews.com/", body=html.encode(), encoding='utf-8')
        
        # Parse the response
        results = list(self.spider.parse(response))
        
        # Should extract at least the deal item
        self.assertGreater(len(results), 0)
        
        # Check if DealnewsItem is in results
        deal_items = [r for r in results if isinstance(r, dict) and 'dealid' in r]
        if deal_items:
            deal = deal_items[0]
            self.assertIn('dealid', deal)
            self.assertIn('title', deal)

if __name__ == '__main__':
    unittest.main()

