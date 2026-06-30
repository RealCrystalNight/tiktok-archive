// TikTok-style video player + hover preview + next/prev scroll
var videoList = [];

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
  var unmuteTop = document.getElementById('unmuteTop');

  // Load video list from data attribute
  var listEl = document.getElementById('videoListData');
  if (listEl) videoList = JSON.parse(listEl.textContent);

  if (!video) return;

  // Restore mute state from localStorage
  var currentId = window.location.pathname.match(/\/video\/(\d+)\//);
  currentId = currentId ? currentId[1] : null;
  var wasUnmuted = currentId ? localStorage.getItem('tiktokArchiveUnmuted_' + currentId) === 'true' : false;

  if (wasUnmuted) {
    video.muted = false;
    if (unmuteIcon) unmuteIcon.style.display = '';
    if (muteIcon) muteIcon.style.display = 'none';
    if (unmuteTop) unmuteTop.classList.add('hidden');
  } else {
    video.muted = true;
  }

  function togglePlay() {
    if (video.paused) { video.play(); } else { video.pause(); }
  }

  function setMuted(muted) {
    video.muted = muted;
    if (unmuteIcon) unmuteIcon.style.display = muted ? 'none' : '';
    if (muteIcon) muteIcon.style.display = muted ? '' : 'none';
    if (unmuteTop) unmuteTop.classList.toggle('hidden', !muted);
    if (currentId) localStorage.setItem('tiktokArchiveUnmuted_' + currentId, muted ? 'false' : 'true');
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

  // Mute/unmute via bottom button
  if (muteBtn) {
    muteBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      setMuted(!video.muted);
    });
  }

  // Unmute via top-left button
  if (unmuteTop) {
    unmuteTop.addEventListener('click', function(e) {
      e.stopPropagation();
      setMuted(false);
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

  // === SCROLL TO NEXT/PREV VIDEO ===
  var scrollTimeout;
  var wheelAccum = 0;
  var wheelDir = 0;

  document.addEventListener('wheel', function(e) {
    if (videoList.length < 2 || !currentId) return;

    var idx = videoList.indexOf(currentId);
    if (idx === -1) return;

    var dir = e.deltaY > 0 ? 1 : -1;
    if (dir !== wheelDir) {
      wheelAccum = 0;
      wheelDir = dir;
    }
    wheelAccum += Math.abs(e.deltaY);

    if (wheelAccum > 300) {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(function() {
        if (wheelDir > 0 && idx < videoList.length - 1) {
          window.location.href = '../' + videoList[idx + 1] + '/';
        } else if (wheelDir < 0 && idx > 0) {
          window.location.href = '../' + videoList[idx - 1] + '/';
        }
        wheelAccum = 0;
      }, 150);
    }

    clearTimeout(scrollTimeout + 1);
    setTimeout(function() { wheelAccum = 0; }, 800);
  });

  // Autoplay
  video.play().catch(function() {
    if (overlay) overlay.classList.remove('hidden');
  });
});
