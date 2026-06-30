// Spinning disk sync with video playback
document.addEventListener('DOMContentLoaded', function() {
  var video = document.querySelector('video');
  var disk = document.querySelector('.music-disk');
  if (!video || !disk) return;

  video.addEventListener('play', function() { disk.classList.add('spinning'); });
  video.addEventListener('pause', function() { disk.classList.remove('spinning'); });
  video.addEventListener('ended', function() { disk.classList.remove('spinning'); });

  // Start spinning if video autoplays
  if (!video.paused) disk.classList.add('spinning');
});
