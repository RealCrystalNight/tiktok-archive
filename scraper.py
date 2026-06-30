#!/usr/bin/env python3
"""
TikTok Archive Scraper
Uses TikWM API for metadata (avatar, stats, music) + yt-dlp for full-quality downloads.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VIDEOS_DIR = BASE_DIR / "videos"
COVERS_DIR = BASE_DIR / "covers"

# Config
TIKTOK_USER = "canthinkyy"
CDN_BASE = "https://www.tikwm.com"


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    VIDEOS_DIR.mkdir(exist_ok=True)
    COVERS_DIR.mkdir(exist_ok=True)


def tikwm_post(endpoint: str, params: dict) -> dict | None:
    """Make a POST request to TikWM API."""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        f"{CDN_BASE}{endpoint}",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [!] TikWM API error: {e}")
        return None


def abs_url(path: str) -> str:
    """Convert relative TikWM path to absolute URL."""
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return f"{CDN_BASE}{path}"


def get_user_videos(username: str) -> list[dict]:
    """Fetch all video metadata for a user via TikWM."""
    print(f"[*] Fetching videos for @{username} via TikWM...")
    all_videos = []
    cursor = ""

    while True:
        params = {"unique_id": username, "count": 30}
        if cursor:
            params["cursor"] = cursor

        resp = tikwm_post("/api/user/posts", params)
        if not resp or resp.get("code") != 0:
            print(f"[!] Failed to fetch videos: {resp}")
            break

        videos = resp.get("data", {}).get("videos", [])
        if not videos:
            break

        all_videos.extend(videos)
        print(f"  [>] Got {len(videos)} videos (total: {len(all_videos)})")

        if not resp["data"].get("hasMore"):
            break
        cursor = resp["data"].get("cursor", "")
        time.sleep(1)

    print(f"[+] Found {len(all_videos)} videos total")
    return all_videos


def get_video_detail(video_url: str) -> dict | None:
    """Get full video metadata including author avatar via TikWM."""
    resp = tikwm_post("/api/", {"url": video_url, "web": "1", "hd": "1"})
    if not resp or resp.get("code") != 0:
        return None
    return resp.get("data")


def download_cover(url: str, video_id: str) -> str:
    """Download cover image locally to avoid CDN URL expiry."""
    if not url:
        return ""
    ext = "webp" if ".webp" in url else "jpeg"
    out = str(COVERS_DIR / f"{video_id}.{ext}")
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return f"covers/{video_id}.{ext}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            with open(out, "wb") as f:
                f.write(resp.read())
        return f"covers/{video_id}.{ext}"
    except Exception as e:
        print(f"  [!] Cover download failed: {e}")
        return ""


def tiktok_api_get(endpoint: str, params: dict) -> dict | None:
    """Make a GET request to TikTok's hidden API."""
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://www.tiktok.com/api/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [!] TikTok API error: {e}")
        return None


def get_comments(video_url: str, video_id: str) -> list[dict]:
    """Fetch all comments + replies via TikTok's hidden API."""
    print(f"  [>] Fetching comments...")
    all_comments = []
    cursor = 0

    while True:
        resp = tiktok_api_get("comment/list/", {
            "aid": 1988, "aweme_id": video_id, "count": 50, "cursor": cursor
        })
        if not resp:
            break

        comments = resp.get("comments", [])
        if not comments:
            break

        for c in comments:
            comment = {
                "id": c.get("cid", ""),
                "text": c.get("text", ""),
                "likes": c.get("digg_count", 0),
                "user": c.get("user", {}).get("unique_id", ""),
                "nickname": c.get("user", {}).get("nickname", ""),
                "avatar": (c.get("user", {}).get("avatar_thumb", {}) or {}).get("url_list", [""])[0],
                "reply_count": c.get("reply_comment_total", 0),
                "replies": [],
            }

            # Fetch replies
            if comment["reply_count"] > 0:
                reply_cursor = 0
                while True:
                    rresp = tiktok_api_get("comment/list/reply/", {
                        "aid": 1988, "comment_id": comment["id"],
                        "item_id": video_id, "count": 50, "cursor": reply_cursor,
                    })
                    if not rresp:
                        break
                    replies = rresp.get("comments", [])
                    if not replies:
                        break
                    for r in replies:
                        comment["replies"].append({
                            "id": r.get("cid", ""),
                            "text": r.get("text", ""),
                            "likes": r.get("digg_count", 0),
                            "user": r.get("user", {}).get("unique_id", ""),
                            "nickname": r.get("user", {}).get("nickname", ""),
                            "avatar": (r.get("user", {}).get("avatar_thumb", {}) or {}).get("url_list", [""])[0],
                        })
                    if not rresp.get("has_more"):
                        break
                    reply_cursor += 50
                    time.sleep(0.3)

                print(f"    [+] {comment['reply_count']} replies for @{comment['user']}")
                time.sleep(0.3)

            all_comments.append(comment)

        print(f"    [>] {len(all_comments)} comments so far...")

        if not resp.get("has_more"):
            break
        cursor += 50
        time.sleep(0.5)

    print(f"  [+] {len(all_comments)} comments")
    return all_comments


def download_video(video_url: str, video_id: str) -> str | None:
    """Download full-quality video via yt-dlp."""
    output_path = str(VIDEOS_DIR / f"{video_id}.mp4")
    if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
        print(f"  [>] Already downloaded: {video_id}.mp4")
        return f"videos/{video_id}.mp4"

    print(f"  [>] Downloading full quality: {video_id}")
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-warnings",
        "--no-check-certificates",
        "-o", output_path,
        video_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  [!] Download failed: {result.stderr[:200]}")
        return None
    return f"videos/{video_id}.mp4"


def save_video_data(video_meta: dict, detail: dict | None, local_index: int) -> dict:
    """Build and save clean video data JSON."""
    vid = video_meta["video_id"]

    # Merge TikWM list data with detail data
    author = {}
    if detail and detail.get("author"):
        author = detail["author"]
    elif video_meta.get("author"):
        author = video_meta["author"]

    # Build clean data
    # Download cover locally (TikTok CDN URLs expire)
    cover_url = abs_url(video_meta.get("cover", ""))
    local_cover = download_cover(cover_url, vid)

    vdata = {
        "id": vid,
        "title": video_meta.get("title", "") or f"TikTok video #{vid}",
        "description": video_meta.get("title", ""),
        "upload_date": "",  # TikWM doesn't provide this in list
        "duration": video_meta.get("duration", 0),
        "view_count": video_meta.get("play_count", 0),
        "like_count": video_meta.get("digg_count", 0),
        "comment_count": video_meta.get("comment_count", 0),
        "share_count": video_meta.get("share_count", 0),
        "save_count": video_meta.get("collect_count", 0),
        "thumbnail": local_cover or cover_url,
        "origin_cover": abs_url(video_meta.get("origin_cover", "")),
        "dynamic_cover": abs_url(video_meta.get("ai_dynamic_cover", "")),
        "webpage_url": f"https://www.tiktok.com/@{author.get('unique_id', 'unknown')}/video/{vid}",
        "track": (video_meta.get("music_info") or {}).get("title", ""),
        "artist": (video_meta.get("music_info") or {}).get("author", ""),
        "music_url": abs_url((video_meta.get("music_info") or {}).get("play", "")),
        "music_cover": abs_url((video_meta.get("music_info") or {}).get("cover", "")),
        "uploader": author.get("nickname", author.get("unique_id", "unknown")),
        "uploader_id": author.get("unique_id", "unknown"),
        "uploader_url": f"https://www.tiktok.com/@{author.get('unique_id', 'unknown')}",
        "uploader_avatar": abs_url(author.get("avatar", "")),
        "hd_url": abs_url(video_meta.get("hdplay", "")),
        "sd_url": abs_url(video_meta.get("play", "")),
        "wm_url": abs_url(video_meta.get("wmplay", "")),
        "local_index": local_index,
    }

    # Save
    data_file = DATA_DIR / f"{vid}.json"
    with open(data_file, "w") as f:
        json.dump(vdata, f, indent=2)

    return vdata


def save_profile(username: str, videos: list[dict]):
    """Save profile data from first video's author info."""
    if not videos:
        return

    first = videos[0]
    avatar_url = first.get("uploader_avatar", "")

    # Download avatar locally
    local_avatar = ""
    if avatar_url:
        local_avatar = download_cover(avatar_url, "profile_avatar")
        if not local_avatar and avatar_url:
            local_avatar = avatar_url  # fallback to remote

    profile = {
        "username": username,
        "nickname": first.get("uploader", username),
        "avatar": local_avatar or avatar_url,
        "video_count": len(videos),
        "last_updated": datetime.now().isoformat(),
    }

    with open(DATA_DIR / "profile.json", "w") as f:
        json.dump(profile, f, indent=2)


def main():
    ensure_dirs()
    username = TIKTOK_USER
    if len(sys.argv) > 1:
        username = sys.argv[1]

    print(f"=== TikTok Archive Scraper ===")
    print(f"Target: @{username}\n")

    # Step 1: Get all video metadata from TikWM
    video_list = get_user_videos(username)
    if not video_list:
        print("[!] No videos found.")
        return

    # Step 2: Process each video
    all_videos = []
    for i, vm in enumerate(video_list, 1):
        vid = vm["video_id"]
        tiktok_url = f"https://www.tiktok.com/@{username}/video/{vid}"

        print(f"\n[{i}/{len(video_list)}] {vid}...")

        # Skip if already processed
        data_file = DATA_DIR / f"{vid}.json"
        if data_file.exists():
            print(f"  [>] Already processed, skipping")
            with open(data_file) as f:
                all_videos.append(json.load(f))
            continue

        # Get full detail (for author avatar)
        print(f"  [>] Fetching detail...")
        detail = get_video_detail(tiktok_url)
        time.sleep(0.5)

        # Save metadata
        vdata = save_video_data(vm, detail, i)

        # Fetch comments
        vdata["comments"] = get_comments(tiktok_url, vid)
        time.sleep(0.5)

        # Download video file
        vdata["video_file"] = download_video(tiktok_url, vid)

        # Re-save with video_file path
        with open(data_file, "w") as f:
            json.dump(vdata, f, indent=2)

        all_videos.append(vdata)
        print(f"  [+] {vdata['title'][:50]}")

        # Be nice
        time.sleep(1)

    # Step 3: Save profile and index
    save_profile(username, all_videos)

    index = {
        "username": username,
        "video_count": len(all_videos),
        "videos": [
            {
                "id": v["id"],
                "title": v["title"],
                "thumbnail": v["thumbnail"],
                "duration": v["duration"],
                "view_count": v["view_count"],
                "like_count": v["like_count"],
                "upload_date": v.get("upload_date", ""),
                "video_file": v.get("video_file", ""),
            }
            for v in all_videos
        ],
        "last_updated": datetime.now().isoformat(),
    }
    with open(DATA_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n=== Done! {len(all_videos)} videos scraped ===")
    print(f"Next: python3 build.py")


if __name__ == "__main__":
    main()
