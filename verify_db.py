#!/usr/bin/env python3
"""
Verify Database - DealNews Scraper
Checks database for expected counts and non-null filter fields
"""

import os
import sys
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

def main():
    print("=" * 60)
    print("DealNews Scraper - Database Verification")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get MySQL connection settings
    mysql_host = os.getenv('MYSQL_HOST', 'localhost')
    mysql_port = int(os.getenv('MYSQL_PORT', '3306'))
    mysql_user = os.getenv('MYSQL_USER', 'root')
    mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
    mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
    
    print(f"Connecting to MySQL: {mysql_host}:{mysql_port} as {mysql_user} to database {mysql_database}")
    
    try:
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            use_pure=True,
            connection_timeout=10
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Check deals table
        print("\n1. DEALS TABLE")
        cursor.execute("SELECT COUNT(*) as count FROM deals")
        deals_count = cursor.fetchone()['count']
        print(f"   Total deals: {deals_count:,}")
        
        # Check most recent deals
        cursor.execute("SELECT dealid, title, store, created_at FROM deals ORDER BY created_at DESC LIMIT 5")
        recent_deals = cursor.fetchall()
        print("   Recent deals:")
        for deal in recent_deals:
            created = deal['created_at'].strftime("%Y-%m-%d %H:%M:%S") if deal['created_at'] else "N/A"
            print(f"   - {deal['dealid'][:20]}...: {deal['title'][:30]}... ({created})")
        
        # Check deal_filters table
        print("\n2. DEAL_FILTERS TABLE")
        cursor.execute("SELECT COUNT(*) as count FROM deal_filters")
        filters_count = cursor.fetchone()['count']
        print(f"   Total filters: {filters_count:,}")
        print(f"   Filters to deals ratio: {filters_count/deals_count*100:.1f}% (should be close to 100%)")
        
        # Check non-null fields
        cursor.execute("""
            SELECT 
                SUM(offer_type IS NOT NULL AND offer_type <> '') AS non_null_offer_type,
                SUM(condition_type IS NOT NULL AND condition_type <> '') AS non_null_condition,
                SUM(offer_status IS NOT NULL AND offer_status <> '') AS non_null_status,
                SUM(category_id IS NOT NULL) AS non_null_category_id,
                SUM(store_id IS NOT NULL) AS non_null_store_id,
                SUM(brand_id IS NOT NULL) AS non_null_brand_id,
                SUM(collection_id IS NOT NULL) AS non_null_collection_id
            FROM deal_filters
        """)
        non_null_counts = cursor.fetchone()
        print("   Non-null field counts:")
        for field, count in non_null_counts.items():
            if count is not None:
                print(f"   - {field}: {count:,} ({count/filters_count*100:.1f}%)")
        
        # Sample some filters
        cursor.execute("""
            SELECT df.dealid, df.offer_type, df.condition_type, df.events, df.offer_status, 
                   df.include_expired, df.category_id, df.store_id, df.brand_id, df.collection_id,
                   d.title
            FROM deal_filters df
            JOIN deals d ON df.dealid = d.dealid
            WHERE df.offer_type IS NOT NULL OR df.condition_type IS NOT NULL OR df.offer_status IS NOT NULL
            LIMIT 5
        """)
        sample_filters = cursor.fetchall()
        print("\n   Sample filters with non-null values:")
        for f in sample_filters:
            print(f"   - {f['dealid'][:20]}... ({f['title'][:20]}...)")
            print(f"     offer_type: {f['offer_type'] or 'NULL'}, condition: {f['condition_type'] or 'NULL'}, status: {f['offer_status'] or 'NULL'}")
            print(f"     category_id: {f['category_id'] or 'NULL'}, store_id: {f['store_id'] or 'NULL'}, brand_id: {f['brand_id'] or 'NULL'}")
        
        # Check related_deals table
        print("\n3. RELATED_DEALS TABLE")
        cursor.execute("SELECT COUNT(*) as count FROM related_deals")
        related_count = cursor.fetchone()['count']
        print(f"   Total related deals: {related_count:,}")
        
        # Check deals with related deals
        cursor.execute("""
            SELECT COUNT(DISTINCT dealid) as count FROM related_deals
        """)
        deals_with_related = cursor.fetchone()['count']
        print(f"   Deals with related deals: {deals_with_related:,} ({deals_with_related/deals_count*100:.1f}%)")
        
        # Check distribution of related deals
        cursor.execute("""
            SELECT COUNT(*) as related_count, COUNT(DISTINCT dealid) as deals_count
            FROM related_deals
            GROUP BY dealid
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)
        related_distribution = cursor.fetchall()
        if related_distribution:
            print("   Top deals by related count:")
            for r in related_distribution:
                print(f"   - {r['related_count']} related deals")
        
        # Check normalized tables
        print("\n4. NORMALIZED TABLES")
        cursor.execute("SELECT COUNT(*) as count FROM stores")
        stores_count = cursor.fetchone()['count']
        print(f"   Stores: {stores_count:,}")
        
        cursor.execute("SELECT COUNT(*) as count FROM categories")
        categories_count = cursor.fetchone()['count']
        print(f"   Categories: {categories_count:,}")
        
        cursor.execute("SELECT COUNT(*) as count FROM brands")
        brands_count = cursor.fetchone()['count']
        print(f"   Brands: {brands_count:,}")
        
        cursor.execute("SELECT COUNT(*) as count FROM collections")
        collections_count = cursor.fetchone()['count']
        print(f"   Collections: {collections_count:,}")
        
        cursor.execute("SELECT COUNT(*) as count FROM deal_images")
        images_count = cursor.fetchone()['count']
        print(f"   Deal images: {images_count:,}")
        
        # Summary
        print("\n" + "=" * 60)
        print("DATABASE VERIFICATION SUMMARY")
        print("=" * 60)
        
        # Calculate save ratio vs expected
        expected_deals = 200000  # Based on logs showing 360k extracted
        save_ratio = deals_count / expected_deals
        
        if deals_count < 10000:
            print("❌ CRITICAL: Very low deal count (<10,000)")
            print(f"   Only {deals_count:,} deals saved out of expected {expected_deals:,}")
            print(f"   Save ratio: {save_ratio:.1%} (should be close to 100%)")
            print("\n   SOLUTION: Run with FORCE_UPDATE=true and CLEAR_DATA=true")
        elif save_ratio < 0.5:
            print("⚠️ WARNING: Low save ratio (<50%)")
            print(f"   {deals_count:,} deals saved out of expected {expected_deals:,}")
            print(f"   Save ratio: {save_ratio:.1%} (should be close to 100%)")
            print("\n   SOLUTION: Run with FORCE_UPDATE=true")
        else:
            print(f"✅ GOOD: {deals_count:,} deals saved")
            print(f"   Save ratio: {save_ratio:.1%}")
        
        # Check filter ratio
        filter_ratio = filters_count / deals_count
        if filter_ratio < 0.9:
            print("\n❌ CRITICAL: Low filter ratio (<90%)")
            print(f"   Only {filters_count:,} filters for {deals_count:,} deals")
            print(f"   Filter ratio: {filter_ratio:.1%} (should be close to 100%)")
            print("\n   SOLUTION: Run with FORCE_UPDATE=true")
        else:
            print(f"\n✅ GOOD: {filters_count:,} filters populated")
            print(f"   Filter ratio: {filter_ratio:.1%}")
        
        # Check non-null fields in filters
        non_null_offer_type = non_null_counts['non_null_offer_type'] or 0
        offer_type_ratio = non_null_offer_type / filters_count if filters_count > 0 else 0
        if offer_type_ratio < 0.5:
            print("\n⚠️ WARNING: Low non-null offer_type ratio (<50%)")
            print(f"   Only {non_null_offer_type:,} non-null offer_types out of {filters_count:,} filters")
            print(f"   Non-null ratio: {offer_type_ratio:.1%} (should be higher)")
        else:
            print(f"\n✅ GOOD: {non_null_offer_type:,} non-null offer_types")
            print(f"   Non-null ratio: {offer_type_ratio:.1%}")
        
        # Final verdict
        if deals_count >= 10000 and filter_ratio >= 0.9 and offer_type_ratio >= 0.5:
            print("\n🎉 OVERALL: GOOD - Database looks healthy!")
            print("   - Deals saved: OK")
            print("   - Filters populated: OK")
            print("   - Non-null fields: OK")
            print("\n   You can share this with the client.")
        else:
            print("\n⚠️ OVERALL: NEEDS ATTENTION - Database issues detected")
            print("   Run with FORCE_UPDATE=true and CLEAR_DATA=true to fix.")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL error: {err}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())