#!/bin/bash
# Optimized background scraper with minimal logging
# This script runs the scraper in the background with reduced logging to improve performance

cd "$(dirname "$0")"

# Kill existing scraper if running
if [ -f scraper.pid ]; then
    OLD_PID=$(cat scraper.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing scraper (PID: $OLD_PID)..."
        kill $OLD_PID
        sleep 2
    fi
    rm -f scraper.pid
fi

# Clean up old log files to prevent performance issues
echo "Cleaning up old log files..."
rm -f error.log output.log scraper_output.log

# Set LOG_LEVEL to WARNING for minimal logging (only warnings and errors)
export LOG_LEVEL=WARNING

# Run scraper in background with minimal logging
echo "Starting scraper in background with minimal logging..."
nohup python3 run_scraper.py > /dev/null 2>&1 &

# Save PID
echo $! > scraper.pid
echo "Scraper started with PID: $(cat scraper.pid)"
echo "Log level: WARNING (minimal logging for best performance)"
echo ""
echo "To check status:"
echo "  ps -p \$(cat scraper.pid)"
echo ""
echo "To check errors only:"
echo "  tail -f error.log"
echo ""
echo "To stop scraper:"
echo "  kill \$(cat scraper.pid)"
