#!/usr/bin/env python3
"""
Test script to verify related deals crawling functionality.

This script checks:
1. If related deals are being extracted and saved to related_deals table
2. If those related deal URLs are being crawled and added to the deals table
3. If URL deduplication is working (checking scanned_urls set)
4. If the unique constraint on deals.url is preventing duplicates
"""

import os
import mysql.connector
from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

def connect_db():
    """Connect to MySQL database"""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DATABASE', 'dealnews')
    )

def test_related_deals_crawling():
    """Test if related deals are being crawled and added to deals table"""
    
    print("=" * 80)
    print("TESTING RELATED DEALS CRAWLING FUNCTIONALITY")
    print("=" * 80)
    print()
    
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    
    # Test 1: Check row 21 in related_deals table
    print("TEST 1: Checking row 21 in related_deals table")
    print("-" * 80)
    cursor.execute("""
        SELECT id, dealid, relatedurl, created_at 
        FROM related_deals 
        WHERE id = 21
    """)
    row_21 = cursor.fetchone()
    
    if row_21:
        print(f"✅ Found row 21 in related_deals:")
        print(f"   ID: {row_21['id']}")
        print(f"   Deal ID: {row_21['dealid']}")
        print(f"   Related URL: {row_21['relatedurl']}")
        print(f"   Created: {row_21['created_at']}")
        related_url = row_21['relatedurl']
    else:
        print("❌ Row 21 not found in related_deals table")
        conn.close()
        return
    
    print()
    
    # Test 2: Check if this URL exists in deals table
    print("TEST 2: Checking if related URL exists in deals table")
    print("-" * 80)
    cursor.execute("""
        SELECT id, dealid, title, url, created_at
        FROM deals
        WHERE url = %s
    """, (related_url,))
    deal_by_url = cursor.fetchone()
    
    if deal_by_url:
        print(f"✅ Found deal with matching URL in deals table:")
        print(f"   ID: {deal_by_url['id']}")
        print(f"   Deal ID: {deal_by_url['dealid']}")
        print(f"   Title: {deal_by_url['title']}")
        print(f"   URL: {deal_by_url['url']}")
        print(f"   Created: {deal_by_url['created_at']}")
    else:
        print(f"❌ URL '{related_url}' NOT found in deals table")
        print("   This means the related deal was NOT crawled!")
    
    print()
    
    # Test 3: Search for "balance" in deals table
    print("TEST 3: Searching for 'balance' in deals table")
    print("-" * 80)
    cursor.execute("""
        SELECT id, dealid, title, url, created_at
        FROM deals
        WHERE title LIKE %s
        LIMIT 10
    """, ('%balance%',))
    balance_deals = cursor.fetchall()
    
    if balance_deals:
        print(f"✅ Found {len(balance_deals)} deal(s) with 'balance' in title:")
        for deal in balance_deals:
            print(f"   - ID {deal['id']}: {deal['title'][:80]}")
    else:
        print("❌ No deals found with 'balance' in title")
    
    print()
    
    # Test 4: Check related_deals table statistics
    print("TEST 4: Related deals table statistics")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as total FROM related_deals")
    total_related = cursor.fetchone()['total']
    print(f"Total related deals in database: {total_related}")
    
    cursor.execute("""
        SELECT COUNT(DISTINCT rd.relatedurl) as crawled_count
        FROM related_deals rd
        INNER JOIN deals d ON rd.relatedurl = d.url
    """)
    crawled_count = cursor.fetchone()['crawled_count']
    print(f"Related deals that were crawled: {crawled_count}")
    print(f"Related deals NOT yet crawled: {total_related - crawled_count}")
    print(f"Crawl percentage: {(crawled_count / total_related * 100):.2f}%" if total_related > 0 else "N/A")
    
    print()
    
    # Test 5: Sample of related deals that were NOT crawled
    print("TEST 5: Sample of related deals that were NOT crawled (first 10)")
    print("-" * 80)
    cursor.execute("""
        SELECT rd.id, rd.dealid, rd.relatedurl, rd.created_at
        FROM related_deals rd
        LEFT JOIN deals d ON rd.relatedurl = d.url
        WHERE d.url IS NULL
        LIMIT 10
    """)
    not_crawled = cursor.fetchall()
    
    if not_crawled:
        print(f"Found {len(not_crawled)} related deals that were NOT crawled:")
        table_data = []
        for rd in not_crawled:
            table_data.append([
                rd['id'],
                rd['dealid'][:20],
                rd['relatedurl'][:60] + '...' if len(rd['relatedurl']) > 60 else rd['relatedurl'],
                rd['created_at']
            ])
        print(tabulate(table_data, headers=['ID', 'Deal ID', 'Related URL', 'Created'], tablefmt='grid'))
    else:
        print("✅ All related deals have been crawled!")
    
    print()
    
    # Test 6: Check for duplicate URLs in deals table
    print("TEST 6: Checking for duplicate URLs in deals table")
    print("-" * 80)
    cursor.execute("""
        SELECT url, COUNT(*) as count
        FROM deals
        WHERE url IS NOT NULL
        GROUP BY url
        HAVING count > 1
        LIMIT 10
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate URLs:")
        for dup in duplicates:
            print(f"   - {dup['url']}: {dup['count']} occurrences")
    else:
        print("✅ No duplicate URLs found - deduplication is working!")
    
    print()
    
    # Test 7: Verify unique constraint on deals.url
    print("TEST 7: Verifying unique constraint on deals.url")
    print("-" * 80)
    cursor.execute("""
        SHOW CREATE TABLE deals
    """)
    create_table = cursor.fetchone()
    create_sql = create_table['Create Table'] if 'Create Table' in create_table else str(create_table)
    
    if 'UNIQUE KEY unique_url' in create_sql or 'UNIQUE KEY `url`' in create_sql:
        print("✅ Unique constraint on 'url' column exists")
    else:
        print("❌ Unique constraint on 'url' column NOT found!")
        print("   This could allow duplicate URLs in the database")
    
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    issues = []
    
    if not deal_by_url:
        issues.append("❌ Related deal URL from row 21 is NOT in deals table (not crawled)")
    else:
        print("✅ Related deal URL from row 21 IS in deals table (crawled successfully)")
    
    if not balance_deals:
        issues.append("❌ No deals with 'balance' in title found")
    else:
        print(f"✅ Found {len(balance_deals)} deal(s) with 'balance' in title")
    
    if crawled_count < total_related:
        issues.append(f"⚠️  Only {crawled_count}/{total_related} related deals have been crawled")
    else:
        print(f"✅ All {total_related} related deals have been crawled")
    
    if duplicates:
        issues.append(f"❌ Found {len(duplicates)} duplicate URLs in deals table")
    else:
        print("✅ No duplicate URLs found")
    
    if issues:
        print()
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  {issue}")
    
    print()
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    try:
        test_related_deals_crawling()
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
