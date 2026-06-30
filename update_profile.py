#!/usr/bin/env python3
"""
Fetch real TikTok profile data and update data/profile.json.
Uses TikWM API for profile stats + downloads avatar locally.
"""

import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
COVERS_DIR = BASE_DIR / "covers"

TIKTOK_USER = "canthinkyy"
TIKWM_API = "https://www.tikwm.com/api/user/info"


def fetch_profile() -> dict:
    """Fetch real profile data from TikWM API."""
    data = urllib.parse.urlencode({"unique_id": TIKTOK_USER}).encode()
    req = urllib.request.Request(
        TIKWM_API,
        data=data,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read())

    if r.get("code") != 0:
        raise Exception(f"API error: {r.get('msg')}")

    u = r["data"]["user"]
    s = r["data"]["stats"]
    return {
        "username": u.get("uniqueId", TIKTOK_USER),
        "nickname": u.get("nickname", ""),
        "signature": u.get("signature", ""),
        "verified": u.get("verified", False),
        "avatar_url": u.get("avatarLarger", ""),
        "bio_link": (u.get("bioLink") or {}).get("link", ""),
        "following_count": s.get("followingCount", 0),
        "follower_count": s.get("followerCount", 0),
        "heart_count": s.get("heartCount", 0),
        "video_count": s.get("videoCount", 0),
    }


def download_avatar(url: str) -> str:
    """Download avatar to covers/profile_avatar.jpeg, return local path."""
    if not url:
        return "covers/profile_avatar.jpeg"
    out = COVERS_DIR / "profile_avatar.jpeg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            out.write_bytes(resp.read())
        print(f"[+] Downloaded avatar -> {out}")
    except Exception as e:
        print(f"[!] Avatar download failed: {e}")
    return "covers/profile_avatar.jpeg"


def main():
    DATA_DIR.mkdir(exist_ok=True)
    COVERS_DIR.mkdir(exist_ok=True)

    print(f"[*] Fetching profile for @{TIKTOK_USER}...")
    profile = fetch_profile()
    print(f"    nickname: {profile['nickname']}")
    print(f"    followers: {profile['follower_count']:,}")
    print(f"    likes: {profile['heart_count']:,}")
    print(f"    following: {profile['following_count']:,}")
    print(f"    videos: {profile['video_count']}")
    print(f"    bio: {profile['signature'][:80]}...")

    # Download avatar
    avatar_path = download_avatar(profile["avatar_url"])
    profile["avatar"] = avatar_path
    profile["last_updated"] = datetime.now().isoformat()

    # Save
    out = DATA_DIR / "profile.json"
    with open(out, "w") as f:
        json.dump(profile, f, indent=2)
    print(f"[+] Saved {out}")


if __name__ == "__main__":
    main()
