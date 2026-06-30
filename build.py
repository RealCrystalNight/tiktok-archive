#!/usr/bin/env python3
"""
TikTok Archive Site Generator
Reads data/ JSON files and generates a static HTML site with TikTok-like UI.
Videos are served via raw.githack.com CDN from the GitHub repo.
"""

import json
import os
import html
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SITE_DIR = BASE_DIR / "site"
VIDEOS_DIR = SITE_DIR / "videos"
COVERS_SRC = BASE_DIR / "covers"

# --- CONFIG ---
GITHUB_USER = "RealCrystalNight"
REPO_NAME = "tiktok-archive"
CDN_BASE = f"https://raw.githack.com/{GITHUB_USER}/{REPO_NAME}/main"


def ensure_dirs():
    SITE_DIR.mkdir(exist_ok=True)
    (SITE_DIR / "css").mkdir(exist_ok=True)
    (SITE_DIR / "js").mkdir(exist_ok=True)
    (SITE_DIR / "videos").mkdir(exist_ok=True)
    (SITE_DIR / "covers").mkdir(exist_ok=True)
    (SITE_DIR / "users").mkdir(exist_ok=True)
    (SITE_DIR / "video").mkdir(exist_ok=True)
    # Copy covers from repo root to site
    if COVERS_SRC.exists():
        import shutil
        for f in COVERS_SRC.iterdir():
            if f.is_file():
                shutil.copy2(f, SITE_DIR / "covers" / f.name)


def fmt_count(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_duration(secs: int) -> str:
    m, s = divmod(int(secs), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fmt_date(d: str) -> str:
    if not d or len(d) != 8:
        return d
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def esc(s: str) -> str:
    return html.escape(str(s))


def linkify(text: str) -> str:
    """Convert @mentions and #hashtags to links."""
    text = re.sub(r'@(\w+)', r'<a href="https://www.tiktok.com/@\1" target="_blank" rel="noopener">@\1</a>', text)
    text = re.sub(r'#(\w+)', r'<a href="https://www.tiktok.com/tag/\1" target="_blank" rel="noopener">#\1</a>', text)
    return text


def video_cdn_url(video_id: str) -> str:
    return f"{CDN_BASE}/videos/{video_id}.mp4"


# ============================================================
# CSS
# ============================================================
CSS = """\
:root {
  --bg: #000000;
  --bg-card: #121212;
  --bg-hover: #1a1a1a;
  --bg-comment: #1e1e1e;
  --border: #2f2f2f;
  --text: #ffffff;
  --text-secondary: #a0a0a0;
  --text-muted: #666666;
  --accent: #fe2c55;
  --accent-hover: #ff4470;
  --tiktok-cyan: #25f4ee;
  --link: #25f4ee;
  --radius: 8px;
  --radius-lg: 12px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { font-size: 15px; scroll-behavior: smooth; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }

/* --- LAYOUT --- */
.container { max-width: 1200px; margin: 0 auto; padding: 0 20px; }

/* --- PROFILE HEADER --- */
.profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 40px 0 32px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
}
.profile-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--accent);
}
.profile-info h1 {
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 4px;
}
.profile-info .username {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 12px;
}
.profile-stats {
  display: flex;
  gap: 24px;
}
.profile-stat {
  text-align: center;
}
.profile-stat .num {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text);
}
.profile-stat .label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* --- VIDEO GRID --- */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  padding-bottom: 60px;
}
.video-card {
  position: relative;
  border-radius: var(--radius);
  overflow: hidden;
  aspect-ratio: 9/12;
  background: var(--bg-card);
  cursor: pointer;
  transition: transform 0.15s;
}
.video-card:hover { transform: scale(1.02); }
.video-card a {
  display: block;
  width: 100%;
  height: 100%;
  text-decoration: none;
}
.video-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.video-card .overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 8px 10px;
  background: linear-gradient(transparent, rgba(0,0,0,0.85));
}
.video-card .overlay .title {
  font-size: 0.78rem;
  font-weight: 500;
  color: #fff;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
}
.video-card .overlay .meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.68rem;
  color: rgba(255,255,255,0.7);
}
.video-card .overlay .meta svg {
  width: 12px;
  height: 12px;
  fill: currentColor;
}
.video-card .duration-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.7);
  color: #fff;
  font-size: 0.68rem;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

/* --- VIDEO PAGE --- */
.video-page {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 0;
  min-height: calc(100vh - 80px);
}
.video-player-wrap {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  overflow: hidden;
}
.video-player-wrap video {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: 100%;
  object-fit: contain;
}
.video-sidebar {
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* Video info */
.video-info {
  padding: 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.video-info .desc {
  font-size: 0.9rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 12px;
  word-break: break-word;
}
.video-info .desc a { color: var(--link); }
.video-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.video-meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.video-meta-item svg { width: 16px; height: 16px; fill: var(--text-muted); }

/* Author */
.video-author {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.video-author img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}
.video-author .author-info {
  flex: 1;
}
.video-author .author-name {
  font-weight: 600;
  font-size: 0.9rem;
}
.video-author .author-name a {
  color: var(--text);
  text-decoration: none;
}
.video-author .author-name a:hover { color: var(--link); }
.video-author .author-stats {
  font-size: 0.75rem;
  color: var(--text-muted);
}

/* Music ticker */
.music-ticker {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.music-disk {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #282828;
  border: 2px solid #404040;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}
.music-disk::after {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #181818;
  border: 2px solid #333;
  position: absolute;
  z-index: 2;
}
.music-disk img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}
.music-disk.spinning {
  animation: spin 3s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.music-info {
  overflow: hidden;
  flex: 1;
}
.music-info .music-name {
  font-size: 0.8rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.music-info .music-author {
  font-size: 0.72rem;
  color: var(--text-muted);
}

/* Comments */
.comments-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}
.comments-section h3 {
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 16px;
  color: var(--text-secondary);
}
.comment {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.comment-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.comment-body { flex: 1; }
.comment-author {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.comment-author a {
  color: var(--text-muted);
  text-decoration: none;
}
.comment-author a:hover { color: var(--link); }
.comment-text {
  font-size: 0.85rem;
  color: var(--text-secondary);
  line-height: 1.5;
  word-break: break-word;
}
.comment-meta {
  display: flex;
  gap: 12px;
  margin-top: 4px;
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* View replies button */
.view-replies-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.75rem;
  cursor: pointer;
  padding: 4px 0;
  margin-top: 4px;
}
.view-replies-btn:hover { color: var(--text-secondary); }

/* Replies — TikTok style */
.replies {
  margin-top: 8px;
  padding-left: 0;
}
.reply {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  padding-left: 12px;
  border-left: 2px solid var(--border);
}
.reply-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}
.reply-body { flex: 1; }
.reply-author {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.reply-author a {
  color: var(--text-muted);
  text-decoration: none;
}
.reply-author a:hover { color: var(--link); }
.reply-text {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
  word-break: break-word;
}
.reply-meta {
  margin-top: 2px;
  font-size: 0.68rem;
  color: var(--text-muted);
}

/* Download btn */
.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--accent);
  color: #fff;
  padding: 8px 16px;
  border-radius: var(--radius);
  font-size: 0.82rem;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.15s;
  margin-top: 12px;
}
.download-btn:hover { background: var(--accent-hover); text-decoration: none; }

/* --- NAV --- */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: rgba(0,0,0,0.9);
  backdrop-filter: blur(10px);
  z-index: 100;
}
.top-nav .logo {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}
.top-nav .logo:hover { text-decoration: none; }
.top-nav .logo svg { width: 24px; height: 24px; }
.top-nav .nav-links {
  display: flex;
  gap: 16px;
}
.top-nav .nav-links a {
  color: var(--text-secondary);
  font-size: 0.85rem;
  text-decoration: none;
}
.top-nav .nav-links a:hover { color: var(--text); }

/* --- FOOTER --- */
.site-footer {
  text-align: center;
  padding: 32px 20px;
  border-top: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 0.78rem;
}

/* --- RESPONSIVE --- */
@media (max-width: 900px) {
  .video-page {
    grid-template-columns: 1fr;
  }
  .video-player-wrap {
    position: relative;
    height: auto;
    aspect-ratio: 9/16;
    max-height: 70vh;
  }
  .video-sidebar {
    height: auto;
    border-left: none;
    border-top: 1px solid var(--border);
  }
  .profile-header {
    flex-direction: column;
    text-align: center;
  }
  .profile-stats { justify-content: center; }
  .video-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
}
@media (max-width: 600px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 4px;
  }
  .profile-header { padding: 24px 0 20px; }
  .profile-avatar { width: 72px; height: 72px; }
  .profile-info h1 { font-size: 1.4rem; }
}

/* --- PROFILE BIO --- */
.profile-bio {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 8px 0;
  line-height: 1.5;
  white-space: pre-line;
}
.profile-link {
  display: inline-block;
  font-size: 0.8rem;
  color: var(--link);
  margin-bottom: 12px;
}

/* --- HOVER PREVIEW --- */
.video-card .hover-preview {
  position: absolute;
  top: 0; left: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
  z-index: 1;
}
.video-card:hover .hover-preview { opacity: 1; }
.video-card:hover .hover-preview + img,
.video-card:hover .hover-preview ~ div { opacity: 0; transition: opacity 0.2s; }

/* --- TIKTOK PLAYER CONTROLS --- */
.player-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 2;
}
.player-overlay.hidden { display: none; }
.play-icon {
  width: 64px; height: 64px;
  opacity: 0.8;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.5));
  transition: opacity 0.15s;
}
.player-overlay:hover .play-icon { opacity: 1; }

.player-controls {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0,0,0,0.7));
  padding: 24px 12px 8px;
  z-index: 3;
  opacity: 0;
  transition: opacity 0.2s;
}
.video-player-wrap:hover .player-controls { opacity: 1; }

.progress-bar {
  width: 100%;
  height: 3px;
  background: rgba(255,255,255,0.3);
  border-radius: 2px;
  cursor: pointer;
  margin-bottom: 8px;
}
.progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  width: 0%;
  transition: width 0.1s linear;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 12px;
}
.ctrl-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  text-decoration: none;
}
.ctrl-btn svg { width: 24px; height: 24px; }

.unmute-top {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 4;
  background: rgba(0,0,0,0.6);
  border: none;
  border-radius: 20px;
  color: white;
  padding: 8px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 500;
  backdrop-filter: blur(4px);
  transition: opacity 0.2s, background 0.15s;
}
.unmute-top:hover { background: rgba(0,0,0,0.8); }
.unmute-top.hidden { opacity: 0; pointer-events: none; }

/* --- SCROLLBAR --- */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
"""

# ============================================================
# JS
# ============================================================
JS = """\
// TikTok-style video player + hover preview
document.addEventListener('DOMContentLoaded', function() {
  // === HOVER PREVIEW ON GRID CARDS ===
  document.querySelectorAll('.video-card').forEach(function(card) {
    var preview = card.querySelector('.hover-preview');
    if (!preview) return;
    var src = preview.dataset.src;
    var hoverTimeout;

    card.addEventListener('mouseenter', function() {
      hoverTimeout = setTimeout(function() {
        preview.src = src;
        preview.play().catch(function(){});
      }, 400);
    });
    card.addEventListener('mouseleave', function() {
      clearTimeout(hoverTimeout);
      preview.pause();
      preview.removeAttribute('src');
      preview.load();
    });
  });

  // === TIKTOK VIDEO PLAYER ===
  var video = document.getElementById('tiktokPlayer');
  var overlay = document.getElementById('playerOverlay');
  var playBtn = document.getElementById('playBtn');
  var playIcon = document.getElementById('playIcon');
  var pauseIcon = document.getElementById('pauseIcon');
  var muteBtn = document.getElementById('muteBtn');
  var unmuteIcon = document.getElementById('unmuteIcon');
  var muteIcon = document.getElementById('muteIcon');
  var progressFill = document.getElementById('progressFill');
  var progressBar = document.getElementById('progressBar');
  var disk = document.querySelector('.music-disk');

  if (!video) return;

  function togglePlay() {
    if (video.paused) { video.play(); } else { video.pause(); }
  }

  // Click overlay to play/pause
  if (overlay) {
    overlay.addEventListener('click', function(e) {
      e.stopPropagation();
      togglePlay();
    });
  }

  // Click video to play/pause
  video.addEventListener('click', function(e) {
    e.stopPropagation();
    togglePlay();
  });

  // Play/pause button
  if (playBtn) {
    playBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      togglePlay();
    });
  }

  // Update UI on play/pause
  video.addEventListener('play', function() {
    if (overlay) overlay.classList.add('hidden');
    if (playIcon) playIcon.style.display = 'none';
    if (pauseIcon) pauseIcon.style.display = '';
    if (disk) disk.classList.add('spinning');
  });
  video.addEventListener('pause', function() {
    if (overlay) overlay.classList.remove('hidden');
    if (playIcon) playIcon.style.display = '';
    if (pauseIcon) pauseIcon.style.display = 'none';
    if (disk) disk.classList.remove('spinning');
  });
  video.addEventListener('ended', function() {
    if (overlay) overlay.classList.remove('hidden');
    if (playIcon) playIcon.style.display = '';
    if (pauseIcon) pauseIcon.style.display = 'none';
    if (disk) disk.classList.remove('spinning');
  });

  // Mute/unmute
  var unmuteTop = document.getElementById('unmuteTop');
  if (muteBtn) {
    video.muted = true;
    muteBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      video.muted = !video.muted;
      if (unmuteIcon) unmuteIcon.style.display = video.muted ? '' : 'none';
      if (muteIcon) muteIcon.style.display = video.muted ? 'none' : '';
      if (unmuteTop) unmuteTop.classList.toggle('hidden', !video.muted);
    });
  }
  if (unmuteTop) {
    unmuteTop.addEventListener('click', function(e) {
      e.stopPropagation();
      video.muted = false;
      if (unmuteIcon) unmuteIcon.style.display = 'none';
      if (muteIcon) muteIcon.style.display = '';
      unmuteTop.classList.add('hidden');
    });
  }

  // Progress bar
  video.addEventListener('timeupdate', function() {
    if (video.duration) {
      progressFill.style.width = (video.currentTime / video.duration * 100) + '%';
    }
  });
  if (progressBar) {
    progressBar.addEventListener('click', function(e) {
      e.stopPropagation();
      var rect = progressBar.getBoundingClientRect();
      var pct = (e.clientX - rect.left) / rect.width;
      video.currentTime = pct * video.duration;
    });
  }

  // Spacebar to play/pause
  document.addEventListener('keydown', function(e) {
    if (e.code === 'Space' && document.activeElement.tagName !== 'INPUT') {
      e.preventDefault();
      togglePlay();
    }
  });

  // Autoplay (muted by default for autoplay policy)
  video.play().catch(function() {
    // Autoplay blocked, show overlay
    if (overlay) overlay.classList.remove('hidden');
  });
});
"""


# ============================================================
# HTML GENERATORS
# ============================================================

def html_shell(title: str, desc: str, url: str, body: str, extra_head: str = "", depth: int = 0) -> str:
    prefix = "../" * depth if depth else ""
    vid_prefix = "../" * (depth + 1) if depth else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="index, follow">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(url)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}">
<meta name="theme-color" content="#fe2c55">
<link rel="canonical" href="{esc(url)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}css/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎵</text></svg>">
{extra_head}
</head>
<body>
<nav class="top-nav">
  <a href="{prefix}index.html" class="logo">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
    TikTok Archive
  </a>
  <div class="nav-links">
    <a href="{prefix}index.html">Videos</a>
  </div>
</nav>
{body}
<script src="{prefix}js/main.js"></script>
</body>
</html>"""


def build_index():
    """Build the homepage with video grid."""
    index_file = DATA_DIR / "index.json"
    if not index_file.exists():
        print("[!] No index.json found. Run scraper.py first.")
        return

    with open(index_file) as f:
        index = json.load(f)

    profile_file = DATA_DIR / "profile.json"
    profile = {}
    if profile_file.exists():
        with open(profile_file) as f:
            profile = json.load(f)

    username = index.get("username", "unknown")
    videos = index.get("videos", [])

    # Video grid cards
    cards = ""
    for v in videos:
        vid = v["id"]
        title = esc(v.get("title", "Untitled"))
        thumb = f"covers/{vid}.jpeg"
        duration = fmt_duration(v.get("duration", 0))
        views = fmt_count(v.get("view_count", 0))

        thumb_html = f'<img src="{esc(thumb)}" alt="{title}" loading="lazy">' if thumb else '<div style="width:100%;height:100%;background:#1a1a1a"></div>'

        cards += f"""
<div class="video-card" data-vid="{esc(vid)}">
  <a href="video/{vid}/">
    {thumb_html}
    <video class="hover-preview" muted loop preload="none" playsinline
           data-src="{esc(video_cdn_url(vid))}"
           poster="{esc(thumb)}"></video>
    <span class="duration-badge">{duration}</span>
    <div class="overlay">
      <div class="title">{title}</div>
      <div class="meta">
        <svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>
        {views}
      </div>
    </div>
  </a>
</div>"""

    # Profile header - use local avatar
    avatar_url = profile.get("avatar", "") or "covers/profile_avatar.jpeg"
    avatar_html = f'<img src="{esc(avatar_url)}" alt="@{esc(username)}" class="profile-avatar">' if avatar_url else '<div class="profile-avatar" style="background:#333;display:flex;align-items:center;justify-content:center;font-size:2rem">@</div>'

    profile_html = f"""
<div class="container">
  <div class="profile-header">
    {avatar_html}
    <div class="profile-info">
      <h1>{esc(profile.get('nickname', username))}</h1>
      <div class="username">@{esc(username)}</div>
      <div class="profile-bio">{linkify(esc(profile.get('signature', '')))}</div>
      {f'<a href="{esc(profile.get("bio_link",""))}" target="_blank" rel="noopener" class="profile-link">{esc(profile.get("bio_link",""))}</a>' if profile.get('bio_link') else ''}
      <div class="profile-stats">
        <div class="profile-stat">
          <div class="num">{fmt_count(profile.get('following_count', 0))}</div>
          <div class="label">Following</div>
        </div>
        <div class="profile-stat">
          <div class="num">{fmt_count(profile.get('follower_count', 0))}</div>
          <div class="label">Followers</div>
        </div>
        <div class="profile-stat">
          <div class="num">{fmt_count(profile.get('heart_count', 0))}</div>
          <div class="label">Likes</div>
        </div>
      </div>
    </div>
  </div>

  <div class="video-grid">
    {cards}
  </div>

  <div class="site-footer">
    <p>Archived {len(videos)} videos from @{esc(username)}</p>
    <p>Last updated: {index.get('last_updated', 'unknown')[:10]}</p>
  </div>
</div>"""

    body = profile_html
    page = html_shell(
        title=f"@{username} — TikTok Archive",
        desc=f"Archived TikTok videos from @{username}. Full quality downloads, comments, and metadata.",
        url=f"{CDN_BASE}/",
        body=body,
    )

    out = SITE_DIR / "index.html"
    with open(out, "w") as f:
        f.write(page)
    print(f"[+] Built index.html ({len(videos)} videos)")


def build_video_page(video_data: dict):
    """Build individual video page."""
    vid = video_data["id"]
    title = video_data.get("title", "Untitled")
    desc = video_data.get("description", "")
    views = fmt_count(video_data.get("view_count", 0))
    likes = fmt_count(video_data.get("like_count", 0))
    comments_count = fmt_count(video_data.get("comment_count", 0))
    duration = fmt_duration(video_data.get("duration", 0))
    upload_date = fmt_date(video_data.get("upload_date", ""))
    track = video_data.get("track", "")
    artist = video_data.get("artist", "")
    thumb = f"../../covers/{vid}.jpeg"
    username = video_data.get("uploader_id", "") or video_data.get("uploader", "unknown")
    nickname = video_data.get("uploader", username)
    video_url = video_data.get("webpage_url", "")
    video_src_cdn = video_cdn_url(vid)
    video_src_local = f"../../../videos/{vid}.mp4"

    # Author avatar - use local cover image (TikWM avatars are behind Cloudflare)
    author_avatar = f"../../covers/{vid}.jpeg"

    avatar_html = f'<img src="{esc(author_avatar)}" alt="" class="comment-avatar">' if author_avatar else ""

    # Description with linkified hashtags/mentions
    desc_html = linkify(esc(desc)) if desc else "<em>No description</em>"

    # Music disk - use local cover image (TikTok CDN URLs expire)
    disk_cover = f"../../covers/{vid}.jpeg"
    disk_img = f'<img src="{esc(disk_cover)}" alt="">' if disk_cover else ""

    # Comments
    comments_html = ""
    for c in video_data.get("comments", [])[:50]:
        c_avatar = c.get("avatar", "")
        c_avatar_html = f'<img src="{esc(c_avatar)}" alt="" class="comment-avatar">' if c_avatar else '<div class="comment-avatar" style="background:#333"></div>'
        c_author = esc(c.get("nickname", "") or c.get("user", "") or "unknown")
        c_author_id = c.get("user", "")
        c_author_url = f"https://www.tiktok.com/@{c_author_id}" if c_author_id else "#"
        c_text = linkify(esc(c.get("text", "")))
        c_likes = fmt_count(c.get("likes", 0))

        # Replies
        replies_html = ""
        reply_count = c.get("reply_count", 0)
        for r in c.get("replies", [])[:20]:
            r_avatar = r.get("avatar", "")
            r_avatar_html = f'<img src="{esc(r_avatar)}" alt="" class="reply-avatar">' if r_avatar else '<div class="reply-avatar" style="background:#333"></div>'
            r_author = esc(r.get("nickname", "") or r.get("user", "") or "unknown")
            r_text = linkify(esc(r.get("text", "")))
            r_likes = fmt_count(r.get("likes", 0))
            replies_html += f"""
      <div class="reply">
        {r_avatar_html}
        <div class="reply-body">
          <div class="reply-author"><a href="https://www.tiktok.com/@{esc(r.get('user',''))}" target="_blank" rel="noopener">{r_author}</a></div>
          <div class="reply-text">{r_text}</div>
          <div class="reply-meta"><span>{r_likes} likes</span></div>
        </div>
      </div>"""

        view_replies = ""
        if reply_count > 0 and replies_html:
            view_replies = f'<button class="view-replies-btn" onclick="this.nextElementSibling.style.display=\'block\';this.style.display=\'none\'">View all {reply_count} replies</button>'

        comments_html += f"""
<div class="comment">
  {c_avatar_html}
  <div class="comment-body">
    <div class="comment-author"><a href="{esc(c_author_url)}" target="_blank" rel="noopener">{c_author}</a></div>
    <div class="comment-text">{c_text}</div>
    <div class="comment-meta">
      <span>{c_likes} likes</span>
    </div>
    {view_replies}
    {f'<div class="replies" style="display:none">{replies_html}</div>' if replies_html else ''}
  </div>
</div>"""

    if not comments_html:
        comments_html = '<p style="color:var(--text-muted);font-size:0.85rem">No comments archived for this video.</p>'

    # OG tags for video page (override generic ones from html_shell)
    cover_cdn = f"{CDN_BASE}/covers/{vid}.jpeg"
    extra_head = f"""
<meta property="og:type" content="video.other">
<meta property="og:site_name" content="TikTok Archive">
<meta property="og:title" content="{esc(title)} — @{esc(username)}">
<meta property="og:description" content="{esc(desc[:200]) if desc else 'Archived TikTok video by @' + esc(username)}">
<meta property="og:url" content="{esc(video_src_cdn)}">
<meta property="og:image" content="{esc(cover_cdn)}">
<meta property="og:image:width" content="720">
<meta property="og:image:height" content="1280">
<meta property="og:video" content="{esc(video_src_cdn)}">
<meta property="og:video:url" content="{esc(video_src_cdn)}">
<meta property="og:video:secure_url" content="{esc(video_src_cdn)}">
<meta property="og:video:type" content="video/mp4">
<meta property="og:video:width" content="1080">
<meta property="og:video:height" content="1920">
<meta name="twitter:card" content="player">
<meta name="twitter:site" content="@{esc(username)}">
<meta name="twitter:title" content="{esc(title)} — @{esc(username)}">
<meta name="twitter:description" content="{esc(desc[:200]) if desc else 'Archived TikTok video'}">
<meta name="twitter:player" content="{esc(video_src_cdn)}">
<meta name="twitter:player:width" content="1080">
<meta name="twitter:player:height" content="1920">
<meta name="theme-color" content="#fe2c55">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "VideoObject",
  "name": "{esc(title)}",
  "description": "{esc(desc[:500])}",
  "thumbnailUrl": "{esc(thumb)}",
  "uploadDate": "{upload_date}",
  "duration": "PT{video_data.get('duration', 0)}S",
  "interactionStatistic": [
    {{ "@type": "InteractionCounter", "interactionType": "https://schema.org/WatchAction", "userInteractionCount": {video_data.get('view_count', 0)} }},
    {{ "@type": "InteractionCounter", "interactionType": "https://schema.org/LikeAction", "userInteractionCount": {video_data.get('like_count', 0)} }},
    {{ "@type": "InteractionCounter", "interactionType": "https://schema.org/CommentAction", "userInteractionCount": {video_data.get('comment_count', 0)} }}
  ],
  "contentUrl": "{esc(video_src_cdn)}",
  "embedUrl": "{esc(video_src_cdn)}",
  "author": {{
    "@type": "Person",
    "name": "{esc(nickname)}",
    "url": "https://www.tiktok.com/@{esc(username)}"
  }}
}}
</script>"""

    body = f"""
<div class="video-page">
  <div class="video-player-wrap" id="playerWrap">
    <video id="tiktokPlayer" autoplay playsinline preload="metadata" poster="{esc(thumb)}">
      <source src="{esc(video_src_local)}" type="video/mp4">
    </video>
    <div class="player-overlay" id="playerOverlay">
      <svg class="play-icon" viewBox="0 0 24 24" fill="white"><path d="M8 5v14l11-7z"/></svg>
    </div>
    <button class="unmute-top" id="unmuteTop" title="Click to unmute">
      <svg viewBox="0 0 24 24" fill="white" width="20" height="20"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
      <span>Unmute</span>
    </button>
    <div class="player-controls" id="playerControls">
      <div class="progress-bar" id="progressBar"><div class="progress-fill" id="progressFill"></div></div>
      <div class="controls-row">
        <button class="ctrl-btn" id="playBtn" title="Play/Pause">
          <svg viewBox="0 0 24 24" fill="white" id="playIcon"><path d="M8 5v14l11-7z"/></svg>
          <svg viewBox="0 0 24 24" fill="white" id="pauseIcon" style="display:none"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        </button>
        <button class="ctrl-btn" id="muteBtn" title="Mute/Unmute">
          <svg viewBox="0 0 24 24" fill="white" id="unmuteIcon"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
          <svg viewBox="0 0 24 24" fill="white" id="muteIcon" style="display:none"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
        </button>
        <a href="{esc(video_src_cdn)}" download class="ctrl-btn" title="Download" id="downloadBtn">
          <svg viewBox="0 0 24 24" fill="white"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
        </a>
      </div>
    </div>
  </div>
  <div class="video-sidebar">
    <div class="video-info">
      <div class="desc">{desc_html}</div>
      <div class="video-meta">
        <span class="video-meta-item">
          <svg viewBox="0 0 24 24"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/></svg>
          {views} views
        </span>
        <span class="video-meta-item">
          <svg viewBox="0 0 24 24"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>
          {likes}
        </span>
        <span class="video-meta-item">
          <svg viewBox="0 0 24 24"><path d="M21.99 4c0-1.1-.89-2-1.99-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18z"/></svg>
          {comments_count} comments
        </span>
        <span class="video-meta-item">{duration}</span>
        <span class="video-meta-item">{upload_date}</span>
      </div>
    </div>

    <div class="video-author">
      {avatar_html}
      <div class="author-info">
        <div class="author-name"><a href="https://www.tiktok.com/@{esc(username)}" target="_blank" rel="noopener">{esc(nickname)}</a></div>
        <div class="author-stats">@{esc(username)}</div>
      </div>
    </div>

    <div class="music-ticker">
      <div class="music-disk">
        {disk_img}
      </div>
      <div class="music-info">
        <div class="music-name">{esc(track) if track else "Original sound"}</div>
        <div class="music-author">{esc(artist) if artist else esc(nickname)}</div>
      </div>
    </div>

    <div class="comments-section">
      <h3>Comments ({comments_count})</h3>
      {comments_html}
    </div>
  </div>
</div>"""

    page = html_shell(
        title=f"{title} — @{username} | TikTok Archive",
        desc=desc[:200] if desc else f"Archived TikTok video by @{username}",
        url=f"{CDN_BASE}/video/{vid}/",
        body=body,
        extra_head=extra_head,
        depth=2,
    )

    # Write to video/{id}/index.html
    out_dir = SITE_DIR / "video" / vid
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "index.html", "w") as f:
        f.write(page)
    print(f"  [+] Built video/{vid}/")


def build_sitemap():
    """Generate sitemap.xml."""
    index_file = DATA_DIR / "index.json"
    if not index_file.exists():
        return

    with open(index_file) as f:
        index = json.load(f)

    urls = [
        f'  <url><loc>{CDN_BASE}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>',
    ]

    for v in index.get("videos", []):
        urls.append(
            f'  <url><loc>{CDN_BASE}/video/{v["id"]}/</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>'
        )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

    with open(SITE_DIR / "sitemap.xml", "w") as f:
        f.write(sitemap)
    print(f"[+] Built sitemap.xml ({len(urls)} URLs)")


def build_robots():
    with open(SITE_DIR / "robots.txt", "w") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {CDN_BASE}/sitemap.xml\n")
    print("[+] Built robots.txt")


def main():
    ensure_dirs()

    # Write CSS
    with open(SITE_DIR / "css" / "style.css", "w") as f:
        f.write(CSS)
    print("[+] Written css/style.css")

    # Write JS
    with open(SITE_DIR / "js" / "main.js", "w") as f:
        f.write(JS)
    print("[+] Written js/main.js")

    # Build pages
    build_index()
    build_sitemap()
    build_robots()

    # Build individual video pages
    data_files = sorted(DATA_DIR.glob("*.json"))
    video_count = 0
    for df in data_files:
        if df.name in ("index.json", "profile.json"):
            continue
        try:
            with open(df) as f:
                vdata = json.load(f)
            if "id" in vdata:
                build_video_page(vdata)
                video_count += 1
        except (json.JSONDecodeError, KeyError):
            continue

    print(f"\n=== Site built! {video_count} video pages generated ===")
    print(f"Output: {SITE_DIR}/")
    print(f"\nTo preview: cd site && python3 -m http.server 8000")
    print(f"To deploy: push the repo to GitHub, videos serve via raw.githack.com")


if __name__ == "__main__":
    main()
