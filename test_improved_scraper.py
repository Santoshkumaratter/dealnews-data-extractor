#!/usr/bin/env python3
"""
Test script for the improved DealNews scraper
This script tests the database connection and runs the scraper with optimized settings
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def test_database_connection():
    """Test MySQL database connection"""
    print("🔍 Testing MySQL database connection...")
    
    try:
        import mysql.connector
        
        # Database connection parameters
        config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', 'root'),
            'database': os.getenv('MYSQL_DATABASE', 'dealnews'),
            'connection_timeout': 30
        }
        
        # Test connection
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM deals")
        count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        print(f"✅ Database connection successful! Found {count} existing deals.")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("💡 Make sure Docker is running and MySQL container is up")
        return False

def run_improved_scraper():
    """Run the improved scraper with optimized settings"""
    print("🚀 Starting improved DealNews scraper...")
    print("📊 Optimizations applied:")
    print("   - Balanced download delay (0.5s) to avoid rate limiting")
    print("   - Auto-throttling enabled for better reliability")
    print("   - Increased timeout (15s) for slow pages")
    print("   - More conservative concurrency (16 requests)")
    print("   - Better pagination handling")
    print("   - Comprehensive start URLs (100+ categories/stores)")
    print("   - Database retry logic with reconnection")
    print()
    
    # Set environment variables for better performance
    env = os.environ.copy()
    env['CLEAR_DATA'] = 'false'  # Don't clear existing data
    env['FORCE_UPDATE'] = 'false'  # Don't force update existing deals
    
    try:
        # Run the scraper
        result = subprocess.run([
            sys.executable, '-m', 'scrapy', 'crawl', 'dealnews',
            '-L', 'INFO'  # Set log level to INFO for better visibility
        ], env=env, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Scraper completed successfully!")
        else:
            print(f"❌ Scraper failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"❌ Error running scraper: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 DealNews Scraper - Improved Version Test")
    print("=" * 60)
    
    # Test database connection first
    if not test_database_connection():
        print("\n💡 To fix database issues:")
        print("   1. Start Docker Desktop")
        print("   2. Run: docker-compose up -d")
        print("   3. Wait for MySQL to be ready")
        print("   4. Run this script again")
        return
    
    print()
    
    # Ask user if they want to run the scraper
    response = input("🤔 Do you want to run the improved scraper now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        run_improved_scraper()
    else:
        print("👋 Scraper test cancelled. You can run it later with:")
        print("   python test_improved_scraper.py")

if __name__ == "__main__":
    main()
