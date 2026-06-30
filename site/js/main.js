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
  if (muteBtn) {
    video.muted = true;
    muteBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      video.muted = !video.muted;
      if (unmuteIcon) unmuteIcon.style.display = video.muted ? '' : 'none';
      if (muteIcon) muteIcon.style.display = video.muted ? 'none' : '';
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
