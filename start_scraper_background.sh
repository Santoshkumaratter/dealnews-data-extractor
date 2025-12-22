#!/bin/bash

# Run scraper in background using nohup
# Redirects stdout (regular output) to output.log
# Redirects stderr (errors/logs) to error.log
# The '&' at the end runs it in background

nohup python3 run_scraper.py > output.log 2> error.log &

echo "==================================================="
echo "🚀 Scraper started in background!"
echo "PID: $!"
echo "==================================================="
echo "Logs will be saved to:"
echo "  - Standard Output: output.log"
echo "  - Errors & Logs:   error.log"
echo ""
echo "To check progress, run:"
echo "  tail -f error.log"
echo "==================================================="
