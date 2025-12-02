# Client Requirements → Database Mapping

## Overview
This document maps each field from the client's PDF/image requirements to the corresponding MySQL database table and column where the data is saved.

---

## 📊 MAIN DEALS TABLE (`deals`)

| Client PDF Field | Database Table | Database Column | Data Type | Description |
|-----------------|----------------|-----------------|-----------|-------------|
| **Deal ID** | `deals` | `dealid` | VARCHAR(50) | Unique deal identifier (e.g., "deal_4432890841138584818") |
| **Rec ID** | `deals` | `recid` | VARCHAR(50) | Recommendation ID (if available) |
| **URL** | `deals` | `url` | TEXT | Source URL from dealnews.com |
| **Title** | `deals` | `title` | TEXT | Deal title/headline |
| **Price** | `deals` | `price` | VARCHAR(100) | Product price (if available) |
| **Promo Code** | `deals` | `promo` | TEXT | Promotional code (if available) |
| **Category** | `deals` | `category` | VARCHAR(255) | Primary category (e.g., "Clothing & Accessories") |
| **Store** | `deals` | `store` | VARCHAR(100) | Store/vendor name (e.g., "Best Buy", "Amazon") |
| **Deal** | `deals` | `deal` | TEXT | Deal text (e.g., "Up to 80% off", "1-Cent Deals") |
| **Deal Plus** | `deals` | `dealplus` | TEXT | Additional deal info (e.g., "free shipping w/ Prime") |
| **Deal Link** | `deals` | `deallink` | TEXT | Direct link to the deal/offer |
| **Deal Text** | `deals` | `dealtext` | TEXT | Deal description text (first 200 chars) |
| **Deal Hover** | `deals` | `dealhover` | TEXT | Hover text (usually same as title) |
| **Published** | `deals` | `published` | VARCHAR(100) | Published timestamp (e.g., "Best Buy · 53 days ago") |
| **Popularity** | `deals` | `popularity` | VARCHAR(50) | Popularity rating (e.g., "5/5", "3/8") |
| **Staff Pick** | `deals` | `staffpick` | VARCHAR(10) | Staff pick status (e.g., "Staff Pick") |
| **Detail** | `deals` | `detail` | TEXT | Full deal description/details |
| **Raw HTML** | `deals` | `raw_html` | LONGTEXT | Raw HTML snapshot of the deal page |
| **Created At** | `deals` | `created_at` | TIMESTAMP | Auto-generated timestamp when record is created |
| **Updated At** | `deals` | `updated_at` | TIMESTAMP | Auto-generated timestamp when record is updated |

---

## 🖼️ DEAL IMAGES TABLE (`deal_images`)

| Client PDF Field | Database Table | Database Column | Data Type | Description |
|-----------------|----------------|-----------------|-----------|-------------|
| **Deal Images** | `deal_images` | `imageurl` | TEXT | Image URL for the deal (one row per image) |
| **Deal ID** (Foreign) | `deal_images` | `dealid` | VARCHAR(50) | Links to `deals.dealid` |
| **Created At** | `deal_images` | `created_at` | TIMESTAMP | Auto-generated timestamp |

**Note:** One deal can have multiple images. Each image is stored as a separate row in `deal_images` table with the same `dealid`.

---

## 📁 DEAL CATEGORIES TABLE (`deal_categories`)

| Client PDF Field | Database Table | Database Column | Data Type | Description |
|-----------------|----------------|-----------------|-----------|-------------|
| **Categories** | `deal_categories` | `category_name` | VARCHAR(255) | Category name (e.g., "Electronics", "Clothing & Accessories") |
| **Category ID** | `deal_categories` | `category_id` | VARCHAR(100) | Category identifier (if available) |
| **Category URL** | `deal_categories` | `category_url` | TEXT | Category page URL |
| **Category Title** | `deal_categories` | `category_title` | VARCHAR(255) | Category title (if available) |
| **Deal ID** (Foreign) | `deal_categories` | `dealid` | VARCHAR(50) | Links to `deals.dealid` |
| **Created At** | `deal_categories` | `created_at` | TIMESTAMP | Auto-generated timestamp |

**Note:** One deal can have multiple categories. Each category is stored as a separate row in `deal_categories` table with the same `dealid`.

---

## 🔗 RELATED DEALS TABLE (`related_deals`)

| Client PDF Field | Database Table | Database Column | Data Type | Description |
|-----------------|----------------|-----------------|-----------|-------------|
| **Related Deals** | `related_deals` | `relatedurl` | TEXT | URL of related deal (one row per related deal) |
| **Deal ID** (Foreign) | `related_deals` | `dealid` | VARCHAR(50) | Links to `deals.dealid` |
| **Created At** | `related_deals` | `created_at` | TIMESTAMP | Auto-generated timestamp |

**Note:** One deal can have multiple related deals. Each related deal URL is stored as a separate row in `related_deals` table with the same `dealid`.

---

## 📋 SUMMARY

### Tables Structure:
1. **`deals`** - Main table containing all deal information (19 columns)
2. **`deal_images`** - Stores multiple images per deal (3 columns)
3. **`deal_categories`** - Stores multiple categories per deal (6 columns)
4. **`related_deals`** - Stores related deal URLs per deal (3 columns)

### Relationships:
- `deal_images.dealid` → `deals.dealid` (One-to-Many)
- `deal_categories.dealid` → `deals.dealid` (One-to-Many)
- `related_deals.dealid` → `deals.dealid` (One-to-Many)

### Unique Constraints:
- `deals.dealid` - UNIQUE (prevents duplicate deals)
- `deal_images(dealid, imageurl)` - UNIQUE (prevents duplicate images per deal)
- `deal_categories(dealid, category_name)` - UNIQUE (prevents duplicate categories per deal)
- `related_deals(dealid, relatedurl)` - UNIQUE (prevents duplicate related deals per deal)

---

## ✅ Data Coverage Status

| Field | Coverage | Status |
|-------|----------|--------|
| `dealid` | 100% | ✅ Complete |
| `title` | 100% | ✅ Complete |
| `url` | 100% | ✅ Complete |
| `deallink` | 100% | ✅ Complete |
| `dealtext` | 100% | ✅ Complete |
| `dealhover` | 100% | ✅ Complete |
| `detail` | 100% | ✅ Complete |
| `raw_html` | 100% | ✅ Complete |
| `published` | 94.0% | ✅ Good |
| `category` | 84.1% | ✅ Good |
| `store` | 81.5% | ✅ Good |
| `deal` | 50.5% | ⚠️ Medium |
| `dealplus` | 20.7% | ⚠️ Low |
| `price` | 4.9% | ⚠️ Low |
| `popularity` | 0.3% | ⚠️ Low |
| `staffpick` | 4.6% | ⚠️ Low (expected - not all deals are staff picks) |
| `recid` | 0% | ⚠️ Not available |
| `promo` | 0% | ⚠️ Not available |

---

## 📝 Notes

1. **Primary Category**: The main category is stored in `deals.category`, while all categories (including multiple) are stored in `deal_categories` table.

2. **Images**: All deal images are stored separately in `deal_images` table. One deal can have multiple images.

3. **Categories**: All deal categories are stored separately in `deal_categories` table. One deal can have multiple categories.

4. **Related Deals**: Related deals are extracted from detail pages and stored in `related_deals` table. This table populates as the scraper visits more detail pages.

5. **Auto-generated Fields**: `created_at` and `updated_at` are automatically managed by MySQL.

6. **Data Validation**: 
   - HTML entities are cleaned from category fields
   - JSON data is prevented from being saved in `deal` field
   - Invalid categories (like "sponsored", "expired") are filtered out
   - Duplicate prevention is handled by UNIQUE constraints

---

**Last Updated:** 2025-11-28
**Database:** MySQL (dealnews)
**Total Deals:** 3,195+ (as of last check)





