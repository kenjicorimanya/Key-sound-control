document.addEventListener('DOMContentLoaded', async () => {
  const tabTitleEl = document.getElementById('tabTitle');
  const tabIconEl = document.getElementById('tabIcon');
  const deviceListEl = document.getElementById('deviceList');
  const volSlider = document.getElementById('volSlider');
  const volLabel = document.getElementById('volLabel');
  const btnMute = document.getElementById('btnMute');
  const permissionBox = document.getElementById('permissionBox');
  const btnPermission = document.getElementById('btnPermission');

  let activeTab = null;
  let activeDeviceId = '';
  let isMuted = false;

  // 1. Get current active tab
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  activeTab = tab;

  if (activeTab) {
    tabTitleEl.textContent = activeTab.title || activeTab.url;
    if (activeTab.url && activeTab.url.includes('youtube.com')) {
      tabIconEl.textContent = '▶️';
    } else if (activeTab.url && activeTab.url.includes('twitch.tv')) {
      tabIconEl.textContent = '🟣';
    } else if (activeTab.url && activeTab.url.includes('spotify.com')) {
      tabIconEl.textContent = '🎵';
    } else {
      tabIconEl.textContent = '🌐';
    }

    // Load saved settings for this tab from storage
    const storageKey = `tab_${activeTab.id}`;
    const data = await chrome.storage.local.get(storageKey);
    if (data[storageKey]) {
      activeDeviceId = data[storageKey].deviceId || '';
      if (data[storageKey].volume !== undefined) {
        volSlider.value = data[storageKey].volume;
        volLabel.textContent = `${data[storageKey].volume}%`;
      }
      if (data[storageKey].muted !== undefined) {
        isMuted = data[storageKey].muted;
        btnMute.textContent = isMuted ? '🔇' : '🔊';
      }
    }
  }

  // Helper: Device icon
  function getDeviceIcon(label) {
    const l = (label || '').toLowerCase();
    if (l.includes('auricular') || l.includes('headphone') || l.includes('headset') || l.includes('tws')) return '🎧';
    if (l.includes('hdmi') || l.includes('monitor') || l.includes('tv')) return '🖥️';
    if (l.includes('fifine') || l.includes('usb') || l.includes('mic')) return '🎙️';
    return '🔊';
  }

  // 2. Load audio output devices
  async function loadDevices() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioOutputs = devices.filter(d => d.kind === 'audiooutput');

      // Check if labels are empty (requires permission in Chromium)
      const hasLabels = audioOutputs.some(d => d.label && d.label.length > 0);
      if (!hasLabels && audioOutputs.length > 0) {
        permissionBox.style.display = 'block';
      } else {
        permissionBox.style.display = 'none';
      }

      deviceListEl.innerHTML = '';

      // Default system output option
      const defaultItem = document.createElement('div');
      defaultItem.className = `device-item ${(!activeDeviceId || activeDeviceId === 'default') ? 'active' : ''}`;
      defaultItem.innerHTML = `
        <div class="device-details">
          <span>🌐</span>
          <span class="device-name">Salida predeterminada de Windows</span>
        </div>
        ${(!activeDeviceId || activeDeviceId === 'default') ? '<span class="check-icon">✓ Activo</span>' : ''}
      `;
      defaultItem.addEventListener('click', () => applyRoute('default'));
      deviceListEl.appendChild(defaultItem);

      // Other physical devices
      let counter = 1;
      audioOutputs.forEach(dev => {
        if (dev.deviceId === 'default') return;

        const name = dev.label || `Salida de audio ${counter++}`;
        const isSelected = (activeDeviceId === dev.deviceId);
        const icon = getDeviceIcon(name);

        const item = document.createElement('div');
        item.className = `device-item ${isSelected ? 'active' : ''}`;
        item.innerHTML = `
          <div class="device-details">
            <span>${icon}</span>
            <span class="device-name">${name}</span>
          </div>
          ${isSelected ? '<span class="check-icon">✓ Activo</span>' : ''}
        `;
        item.addEventListener('click', () => applyRoute(dev.deviceId));
        deviceListEl.appendChild(item);
      });

    } catch (err) {
      deviceListEl.innerHTML = `<div style="font-size:11px;color:#f7768e;padding:10px;">Error al listar salidas: ${err.message}</div>`;
    }
  }

  // 3. Permission trigger for device names
  btnPermission.addEventListener('click', async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      permissionBox.style.display = 'none';
      await loadDevices();
    } catch (e) {
      alert("No se pudo obtener el permiso. Puedes seguir seleccionando las salidas.");
    }
  });

  // 4. Apply Route to Active Tab
  async function applyRoute(deviceId) {
    activeDeviceId = deviceId;
    
    // Save in storage for this tab
    const storageKey = `tab_${activeTab.id}`;
    await chrome.storage.local.set({
      [storageKey]: {
        deviceId: activeDeviceId,
        volume: parseInt(volSlider.value),
        muted: isMuted
      }
    });

    // Execute redirection directly on tab media elements
    if (activeTab && activeTab.id) {
      try {
        await chrome.scripting.executeScript({
          target: { tabId: activeTab.id },
          func: (targetSinkId) => {
            window.__keySoundControlSinkId = targetSinkId;
            const mediaEls = document.querySelectorAll('video, audio');
            mediaEls.forEach(el => {
              if (typeof el.setSinkId === 'function') {
                el.setSinkId(targetSinkId === 'default' ? '' : targetSinkId)
                  .then(() => console.log('Key-sound-control: sinkId aplicado con éxito:', targetSinkId))
                  .catch(err => console.error('Key-sound-control: error setSinkId:', err));
              }
            });

            // Observer for dynamically added videos (YouTube autoplay, ads, etc.)
            if (!window.__keySoundControlObserver) {
              window.__keySoundControlObserver = new MutationObserver((mutations) => {
                mutations.forEach(m => {
                  m.addedNodes.forEach(node => {
                    if (node.tagName === 'VIDEO' || node.tagName === 'AUDIO') {
                      if (typeof node.setSinkId === 'function' && window.__keySoundControlSinkId) {
                        node.setSinkId(window.__keySoundControlSinkId === 'default' ? '' : window.__keySoundControlSinkId);
                      }
                    }
                  });
                });
              });
              window.__keySoundControlObserver.observe(document.body, { childList: true, subtree: true });
            }
          },
          args: [activeDeviceId]
        });
      } catch (err) {
        console.error("Error al inyectar script:", err);
      }
    }

    await loadDevices();
  }

  // 5. Volume Slider
  volSlider.addEventListener('input', async (e) => {
    const val = parseInt(e.target.value);
    volLabel.textContent = `${val}%`;

    if (activeTab && activeTab.id) {
      try {
        await chrome.scripting.executeScript({
          target: { tabId: activeTab.id },
          func: (volFraction) => {
            document.querySelectorAll('video, audio').forEach(el => {
              el.volume = volFraction;
            });
          },
          args: [val / 100.0]
        });
      } catch (err) {}
    }

    // Save
    const storageKey = `tab_${activeTab.id}`;
    const data = await chrome.storage.local.get(storageKey);
    const existing = data[storageKey] || {};
    existing.volume = val;
    await chrome.storage.local.set({ [storageKey]: existing });
  });

  // 6. Mute Button
  btnMute.addEventListener('click', async () => {
    isMuted = !isMuted;
    btnMute.textContent = isMuted ? '🔇' : '🔊';

    if (activeTab && activeTab.id) {
      try {
        await chrome.scripting.executeScript({
          target: { tabId: activeTab.id },
          func: (muteState) => {
            document.querySelectorAll('video, audio').forEach(el => {
              el.muted = muteState;
            });
          },
          args: [isMuted]
        });
      } catch (err) {}
    }

    // Save
    const storageKey = `tab_${activeTab.id}`;
    const data = await chrome.storage.local.get(storageKey);
    const existing = data[storageKey] || {};
    existing.muted = isMuted;
    await chrome.storage.local.set({ [storageKey]: existing });
  });

  // Initial load
  await loadDevices();
});
