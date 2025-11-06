#!/bin/bash
# Setup cron job to run scraper daily
# This script sets up a daily cron job to run the DealNews scraper

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LOG="$SCRIPT_DIR/logs/cron.log"
CRON_ERROR_LOG="$SCRIPT_DIR/logs/cron_error.log"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Create the cron job command
# Run daily at 2 AM
CRON_SCHEDULE="0 2 * * *"
CRON_COMMAND="cd $SCRIPT_DIR && /usr/bin/python3 $SCRIPT_DIR/run_scraper.py >> $CRON_LOG 2>> $CRON_ERROR_LOG"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_scraper.py"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "run_scraper.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $CRON_COMMAND") | crontab -

echo "✅ Cron job setup complete!"
echo ""
echo "Schedule: Daily at 2:00 AM"
echo "Log file: $CRON_LOG"
echo "Error log: $CRON_ERROR_LOG"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"
echo ""
echo "To test immediately: python3 $SCRIPT_DIR/run_scraper.py"

