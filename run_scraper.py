#!/usr/bin/env python3
"""
Run the DealNews scraper to collect 100,000+ deals into MySQL.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=" * 60)
    print("DealNews Scraper - Collecting 100,000+ Deals")
    print("=" * 60)
    print()
    
    # Check if MySQL is enabled
    disable_mysql = os.getenv('DISABLE_MYSQL', 'false').lower() in ('1', 'true', 'yes')
    if disable_mysql:
        print("⚠️  WARNING: MySQL is disabled. Deals will only be exported to JSON/CSV.")
        print("   Set DISABLE_MYSQL=false in .env to enable MySQL storage.")
        print()
    
    # Run the scraper
    print("🚀 Starting scraper...")
    print()
    
    try:
        # Run scrapy crawl using python -m scrapy (more reliable)
        result = subprocess.run(
            [sys.executable, '-m', 'scrapy', 'crawl', 'dealnews'],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print()
            print("=" * 60)
            print("✅ Scraping completed successfully!")
            print("=" * 60)
            print()
            print("Next steps:")
            print("  1. Run: python3 verify_mysql.py")
            print("  2. Check MySQL database for deal counts")
            print()
        else:
            print()
            print("❌ Scraping failed with exit code:", result.returncode)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print()
        print("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error running scraper: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

