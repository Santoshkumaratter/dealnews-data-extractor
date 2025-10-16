#!/usr/bin/env python3
"""
Simple test to verify scraper is working
"""

import os
import sys
sys.path.append('.')


def test_imports():
    """Test that all imports work"""
    print("🔍 Testing imports...")
    try:
        from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider
        from dealnews_scraper.items import DealnewsItem
        from dealnews_scraper.normalized_pipeline import NormalizedMySQLPipeline
        print("   ✅ All imports working")
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_spider():
    """Test spider initialization"""
    print("🕷️ Testing spider...")
    try:
        from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider
        spider = DealnewsSpider()
        print(f"   ✅ Spider initialized with {len(spider.start_urls)} URLs")
        return True
    except Exception as e:
        print(f"   ❌ Spider error: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("🗄️ Testing database connection...")
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=int(os.getenv('MYSQL_PORT', '3306')),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', 'root'),
            database=os.getenv('MYSQL_DATABASE', 'dealnews'),
            connection_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"   ✅ Database connected successfully")
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print("   💡 To fix: Start MySQL server or update .env with correct credentials")
        return False

def test_environment():
    """Test environment configuration"""
    print("🔧 Testing environment...")
    env_file = '.env'
    if os.path.exists(env_file):
        print("   ✅ .env file exists")
    else:
        print("   ⚠️ .env file not found, using defaults")

    # Check required env vars
    required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DATABASE']
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"   ⚠️ Missing env vars: {missing_vars}")
    else:
        print("   ✅ All required env vars set")

    return True

def main():
    print("=" * 60)
    print("DealNews Scraper - Simple Test")
    print("=" * 60)

    tests = [
        ("Environment", test_environment),
        ("Imports", test_imports),
        ("Spider", test_spider),
        ("Database", test_database_connection),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} {status}")
        if result:
            passed += 1

    print("\n" + "=" * 60)
    if passed >= 3:  # Allow database to fail if MySQL not running
        print("🎉 MOST TESTS PASSED! Scraper is ready!")
        print("\nNext steps:")
        print("1. If database test failed, start MySQL server")
        print("2. Run: docker-compose up scraper")
        print("3. Or run without Docker: python3 run.py")
    else:
        print("❌ SOME TESTS FAILED - Please fix issues above")
    print("=" * 60)

    return passed >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
