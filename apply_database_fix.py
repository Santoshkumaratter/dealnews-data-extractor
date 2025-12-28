#!/usr/bin/env python3
"""
Apply database fix: Add unique constraint on deals.url
"""

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def apply_fix():
    """Apply the database fix"""
    
    print("=" * 80)
    print("APPLYING DATABASE FIX: Adding unique constraint on deals.url")
    print("=" * 80)
    print()
    
    conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'root'),
        database=os.getenv('MYSQL_DATABASE', 'dealnews')
    )
    cursor = conn.cursor(dictionary=True)
    
    # Step 1: Check for existing duplicates
    print("Step 1: Checking for duplicate URLs...")
    cursor.execute("""
        SELECT url, COUNT(*) as count
        FROM deals
        WHERE url IS NOT NULL
        GROUP BY url
        HAVING count > 1
    """)
    duplicates = cursor.fetchall()
    
    if duplicates:
        print(f"⚠️  Found {len(duplicates)} duplicate URLs")
        print(f"   Removing duplicates (keeping first occurrence)...")
        
        # Remove duplicates
        cursor.execute("""
            DELETE d1 FROM deals d1
            INNER JOIN deals d2 
            WHERE d1.id > d2.id AND d1.url = d2.url AND d1.url IS NOT NULL
        """)
        conn.commit()
        print(f"✅ Removed {cursor.rowcount} duplicate rows")
    else:
        print("✅ No duplicate URLs found")
    
    print()
    
    # Step 2: Check if constraint already exists
    print("Step 2: Checking if unique constraint already exists...")
    cursor.execute("SHOW CREATE TABLE deals")
    create_table = cursor.fetchone()
    create_sql = create_table['Create Table'] if 'Create Table' in create_table else str(create_table)
    
    if 'UNIQUE KEY `unique_url`' in create_sql or 'UNIQUE KEY unique_url' in create_sql:
        print("✅ Unique constraint already exists")
    else:
        print("⚠️  Unique constraint does not exist")
        print("   Adding unique constraint...")
        
        try:
            cursor.execute("""
                ALTER TABLE deals
                ADD CONSTRAINT unique_url UNIQUE (url)
            """)
            conn.commit()
            print("✅ Successfully added unique constraint on deals.url")
        except mysql.connector.Error as err:
            if "Duplicate entry" in str(err):
                print(f"❌ Failed to add constraint due to duplicate entries: {err}")
                print("   Please run this script again to remove duplicates first")
            else:
                print(f"❌ Failed to add constraint: {err}")
    
    print()
    
    # Step 3: Verify the constraint
    print("Step 3: Verifying the constraint...")
    cursor.execute("SHOW CREATE TABLE deals")
    create_table = cursor.fetchone()
    create_sql = create_table['Create Table'] if 'Create Table' in create_table else str(create_table)
    
    if 'UNIQUE KEY `unique_url`' in create_sql or 'UNIQUE KEY unique_url' in create_sql:
        print("✅ Unique constraint verified successfully")
    else:
        print("❌ Unique constraint not found after applying fix")
    
    print()
    print("=" * 80)
    print("DATABASE FIX COMPLETED")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    try:
        apply_fix()
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        import traceback
        traceback.print_exc()
