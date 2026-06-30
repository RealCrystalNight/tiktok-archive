#!/bin/bash
# Full pipeline: scrape → build → ready to push
set -e

echo "=== TikTok Archive Pipeline ==="
echo ""

# Step 1: Scrape
echo "[1/2] Scraping videos..."
python3 scraper.py "${1:-canthinkyy}"

# Step 2: Build site
echo ""
echo "[2/2] Building site..."
python3 build.py

echo ""
echo "=== Done! ==="
echo "Preview:  cd site && python3 -m http.server 8000"
echo "Deploy:   git add . && git commit -m 'update' && git push"
