#!/bin/bash
# Fix and verify DealNews scraper

echo "🔧 DealNews Scraper - Fix and Verify"
echo "==================================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Stop any running containers
echo "🛑 Stopping any running containers..."
docker-compose down -v || docker compose down -v

# Remove old containers and images
echo "🧹 Cleaning up old containers and images..."
docker ps -a | grep dealnews_scraper | awk '{print $1}' | xargs -I{} docker rm -f {} 2>/dev/null || true
docker images | grep dealnews-data-extractor | awk '{print $3}' | xargs -I{} docker rmi -f {} 2>/dev/null || true
docker builder prune -f

# Set up environment
echo "🔧 Setting up environment..."
cp .env-template .env 2>/dev/null || cp env.example .env 2>/dev/null || echo "⚠️ No .env template found"

# Force refresh
echo "🔄 Setting FORCE_UPDATE=true and CLEAR_DATA=true..."
sed -i.bak 's/FORCE_UPDATE=.*/FORCE_UPDATE=true/' .env 2>/dev/null || echo "FORCE_UPDATE=true" >> .env
sed -i.bak 's/CLEAR_DATA=.*/CLEAR_DATA=true/' .env 2>/dev/null || echo "CLEAR_DATA=true" >> .env
rm -f .env.bak 2>/dev/null

# Create directories
echo "📁 Creating directories..."
mkdir -p logs dumps

# Rebuild with no cache
echo "🏗️ Rebuilding with no cache..."
docker-compose build --no-cache scraper || docker compose build --no-cache scraper

# Start the scraper
echo "🚀 Starting scraper..."
docker-compose up -d scraper || docker compose up -d scraper

# Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Verify container is running
CONTAINER_ID=$(docker ps -q -f name=dealnews_scraper)
if [ -z "$CONTAINER_ID" ]; then
    echo "❌ Container not running. Check docker-compose logs."
    exit 1
fi

# Verify the container has the updated code
echo "🔍 Verifying container has updated code..."
echo "Checking for 'already exists, skipping' string (should be gone):"
docker exec $CONTAINER_ID sh -c "grep -n 'already exists, skipping' -R /app || echo '✅ OK: String not found'"

echo "Checking for 'deal_' strategy in spider:"
docker exec $CONTAINER_ID sh -c "grep -n 'deal_' /app/dealnews_scraper/spiders/dealnews_spider.py | head -n3"

echo "Checking for 'auto-id' (should NOT exist):"
docker exec $CONTAINER_ID sh -c "grep -n 'auto-id' -R /app || echo '✅ OK: No auto-id found'"

echo "Checking for ON DUPLICATE KEY UPDATE in pipeline:"
docker exec $CONTAINER_ID sh -c "grep -n 'ON DUPLICATE KEY UPDATE' /app/dealnews_scraper/normalized_pipeline.py | head -n2"

# Stream logs for a while
echo "📜 Streaming logs for 60 seconds..."
timeout 60 docker logs -f dealnews_scraper || true

# Copy logs
echo "📋 Copying logs..."
docker cp dealnews_scraper:/app/dealnews_scraper.log logs/dealnews_scraper.log || echo "⚠️ Could not copy log"

# Dump database
echo "💾 Dumping database..."
mysqldump -h localhost -P 3306 -uroot -proot dealnews > dumps/dealnews_$(date +%F_%H-%M-%S).sql 2>/dev/null || echo "⚠️ Could not dump database"

# Run verification
echo "🔍 Running database verification..."
python3 verify_db.py

echo "✅ Done! Check the verification results above."
echo "If verification failed, try running the scraper for longer before verifying."
echo "You can stream logs with: docker logs -f dealnews_scraper"
