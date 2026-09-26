import json
import os
import sys
import winreg
import logging

logger = logging.getLogger("ConfigManager")

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
RUN_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "KeySoundControl"

DEFAULT_CONFIG = {
    "router_hotkey": "alt+a",
    "mixer_hotkey": "alt+v",
    "spawn_at_cursor": True,
    "start_with_windows": False,
    "remember_assignments": True,
    "assignments": {}
}

class ConfigManager:
    def __init__(self):
        self.config = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                logger.error(f"Error loading config.json: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config.json: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

    def set_start_with_windows(self, enable: bool) -> bool:
        """Configures Windows Run registry key to auto-start on boot."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_SET_VALUE)
            if enable:
                python_exe = sys.executable
                main_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
                cmd = f'"{python_exe}" "{main_py}"'
                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_REG_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            self.set("start_with_windows", enable)
            return True
        except Exception as e:
            logger.error(f"Error updating Windows startup registry: {e}")
            return False
