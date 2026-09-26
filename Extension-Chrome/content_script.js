// Key-sound-control content script
(function() {
  // Listen for messages from popup or background
  chrome.runtime.onMessage?.addListener((msg, sender, sendResponse) => {
    if (msg.action === 'setSinkId') {
      window.__keySoundControlSinkId = msg.sinkId;
      applySinkToAllMedia(msg.sinkId);
      sendResponse({ status: 'ok' });
    }
  });

  function applySinkToAllMedia(sinkId) {
    const target = (sinkId === 'default' ? '' : sinkId);
    const mediaEls = document.querySelectorAll('video, audio');
    mediaEls.forEach(el => {
      if (typeof el.setSinkId === 'function') {
        el.setSinkId(target).catch(() => {});
      }
    });
  }

  // Ensure newly injected videos (like YouTube playlist navigation or ads) get the sink
  const observer = new MutationObserver((mutations) => {
    if (!window.__keySoundControlSinkId) return;
    const target = (window.__keySoundControlSinkId === 'default' ? '' : window.__keySoundControlSinkId);

    mutations.forEach(m => {
      m.addedNodes.forEach(node => {
        if (node.tagName === 'VIDEO' || node.tagName === 'AUDIO') {
          if (typeof node.setSinkId === 'function') {
            node.setSinkId(target).catch(() => {});
          }
        }
      });
    });
  });

  if (document.body) {
    observer.observe(document.body, { childList: true, subtree: true });
  } else {
    document.addEventListener('DOMContentLoaded', () => {
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }
})();
