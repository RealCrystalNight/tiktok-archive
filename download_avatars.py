#!/usr/bin/env python3
"""
Download all comment/reply avatars locally.
TikTok CDN URLs expire, so we save them under covers/avatars/{user_id}.jpeg
"""

import json
import urllib.request
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
AVATAR_DIR = BASE_DIR / "covers" / "avatars"


def download(url: str, path: Path) -> bool:
    if path.exists():
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"  [!] Failed: {url[:60]}... {e}")
        return False


def main():
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    total = 0
    saved = 0

    for fpath in sorted(DATA_DIR.glob("*.json")):
        if fpath.name in ("index.json", "profile.json"):
            continue
        try:
            with open(fpath) as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError):
            continue

        vid = data.get("id", fpath.stem)
        for c in data.get("comments", []):
            avatar = c.get("avatar", "")
            user = c.get("user", "")
            if avatar and user and user not in seen:
                seen.add(user)
                ext = avatar.split("?")[0].rsplit(".", 1)[-1] if "." in avatar.split("?")[0] else "jpeg"
                out = AVATAR_DIR / f"{user}.{ext}"
                if download(avatar, out):
                    saved += 1
                total += 1
            for r in c.get("replies", []):
                r_avatar = r.get("avatar", "")
                r_user = r.get("user", "")
                if r_avatar and r_user and r_user not in seen:
                    seen.add(r_user)
                    ext = r_avatar.split("?")[0].rsplit(".", 1)[-1] if "." in r_avatar.split("?")[0] else "jpeg"
                    out = AVATAR_DIR / f"{r_user}.{ext}"
                    if download(r_avatar, out):
                        saved += 1
                    total += 1

    print(f"[+] Done: {saved}/{total} avatars downloaded ({len(seen)} unique users)")


if __name__ == "__main__":
    main()
