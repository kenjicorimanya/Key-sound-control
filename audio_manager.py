import ctypes
from ctypes import wintypes
import psutil
import logging
from dataclasses import dataclass
import pycaw.pycaw as pycaw
from pycaw.constants import AudioDeviceState
from audio_policy import AudioPolicyService

logger = logging.getLogger("AudioManager")
user32 = ctypes.windll.user32

@dataclass
class AudioDeviceInfo:
    id: str
    name: str
    clean_name: str
    volume_percent: int
    is_muted: bool
    is_default: bool
    icon: str

@dataclass
class AudioSessionInfo:
    pid: int
    name: str
    display_name: str
    window_title: str
    volume_percent: int
    is_muted: bool
    current_device_id: str | None

@dataclass
class ForegroundAppInfo:
    hwnd: int
    pid: int
    process_name: str
    window_title: str

class AudioManager:
    def __init__(self):
        self.policy_service = AudioPolicyService()

    def get_foreground_app(self) -> ForegroundAppInfo:
        """Retrieves details of the currently focused window in Windows."""
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ForegroundAppInfo(0, 0, "Windows", "")

        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Get window title
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        title = buff.value.strip()

        # Get process name
        proc_name = "Desconocido"
        try:
            p = psutil.Process(pid.value)
            proc_name = p.name()
        except Exception:
            pass

        return ForegroundAppInfo(
            hwnd=hwnd,
            pid=pid.value,
            process_name=proc_name,
            window_title=title
        )

    def _determine_icon(self, name: str) -> str:
        """Assigns an appropriate emoji icon based on device friendly name."""
        n = name.lower()
        if any(w in n for w in ["auricular", "headphone", "headset", "earphone", "tws", "airpod", "buds"]):
            return "🎧"
        elif any(w in n for w in ["hdmi", "displayport", "monitor", "tv", "pantalla", "lg", "samsung"]):
            return "🖥️"
        elif any(w in n for w in ["usb", "fifine", "hyperx", "yeti", "rode"]):
            return "🎙️"
        elif any(w in n for w in ["bluetooth", "bt"]):
            return "📶"
        else:
            return "🔊"

    def get_playback_devices(self) -> list[AudioDeviceInfo]:
        """Returns all active sound playback devices."""
        devices = []
        try:
            default_device = pycaw.AudioUtilities.GetSpeakers()
            default_id = default_device.id if default_device else ""
        except Exception:
            default_id = ""

        try:
            all_devs = pycaw.AudioUtilities.GetAllDevices()
            for dev in all_devs:
                if dev.state == AudioDeviceState.Active and dev.id.startswith("{0.0.0."):
                    clean_name = dev.FriendlyName
                    # Simplify name (remove duplicate manufacturer tags if present)
                    clean_name = clean_name.replace("(R)", "").strip()
                    
                    try:
                        vol = round(dev.EndpointVolume.GetMasterVolumeLevelScalar() * 100)
                        mute = bool(dev.EndpointVolume.GetMute())
                    except Exception:
                        vol = 100
                        mute = False

                    is_def = (dev.id == default_id)
                    icon = self._determine_icon(dev.FriendlyName)

                    devices.append(AudioDeviceInfo(
                        id=dev.id,
                        name=dev.FriendlyName,
                        clean_name=clean_name,
                        volume_percent=vol,
                        is_muted=mute,
                        is_default=is_def,
                        icon=icon
                    ))
        except Exception as e:
            logger.error(f"Error enumerating playback devices: {e}")

        # Place default device first, then sort by name
        devices.sort(key=lambda d: (not d.is_default, d.clean_name))
        return devices

    def set_device_volume(self, device_id: str, volume_percent: int) -> bool:
        """Sets master volume for a specific playback device (0-100)."""
        vol_scalar = max(0.0, min(1.0, volume_percent / 100.0))
        try:
            all_devs = pycaw.AudioUtilities.GetAllDevices()
            for dev in all_devs:
                if dev.id == device_id:
                    dev.EndpointVolume.SetMasterVolumeLevelScalar(vol_scalar, None)
                    return True
        except Exception as e:
            logger.error(f"Error setting volume for {device_id}: {e}")
        return False

    def toggle_device_mute(self, device_id: str) -> bool:
        """Toggles mute state of a specific playback device."""
        try:
            all_devs = pycaw.AudioUtilities.GetAllDevices()
            for dev in all_devs:
                if dev.id == device_id:
                    current = dev.EndpointVolume.GetMute()
                    dev.EndpointVolume.SetMute(not current, None)
                    return True
        except Exception as e:
            logger.error(f"Error toggling mute for {device_id}: {e}")
        return False

    def get_audio_sessions(self) -> list[AudioSessionInfo]:
        """Returns all running applications that have an audio session."""
        sessions_info = []
        seen_pids = set()

        try:
            raw_sessions = pycaw.AudioUtilities.GetAllSessions()
            for s in raw_sessions:
                if not s.Process:
                    continue

                pid = s.Process.pid
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)

                proc_name = s.Process.name()
                # Skip system background processes if they don't produce meaningful sound
                if proc_name.lower() in ["audiodg.exe", "system"]:
                    continue

                display_name = proc_name.replace(".exe", "").capitalize()
                
                # Try getting window title if any
                win_title = ""
                try:
                    def enum_windows_callback(hwnd, extra):
                        if user32.IsWindowVisible(hwnd):
                            w_pid = wintypes.DWORD()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(w_pid))
                            if w_pid.value == pid:
                                length = user32.GetWindowTextLengthW(hwnd)
                                if length > 0:
                                    buff = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(hwnd, buff, length + 1)
                                    if buff.value.strip():
                                        extra.append(buff.value.strip())
                        return True

                    titles = []
                    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, ctypes.c_void_p)
                    # Simple fallback
                except Exception:
                    pass

                try:
                    vol = round(s.SimpleAudioVolume.GetMasterVolume() * 100)
                    mute = bool(s.SimpleAudioVolume.GetMute())
                except Exception:
                    vol = 100
                    mute = False

                current_dev = self.policy_service.get_app_audio_device(pid)

                sessions_info.append(AudioSessionInfo(
                    pid=pid,
                    name=proc_name,
                    display_name=display_name,
                    window_title=win_title,
                    volume_percent=vol,
                    is_muted=mute,
                    current_device_id=current_dev
                ))
        except Exception as e:
            logger.error(f"Error enumerating audio sessions: {e}")

        sessions_info.sort(key=lambda s: s.display_name.lower())
        return sessions_info

    def set_session_volume(self, pid: int, volume_percent: int) -> bool:
        """Sets volume for a specific application session (0-100)."""
        vol_scalar = max(0.0, min(1.0, volume_percent / 100.0))
        try:
            raw_sessions = pycaw.AudioUtilities.GetAllSessions()
            for s in raw_sessions:
                if s.Process and s.Process.pid == pid:
                    s.SimpleAudioVolume.SetMasterVolume(vol_scalar, None)
                    return True
        except Exception as e:
            logger.error(f"Error setting session volume for PID {pid}: {e}")
        return False

    def toggle_session_mute(self, pid: int) -> bool:
        """Toggles mute state of a specific application session."""
        try:
            raw_sessions = pycaw.AudioUtilities.GetAllSessions()
            for s in raw_sessions:
                if s.Process and s.Process.pid == pid:
                    current = s.SimpleAudioVolume.GetMute()
                    s.SimpleAudioVolume.SetMute(not current, None)
                    return True
        except Exception as e:
            logger.error(f"Error toggling session mute for PID {pid}: {e}")
        return False

    def route_app(self, pid: int, device_id: str | None) -> bool:
        """Directs app audio to the selected device (or default if None)."""
        return self.policy_service.set_app_audio_device(pid, device_id)
