#!/bin/bash

echo "🚀 Setting up DealNews Scraper with Laradock-style MySQL and phpMyAdmin"
echo "=================================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env-template .env
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Update .env for Laradock-style setup
echo "🔧 Configuring environment for Laradock-style setup..."
cat > .env << EOF
# DealNews Scraper Environment Configuration

# MySQL Configuration (Laradock-style)
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=dealnews

# Feature Flags
DISABLE_PROXY=true
DISABLE_MYSQL=false

# Data Management
FORCE_UPDATE=true
CLEAR_DATA=true
CAPTURE_MODE=full

# Scraper Configuration
MAX_DEALS=100000
DOWNLOAD_DELAY=3.0
CONCURRENT_REQUESTS=4
CONCURRENT_REQUESTS_PER_DOMAIN=2

# Logging Configuration
LOG_LEVEL=WARNING
EOF

echo "✅ Environment configured for Laradock-style setup"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p exports logs mysql-init

echo "✅ Directories created"

# Create MySQL initialization script
echo "🗄️ Creating MySQL initialization script..."
cat > mysql-init/01-init.sql << 'EOF'
-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS dealnews;

-- Use the database
USE dealnews;

-- Create tables
CREATE TABLE IF NOT EXISTS deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(50) UNIQUE,
    recid VARCHAR(50),
    url TEXT,
    title TEXT,
    price VARCHAR(100),
    promo TEXT,
    category VARCHAR(100),
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
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS stores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_name VARCHAR(100) UNIQUE,
    store_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_store_name (store_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(100) UNIQUE,
    category_url TEXT,
    category_title VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS brands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    brand_name VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_brand_name (brand_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS collections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    collection_name VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_collection_name (collection_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS deal_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(50),
    imageurl TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid),
    FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS deal_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(50),
    category_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_deal_category (dealid, category_id),
    INDEX idx_dealid (dealid),
    INDEX idx_category_id (category_id),
    FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS related_deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(50),
    related_dealid VARCHAR(50),
    related_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid),
    INDEX idx_related_dealid (related_dealid),
    FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS deal_filters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(50),
    start_date DATE,
    max_price DECIMAL(10,2),
    category_id INT,
    store_id INT,
    brand_id INT,
    offer_type VARCHAR(50),
    popularity_rank INT,
    collection_id INT,
    condition_type VARCHAR(50),
    events VARCHAR(100),
    offer_status VARCHAR(50),
    include_expired BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid),
    INDEX idx_offer_type (offer_type),
    INDEX idx_condition_type (condition_type),
    INDEX idx_offer_status (offer_status),
    UNIQUE KEY unique_deal_filter (dealid),
    FOREIGN KEY (dealid) REFERENCES deals(dealid) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE SET NULL,
    FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE SET NULL,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
EOF

echo "✅ MySQL initialization script created"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Start the services: docker-compose up -d"
echo "2. Wait for MySQL to initialize (about 30 seconds)"
echo "3. Run the scraper: docker-compose up scraper"
echo "4. Check your data at: http://localhost:8081 (phpMyAdmin)"
echo ""
echo "🔧 Services included:"
echo "- MySQL 8.0 (port 3306)"
echo "- phpMyAdmin (port 8081)"
echo "- DealNews Scraper"
echo ""
echo "✅ Ready to use!"
