// Key-sound-control Background Service Worker

let creatingOffscreen = null;

async function ensureOffscreenDocument() {
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT']
  });
  if (existingContexts.length > 0) {
    return;
  }

  if (creatingOffscreen) {
    await creatingOffscreen;
  } else {
    creatingOffscreen = chrome.offscreen.createDocument({
      url: 'offscreen.html',
      reasons: ['USER_MEDIA'],
      justification: 'Redirigir audio de pestañas a dispositivos de audio específicos'
    });
    await creatingOffscreen;
    creatingOffscreen = null;
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.action === 'ROUTE_TAB') {
        const { tabId, deviceId } = msg;

        if (!deviceId || deviceId === 'default') {
          // Revert to normal tab audio (stop capture)
          await ensureOffscreenDocument();
          chrome.runtime.sendMessage({
            target: 'offscreen',
            action: 'STOP_PLAYBACK',
            tabId: tabId
          });
          sendResponse({ status: 'ok', deviceId: 'default' });
          return;
        }

        // 1. Ensure offscreen document is ready
        await ensureOffscreenDocument();

        // 2. Obtain media stream ID for the target tab
        const streamId = await chrome.tabCapture.getMediaStreamId({
          targetTabId: tabId
        });

        // 3. Dispatch to offscreen document to play to selected sinkId
        chrome.runtime.sendMessage({
          target: 'offscreen',
          action: 'START_PLAYBACK',
          tabId: tabId,
          streamId: streamId,
          deviceId: deviceId,
          volume: msg.volume !== undefined ? msg.volume : 100,
          muted: msg.muted !== undefined ? msg.muted : false
        });

        sendResponse({ status: 'ok', deviceId: deviceId });
      } else if (msg.action === 'SET_VOLUME') {
        await ensureOffscreenDocument();
        chrome.runtime.sendMessage({
          target: 'offscreen',
          action: 'SET_VOLUME',
          tabId: msg.tabId,
          volume: msg.volume
        });
        sendResponse({ status: 'ok' });
      } else if (msg.action === 'SET_MUTE') {
        await ensureOffscreenDocument();
        chrome.runtime.sendMessage({
          target: 'offscreen',
          action: 'SET_MUTE',
          tabId: msg.tabId,
          muted: msg.muted
        });
        sendResponse({ status: 'ok' });
      }
    } catch (err) {
      console.error('Error in background message listener:', err);
      sendResponse({ status: 'error', error: err.message });
    }
  })();
  return true; // Keep message channel open for async response
});

// Clean up offscreen streams when tabs are closed
chrome.tabs.onRemoved.addListener(async (tabId) => {
  try {
    await chrome.storage.local.remove(`tab_${tabId}`);
    const existing = await chrome.runtime.getContexts({ contextTypes: ['OFFSCREEN_DOCUMENT'] });
    if (existing.length > 0) {
      chrome.runtime.sendMessage({
        target: 'offscreen',
        action: 'STOP_PLAYBACK',
        tabId: tabId
      });
    }
  } catch (e) {}
});
