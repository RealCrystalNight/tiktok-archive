# TikTok Archive

Archived TikTok videos from **@canthinkyy** — full quality, with comments, descriptions, and metadata.

## Structure

```
data/          # JSON metadata per video (title, description, comments, stats)
videos/        # Full quality MP4 downloads
site/          # Generated static HTML (TikTok-like UI)
scraper.py     # Fetches videos + metadata via yt-dlp
build.py       # Generates the static site from data/
```

## Usage

```bash
# 1. Scrape all videos from a TikTok user
python3 scraper.py canthinkyy

# 2. Generate the static site
python3 build.py

# 3. Preview locally
cd site && python3 -m http.server 8000

# 4. Push to GitHub (videos served via raw.githack.com)
git add . && git commit -m "update archive" && git push
```

## How it works

- **yt-dlp** downloads full-quality MP4s + extracts comments and metadata
- **build.py** generates a static HTML site with TikTok's dark UI aesthetic
- Videos are served via **raw.githack.com** CDN from the GitHub repo
- Each video has its own page with player, description, comments, and spinning music disk
- Profile photos link to actual TikTok profiles (not local)

## Updating

Re-run `scraper.py` to fetch new videos, then `build.py` to regenerate the site.
Only new/changed videos are re-downloaded.
