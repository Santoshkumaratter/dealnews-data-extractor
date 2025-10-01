#!/bin/bash

echo "🚀 DealNews Scraper - Laradock Integration Setup"
echo "================================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env-template .env
    echo "✅ .env file created!"
else
    echo "✅ .env file already exists"
fi

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "🐍 Python3 found, setting up database..."
    python3 setup_laradock_db.py
elif command -v python &> /dev/null; then
    echo "🐍 Python found, setting up database..."
    python setup_laradock_db.py
else
    echo "❌ Python not found! Please install Python first."
    exit 1
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure your Laradock is running: docker ps"
echo "2. Run the scraper: docker-compose up scraper"
echo "3. Check your data at: http://localhost:8081 (phpMyAdmin)"
echo ""
echo "✅ Ready to scrape DealNews!"
