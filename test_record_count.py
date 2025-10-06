#!/usr/bin/env python3
"""
Test script to count how many records the improved scraper can extract
This script runs the scraper and counts the records saved
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

def count_json_records():
    """Count records in the exported JSON file"""
    json_file = Path("exports/deals.json")
    if not json_file.exists():
        return 0
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return 0

def count_csv_records():
    """Count records in the exported CSV file"""
    csv_file = Path("exports/deals.csv")
    if not csv_file.exists():
        return 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Subtract 1 for header row
            return max(0, len(lines) - 1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return 0

def run_scraper_test():
    """Run the scraper and count records"""
    print("=" * 60)
    print("Testing Improved DealNews Scraper - Record Count")
    print("=" * 60)
    
    # Clear previous exports (with error handling)
    try:
        if Path("exports/deals.json").exists():
            Path("exports/deals.json").unlink()
    except PermissionError:
        print("Note: Could not delete existing deals.json (file in use)")
    
    try:
        if Path("exports/deals.csv").exists():
            Path("exports/deals.csv").unlink()
    except PermissionError:
        print("Note: Could not delete existing deals.csv (file in use)")
    
    print("Starting scraper test...")
    print("Note: This will run without database (MySQL disabled)")
    print()
    
    # Set environment variables to disable MySQL and enable exports
    env = os.environ.copy()
    env['DISABLE_MYSQL'] = 'true'  # Disable MySQL to avoid connection errors
    env['CLEAR_DATA'] = 'false'
    env['FORCE_UPDATE'] = 'false'
    
    start_time = time.time()
    
    try:
        # Run the scraper with a timeout
        print("Running scraper for 2 minutes to test record extraction...")
        result = subprocess.run([
            sys.executable, '-m', 'scrapy', 'crawl', 'dealnews',
            '-L', 'INFO',
            '-s', 'CLOSESPIDER_TIMEOUT=120'  # Stop after 2 minutes
        ], env=env, cwd=Path(__file__).parent, timeout=130)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\nScraper completed in {duration:.1f} seconds")
        
        # Count records
        json_count = count_json_records()
        csv_count = count_csv_records()
        
        print("\n" + "=" * 60)
        print("RECORD COUNT RESULTS")
        print("=" * 60)
        print(f"JSON Records: {json_count}")
        print(f"CSV Records: {csv_count}")
        print(f"Duration: {duration:.1f} seconds")
        
        if json_count > 0:
            rate = json_count / duration
            print(f"Extraction Rate: {rate:.1f} records/second")
            
            # Estimate full run
            estimated_full = json_count * (3600 / duration)  # Estimate for 1 hour
            print(f"Estimated 1-hour run: {estimated_full:.0f} records")
        
        # Show sample of extracted data
        if json_count > 0:
            print(f"\nSample of extracted data:")
            try:
                with open("exports/deals.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data:
                        sample = data[0]
                        print(f"  Deal ID: {sample.get('dealid', 'N/A')}")
                        print(f"  Title: {sample.get('title', 'N/A')[:50]}...")
                        print(f"  Store: {sample.get('store', 'N/A')}")
                        print(f"  Price: {sample.get('price', 'N/A')}")
            except Exception as e:
                print(f"  Error reading sample: {e}")
        
        return json_count
        
    except subprocess.TimeoutExpired:
        print("Scraper timed out after 2 minutes")
        json_count = count_json_records()
        csv_count = count_csv_records()
        print(f"\nRecords extracted before timeout:")
        print(f"JSON Records: {json_count}")
        print(f"CSV Records: {csv_count}")
        return json_count
        
    except Exception as e:
        print(f"Error running scraper: {e}")
        return 0

def main():
    """Main function"""
    print("This test will run the improved scraper for 2 minutes")
    print("to see how many records it can extract.")
    print()
    
    # Auto-run the test
    record_count = run_scraper_test()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if record_count > 737:
        print(f"SUCCESS: Extracted {record_count} records (vs 737 before)")
        print("The improvements are working!")
    elif record_count > 0:
        print(f"PARTIAL: Extracted {record_count} records")
        print("Some improvement, but may need more optimization")
    else:
        print("ISSUE: No records extracted")
        print("Check the logs for errors")

if __name__ == "__main__":
    main()
