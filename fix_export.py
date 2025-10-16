#!/usr/bin/env python3
"""
Fix Export Script
This script processes the exported deals.json file to:
1. Filter out navigation items
2. Keep only real deals
3. Create a clean export file
"""

import json
import os
import sys
from datetime import datetime

def clean_json_export():
    """Clean the JSON export to remove navigation items and keep only real deals"""
    print("🧹 Cleaning JSON export...")
    
    # Check if exports directory exists
    if not os.path.exists('exports'):
        print("❌ Exports directory not found!")
        return False
    
    # Check if deals.json exists
    json_file = 'exports/deals.json'
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found!")
        return False
    
    try:
        # Load JSON data line by line (safer for large files)
        deals = []
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Fix common JSON issues
            content = content.replace('}\n{', '},\n{')
            if not content.startswith('['):
                content = '[' + content
            if not content.endswith(']'):
                content = content + ']'
            
            # Try to parse the fixed content
            try:
                deals = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing error: {e}")
                # Try a different approach - read line by line
                print("Trying line-by-line parsing...")
                deals = []
                with open(json_file, 'r', encoding='utf-8') as f2:
                    for line in f2:
                        line = line.strip()
                        if line and line not in ['[', ']', ',']:
                            try:
                                # Remove trailing comma if present
                                if line.endswith(','):
                                    line = line[:-1]
                                # Add braces if missing
                                if not line.startswith('{'):
                                    line = '{' + line
                                if not line.endswith('}'):
                                    line = line + '}'
                                deal = json.loads(line)
                                deals.append(deal)
                            except:
                                pass
        
        print(f"📊 Total items loaded: {len(deals)}")
        
        # Filter criteria to identify real deals
        def is_real_deal(deal):
            # Skip navigation items
            if deal.get('dealid', '').startswith('nav-menu-'):
                return False
                
            # Skip empty deals
            if not deal.get('title') or deal.get('title') in ['No title found', 'Interests:']:
                return False
                
            # Skip navigation links
            skip_titles = [
                'Apple TV', 'Fubo TV', 'Peacock TV', 'About Us', 'Contact', 
                'Sign In', 'Register', 'Holiday Hours', 'Return Policy'
            ]
            if deal.get('title') in skip_titles:
                return False
                
            return True
        
        # Filter deals
        real_deals = [deal for deal in deals if is_real_deal(deal)]
        
        print(f"✅ Real deals found: {len(real_deals)}")
        
        # Save cleaned deals
        clean_file = f'exports/clean_deals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(clean_file, 'w', encoding='utf-8') as f:
            json.dump(real_deals, f, indent=2)
        
        print(f"💾 Cleaned deals saved to: {clean_file}")
        
        # Also save as CSV
        csv_file = clean_file.replace('.json', '.csv')
        export_to_csv(real_deals, csv_file)
        
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning JSON export: {e}")
        return False

def export_to_csv(deals, csv_file):
    """Export deals to CSV format"""
    try:
        # Get all possible fields from all deals
        fields = set()
        for deal in deals:
            fields.update(deal.keys())
        
        fields = sorted(list(fields))
        
        # Write CSV header and data
        with open(csv_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(','.join([f'"{field}"' for field in fields]) + '\n')
            
            # Write data rows
            for deal in deals:
                row = []
                for field in fields:
                    value = deal.get(field, '')
                    # Handle string values with commas and quotes
                    if isinstance(value, str):
                        value = value.replace('"', '""')  # Escape quotes
                        value = f'"{value}"'
                    elif isinstance(value, list):
                        value = f'"{str(value)}"'
                    else:
                        value = f'"{str(value)}"'
                    row.append(value)
                f.write(','.join(row) + '\n')
        
        print(f"💾 CSV export saved to: {csv_file}")
        return True
    except Exception as e:
        print(f"❌ Error exporting to CSV: {e}")
        return False

def fix_json_file():
    """Fix the JSON file directly"""
    print("🔧 Fixing JSON file...")
    
    json_file = 'exports/deals.json'
    if not os.path.exists(json_file):
        print(f"❌ {json_file} not found!")
        return False
    
    try:
        # Create a backup
        backup_file = f'exports/deals_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(json_file, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        print(f"✅ Backup created: {backup_file}")
        
        # Read the file and fix it
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix common JSON issues
        if not content.startswith('['):
            content = '[' + content
        
        # Find the last valid JSON object
        last_brace_pos = content.rfind('}')
        if last_brace_pos > 0:
            content = content[:last_brace_pos+1] + ']'
        else:
            content = content + ']'
        
        # Replace problematic sequences
        content = content.replace('}\n{', '},\n{')
        
        # Write the fixed content
        fixed_file = 'exports/deals_fixed.json'
        with open(fixed_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fixed JSON saved to: {fixed_file}")
        return fixed_file
        
    except Exception as e:
        print(f"❌ Error fixing JSON file: {e}")
        return False

def main():
    print("=" * 60)
    print("DealNews Scraper - Fix Export")
    print("=" * 60)
    
    # Fix JSON file first
    fixed_file = fix_json_file()
    
    # Clean JSON export
    if clean_json_export():
        print("\n✅ Export cleaning completed successfully!")
    else:
        print("\n❌ Export cleaning failed!")
        print("Trying alternative method...")
        
        # Try to extract deals manually
        try:
            deals = []
            json_file = 'exports/deals.json'
            with open(json_file, 'r', encoding='utf-8') as f:
                current_deal = {}
                for line in f:
                    line = line.strip()
                    if line.startswith('{'):
                        current_deal = {}
                    elif line.endswith('},') or line == '}':
                        if current_deal and 'dealid' in current_deal:
                            deals.append(current_deal.copy())
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().strip('"')
                        value = value.strip().strip(',').strip('"')
                        if key and value:
                            current_deal[key] = value
            
            print(f"📊 Extracted {len(deals)} deals manually")
            
            # Save the extracted deals
            manual_file = f'exports/manual_deals_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(manual_file, 'w', encoding='utf-8') as f:
                json.dump(deals, f, indent=2)
            
            print(f"💾 Manual extraction saved to: {manual_file}")
            
        except Exception as e:
            print(f"❌ Manual extraction failed: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()