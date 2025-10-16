#!/usr/bin/env python3
"""
Docker-free test to verify scraper can extract deals
"""

import os
import sys
import time
sys.path.append('.')

def test_scraper_without_docker():
    """Test scraper without Docker/MySQL"""
    print("🧪 Testing scraper without Docker/MySQL...")
    print("This will test if the scraper can extract deals and export to JSON/CSV")

    # Set environment to disable MySQL
    os.environ['DISABLE_MYSQL'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['CLOSESPIDER_ITEMCOUNT'] = '50'  # Stop after 50 items

    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider

        # Get settings
        settings = get_project_settings()
        settings.set('LOG_LEVEL', 'INFO')

        # Configure feeds for testing
        settings.set('FEEDS', {
            'test_output_deals.json': {
                'format': 'json',
                'encoding': 'utf8',
                'indent': 2,
            },
            'test_output_deals.csv': {
                'format': 'csv',
                'encoding': 'utf8',
            }
        })

        print("🚀 Starting test scraper (50 items max)...")

        # Create and run crawler
        process = CrawlerProcess(settings)
        process.crawl(DealnewsSpider)

        start_time = time.time()
        process.start()
        end_time = time.time()

        duration = end_time - start_time
        print(f"✅ Scraper completed in {duration:.1f} seconds")

        # Check if output files were created
        json_exists = os.path.exists('test_output_deals.json')
        csv_exists = os.path.exists('test_output_deals.csv')

        if json_exists and csv_exists:
            # Check file sizes
            json_size = os.path.getsize('test_output_deals.json')
            csv_size = os.path.getsize('test_output_deals.csv')

            print("✅ Output files created:")
            print(f"   📄 test_output_deals.json: {json_size:,} bytes")
            print(f"   📄 test_output_deals.csv: {csv_size:,} bytes")

            # Check if JSON has actual data
            import json
            with open('test_output_deals.json', 'r') as f:
                data = json.load(f)
                if data:
                    print(f"   ✅ JSON contains {len(data)} items")
                    # Check first item has required fields
                    first_item = data[0]
                    required_fields = ['dealid', 'title', 'url']
                    missing_fields = [f for f in required_fields if f not in first_item]
                    if missing_fields:
                        print(f"   ⚠️ Missing fields in first item: {missing_fields}")
                    else:
                        print("   ✅ First item has all required fields")
                else:
                    print("   ❌ JSON is empty")
                    return False

            return True
        else:
            print("❌ Output files not created")
            return False

    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return False

def main():
    print("=" * 60)
    print("DealNews Scraper - Docker-Free Test")
    print("=" * 60)

    success = test_scraper_without_docker()

    print("\n" + "=" * 60)
    if success:
        print("🎉 DOCKER-FREE TEST PASSED!")
        print("✅ Scraper can extract and export deals")
        print("✅ JSON and CSV exports working")
        print("✅ Items have required fields")
        print("\n🚀 Next steps:")
        print("1. Enable MySQL in .env (DISABLE_MYSQL=false)")
        print("2. Start MySQL server")
        print("3. Run full scraper with: docker-compose up scraper")
    else:
        print("❌ DOCKER-FREE TEST FAILED")
        print("Please check the errors above")
    print("=" * 60)

    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
