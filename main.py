import os
import sys
import threading
import logging
from PIL import Image, ImageDraw
import pystray

from config_manager import ConfigManager
from audio_manager import AudioManager
from input_listener import InputListener
from router_hud import RouterHUD
from mixer_hud import MixerHUD
from settings_gui import SettingsWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("KeySoundControl")

class KeySoundControlApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.audio_manager = AudioManager()

        self.router_hud = RouterHUD(self.audio_manager, self.config_manager)
        self.mixer_hud = MixerHUD(self.audio_manager, self.config_manager)
        
        self.input_listener = InputListener(
            on_router_trigger=self.trigger_router_hud,
            on_mixer_trigger=self.trigger_mixer_hud
        )
        self.settings_window = SettingsWindow(
            self.config_manager,
            self.input_listener,
            self.audio_manager
        )

        self.tray_icon = None

    def trigger_router_hud(self):
        logger.info("Triggered Router HUD")
        # Run HUD in main or UI thread
        self.router_hud.show()

    def trigger_mixer_hud(self):
        logger.info("Triggered Mixer HUD")
        self.mixer_hud.show()

    def open_settings(self):
        threading.Thread(target=self.settings_window.show, daemon=True).start()

    def _create_tray_image(self):
        """Generates a stylish modern sound icon for the Windows taskbar."""
        width = 64
        height = 64
        image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw rounded background circle (deep blue/purple)
        draw.ellipse([4, 4, 60, 60], fill="#7aa2f7")

        # Draw speaker icon shape in white
        # Base
        draw.rectangle([18, 26, 26, 38], fill="#1a1b26")
        # Cone
        draw.polygon([(26, 26), (38, 16), (38, 48), (26, 38)], fill="#1a1b26")
        # Sound waves
        draw.arc([36, 22, 48, 42], start=-60, end=60, fill="#1a1b26", width=3)
        draw.arc([42, 16, 56, 48], start=-60, end=60, fill="#1a1b26", width=3)

        return image

    def run(self):
        logger.info("Starting Key-sound-control background service...")

        # Start input listener
        router_hk = self.config_manager.get("router_hotkey", "alt+a")
        mixer_hk = self.config_manager.get("mixer_hotkey", "alt+v")
        self.input_listener.start(router_hk, mixer_hk)

        # Build System Tray Icon
        icon_img = self._create_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("🎧 Key-sound-control", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🔀 Selector de Salida (HUD 1)", lambda: threading.Thread(target=self.trigger_router_hud, daemon=True).start()),
            pystray.MenuItem("🎚️ Mezclador de Volumen (HUD 2)", lambda: threading.Thread(target=self.trigger_mixer_hud, daemon=True).start()),
            pystray.MenuItem("⚙️ Configuración", self.open_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Salir", self.quit)
        )

        self.tray_icon = pystray.Icon(
            "KeySoundControl",
            icon_img,
            "Key-sound-control (Enrutador y Mezclador)",
            menu
        )

        # Run tray loop
        self.tray_icon.run()

    def quit(self):
        logger.info("Stopping Key-sound-control...")
        self.input_listener.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        sys.exit(0)

if __name__ == "__main__":
    app = KeySoundControlApp()
    app.run()
