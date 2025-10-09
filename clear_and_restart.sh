#!/bin/bash

echo "🧹 Clearing database and restarting scraper..."

# Stop any running containers
docker-compose down

# Clear the database
echo "🗑️  Clearing database..."
docker-compose exec mysql mysql -uroot -proot -e "DROP DATABASE IF EXISTS dealnews; CREATE DATABASE dealnews;"

# Set environment variables for fresh start
export CLEAR_DATA=true
export FORCE_UPDATE=true

# Start the scraper
echo "🚀 Starting fresh scraper run..."
docker-compose up scraper

echo "✅ Done! Check the logs for progress."
