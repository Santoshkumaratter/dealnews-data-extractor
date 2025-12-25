-- Updated schema with client feedback
-- Main deals table with category_id for joining
CREATE TABLE IF NOT EXISTS deals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dealid VARCHAR(50) UNIQUE NOT NULL,
  recid VARCHAR(50),
  url TEXT,
  title TEXT,
  price VARCHAR(100),
  promo TEXT,
  category VARCHAR(255),
  category_id VARCHAR(100),
  store VARCHAR(100),
  deal TEXT,
  dealplus TEXT,
  deallink TEXT,
  dealtext TEXT,
  dealhover TEXT,
  published VARCHAR(100),
  popularity VARCHAR(50),
  staffpick VARCHAR(10),
  detail TEXT,
  raw_html LONGTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_dealid (dealid),
  INDEX idx_created_at (created_at),
  INDEX idx_store (store),
  INDEX idx_category (category),
  INDEX idx_category_id (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Categories lookup table (unique category_id)
-- This is a normalized table - one row per unique category
CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  category_id VARCHAR(100) UNIQUE NOT NULL,
  category_name VARCHAR(255),
  category_url TEXT,
  category_description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category_id (category_id),
  INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Deal images table (multiple images per deal)
-- Unique constraint on (dealid, imageurl) prevents duplicate images
CREATE TABLE IF NOT EXISTS deal_images (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dealid VARCHAR(50) NOT NULL,
  imageurl TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_deal_image (dealid, imageurl(255)),
  INDEX idx_dealid (dealid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Related deals table (multiple related deals per deal)
-- Unique constraint on (dealid, relatedurl) prevents duplicate related deals
CREATE TABLE IF NOT EXISTS related_deals (
  id INT AUTO_INCREMENT PRIMARY KEY,
  dealid VARCHAR(50) NOT NULL,
  relatedurl TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unique_related_deal (dealid, relatedurl(255)),
  INDEX idx_dealid (dealid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
