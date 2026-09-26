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
  let activeDeviceId = 'default';
  let isMuted = false;

  // 1. Get current active tab
  try {
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
        activeDeviceId = data[storageKey].deviceId || 'default';
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
  } catch (e) {
    console.error("Error al obtener la pestaña activa:", e);
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

      // Check if labels are missing/empty
      const hasLabels = audioOutputs.some(d => d.label && d.label.trim().length > 0);
      if (!hasLabels && audioOutputs.length > 0) {
        permissionBox.style.display = 'block';
      } else {
        permissionBox.style.display = 'none';
      }

      deviceListEl.innerHTML = '';

      // Default system output option
      const defaultItem = document.createElement('div');
      const isDefaultActive = (!activeDeviceId || activeDeviceId === 'default');
      defaultItem.className = `device-item ${isDefaultActive ? 'active' : ''}`;
      defaultItem.innerHTML = `
        <div class="device-details">
          <span>🌐</span>
          <span class="device-name">Salida predeterminada de Windows</span>
        </div>
        ${isDefaultActive ? '<span class="check-icon">✓ Activo</span>' : ''}
      `;
      defaultItem.addEventListener('click', () => applyRoute('default'));
      deviceListEl.appendChild(defaultItem);

      // Other physical devices
      let counter = 1;
      audioOutputs.forEach(dev => {
        if (dev.deviceId === 'default') return;

        const name = (dev.label && dev.label.trim().length > 0) ? dev.label : `Salida de audio ${counter++}`;
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

  // 3. Permission trigger for device names (opens tab to avoid popup crash)
  btnPermission.addEventListener('click', () => {
    chrome.tabs.create({ url: chrome.runtime.getURL('permissions.html') });
    window.close();
  });

  // 4. Apply Route to Active Tab via Background TabCapture & Offscreen setSinkId
  async function applyRoute(deviceId) {
    activeDeviceId = deviceId;
    
    if (activeTab && activeTab.id) {
      const storageKey = `tab_${activeTab.id}`;
      await chrome.storage.local.set({
        [storageKey]: {
          deviceId: activeDeviceId,
          volume: parseInt(volSlider.value),
          muted: isMuted
        }
      });

      // Dispatch route command to background
      chrome.runtime.sendMessage({
        action: 'ROUTE_TAB',
        tabId: activeTab.id,
        deviceId: activeDeviceId,
        volume: parseInt(volSlider.value),
        muted: isMuted
      }, (res) => {
        console.log('Key-sound-control ruta aplicada:', res);
      });
    }

    await loadDevices();
  }

  // 5. Volume Slider
  volSlider.addEventListener('input', async (e) => {
    const val = parseInt(e.target.value);
    volLabel.textContent = `${val}%`;

    if (activeTab && activeTab.id) {
      chrome.runtime.sendMessage({
        action: 'SET_VOLUME',
        tabId: activeTab.id,
        volume: val
      });

      const storageKey = `tab_${activeTab.id}`;
      const data = await chrome.storage.local.get(storageKey);
      const existing = data[storageKey] || {};
      existing.volume = val;
      await chrome.storage.local.set({ [storageKey]: existing });
    }
  });

  // 6. Mute Button
  btnMute.addEventListener('click', async () => {
    isMuted = !isMuted;
    btnMute.textContent = isMuted ? '🔇' : '🔊';

    if (activeTab && activeTab.id) {
      chrome.runtime.sendMessage({
        action: 'SET_MUTE',
        tabId: activeTab.id,
        muted: isMuted
      });

      const storageKey = `tab_${activeTab.id}`;
      const data = await chrome.storage.local.get(storageKey);
      const existing = data[storageKey] || {};
      existing.muted = isMuted;
      await chrome.storage.local.set({ [storageKey]: existing });
    }
  });

  // Initial load
  await loadDevices();
});
