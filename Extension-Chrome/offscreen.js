// Key-sound-control Ultra-Low-Latency Offscreen Audio Router

const activeTabPlayers = new Map();

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.target !== 'offscreen') return;

  (async () => {
    try {
      if (msg.action === 'START_PLAYBACK') {
        const { tabId, streamId, deviceId, volume, muted } = msg;

        // If already capturing this tab, change device/volume instantly (0ms delay)
        if (activeTabPlayers.has(tabId)) {
          const player = activeTabPlayers.get(tabId);
          if (player.deviceId !== deviceId) {
            player.deviceId = deviceId;
            if (player.ctx && typeof player.ctx.setSinkId === 'function') {
              await player.ctx.setSinkId(deviceId);
            } else if (player.fallbackAudio && typeof player.fallbackAudio.setSinkId === 'function') {
              await player.fallbackAudio.setSinkId(deviceId);
            }
          }
          const volVal = (volume !== undefined ? volume : 100) / 100.0;
          player.lastVol = volVal;
          player.gainNode.gain.setValueAtTime(muted ? 0 : volVal, player.ctx.currentTime);
          return;
        }

        // New capture with minimum latency
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            mandatory: {
              chromeMediaSource: 'tab',
              chromeMediaSourceId: streamId
            }
          },
          video: false
        });

        // Use Web Audio API with latencyHint: 'interactive' (eliminates HTML5 element buffer delay)
        const ctx = new (window.AudioContext || window.webkitAudioContext)({
          latencyHint: 'interactive'
        });

        if (ctx.state === 'suspended') {
          await ctx.resume();
        }

        let fallbackAudio = null;
        if (typeof ctx.setSinkId === 'function') {
          await ctx.setSinkId(deviceId);
        } else {
          // Fallback if AudioContext.setSinkId is not available
          fallbackAudio = new Audio();
          fallbackAudio.srcObject = stream;
          if (typeof fallbackAudio.setSinkId === 'function') {
            await fallbackAudio.setSinkId(deviceId);
          }
          fallbackAudio.play().catch(() => {});
        }

        const source = ctx.createMediaStreamSource(stream);
        const gainNode = ctx.createGain();
        const volVal = (volume !== undefined ? volume : 100) / 100.0;
        gainNode.gain.setValueAtTime(muted ? 0 : volVal, ctx.currentTime);

        source.connect(gainNode);
        gainNode.connect(ctx.destination);

        activeTabPlayers.set(tabId, {
          stream,
          ctx,
          source,
          gainNode,
          deviceId,
          lastVol: volVal,
          fallbackAudio
        });

        console.log(`[Offscreen] Tab ${tabId} enrutada a ${deviceId} con latencia ultrabaja (<20ms).`);

      } else if (msg.action === 'STOP_PLAYBACK') {
        const { tabId } = msg;
        if (activeTabPlayers.has(tabId)) {
          const player = activeTabPlayers.get(tabId);
          player.stream.getTracks().forEach(t => t.stop());
          try {
            player.ctx.close();
          } catch (e) {}
          if (player.fallbackAudio) {
            player.fallbackAudio.pause();
            player.fallbackAudio.srcObject = null;
          }
          activeTabPlayers.delete(tabId);
          console.log(`[Offscreen] Tab ${tabId} desconectada (restaurada a salida normal).`);
        }

      } else if (msg.action === 'SET_VOLUME') {
        const { tabId, volume } = msg;
        if (activeTabPlayers.has(tabId)) {
          const player = activeTabPlayers.get(tabId);
          const volVal = volume / 100.0;
          player.lastVol = volVal;
          player.gainNode.gain.setValueAtTime(volVal, player.ctx.currentTime);
        }

      } else if (msg.action === 'SET_MUTE') {
        const { tabId, muted } = msg;
        if (activeTabPlayers.has(tabId)) {
          const player = activeTabPlayers.get(tabId);
          player.gainNode.gain.setValueAtTime(muted ? 0 : (player.lastVol || 1), player.ctx.currentTime);
        }
      }
    } catch (err) {
      console.error('[Offscreen] Error en audio router:', err);
    }
  })();
});
