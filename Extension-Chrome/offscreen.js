// Key-sound-control Offscreen Audio Handler

const activeTabPlayers = new Map();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target !== 'offscreen') return;

  (async () => {
    try {
      if (msg.action === 'START_PLAYBACK') {
        const { tabId, streamId, deviceId, volume, muted } = msg;

        // Cleanup existing player for this tab if present
        if (activeTabPlayers.has(tabId)) {
          const old = activeTabPlayers.get(tabId);
          old.stream.getTracks().forEach(t => t.stop());
          old.audio.pause();
          old.audio.srcObject = null;
          activeTabPlayers.delete(tabId);
        }

        // Capture stream using streamId
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            mandatory: {
              chromeMediaSource: 'tab',
              chromeMediaSourceId: streamId
            }
          },
          video: false
        });

        // Create player and route to sinkId
        const audio = new Audio();
        audio.srcObject = stream;
        audio.volume = (volume !== undefined ? volume : 100) / 100.0;
        audio.muted = !!muted;

        if (typeof audio.setSinkId === 'function') {
          await audio.setSinkId(deviceId);
          console.log(`[Offscreen] Tab ${tabId} audio redirigido con éxito a ${deviceId}`);
        } else {
          console.warn('[Offscreen] audio.setSinkId no está soportado en este contexto.');
        }

        await audio.play();
        activeTabPlayers.set(tabId, { stream, audio });

      } else if (msg.action === 'STOP_PLAYBACK') {
        const { tabId } = msg;
        if (activeTabPlayers.has(tabId)) {
          const p = activeTabPlayers.get(tabId);
          p.stream.getTracks().forEach(t => t.stop());
          p.audio.pause();
          p.audio.srcObject = null;
          activeTabPlayers.delete(tabId);
          console.log(`[Offscreen] Tab ${tabId} restablecida al audio normal.`);
        }

      } else if (msg.action === 'SET_VOLUME') {
        const { tabId, volume } = msg;
        if (activeTabPlayers.has(tabId)) {
          activeTabPlayers.get(tabId).audio.volume = (volume / 100.0);
        }

      } else if (msg.action === 'SET_MUTE') {
        const { tabId, muted } = msg;
        if (activeTabPlayers.has(tabId)) {
          activeTabPlayers.get(tabId).audio.muted = !!muted;
        }
      }
    } catch (err) {
      console.error('[Offscreen] Error handling audio stream:', err);
    }
  })();
});
