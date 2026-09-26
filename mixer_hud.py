import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger("MixerHUD")
user32 = ctypes.windll.user32

class MixerHUD:
    def __init__(self, audio_manager, config_manager):
        self.audio_manager = audio_manager
        self.config_manager = config_manager
        self.root = None
        self._is_visible = False

    def show(self):
        """Builds and displays the floating Volume Mixer HUD."""
        if self._is_visible and self.root:
            self.close()
            return

        devices = self.audio_manager.get_playback_devices()
        sessions = self.audio_manager.get_audio_sessions()

        self.root = tk.Tk()
        self.root.title("Key-sound-control Mixer")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.97)
        self.root.configure(bg="#1a1b26")

        self._is_visible = True

        border_frame = tk.Frame(self.root, bg="#3b4261", bd=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(border_frame, bg="#1a1b26", padx=18, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with Title and Close button
        header_frame = tk.Frame(main_frame, bg="#1a1b26")
        header_frame.pack(fill=tk.X, pady=(0, 12))

        lbl_title = tk.Label(
            header_frame,
            text="🎚️ MEZCLADOR DE VOLUMEN",
            font=("Segoe UI", 10, "bold"),
            fg="#7aa2f7",
            bg="#1a1b26"
        )
        lbl_title.pack(side=tk.LEFT)

        btn_close = tk.Label(
            header_frame,
            text="✕",
            font=("Segoe UI", 10, "bold"),
            fg="#565f89",
            bg="#1a1b26",
            cursor="hand2"
        )
        btn_close.pack(side=tk.RIGHT)
        btn_close.bind("<Button-1>", lambda e: self.close())
        btn_close.bind("<Enter>", lambda e: btn_close.configure(fg="#f7768e"))
        btn_close.bind("<Leave>", lambda e: btn_close.configure(fg="#565f89"))

        # Scrollable container for many devices/apps
        content_container = tk.Frame(main_frame, bg="#1a1b26")
        content_container.pack(fill=tk.BOTH, expand=True)

        # 1. SECTION: Physical Output Devices
        lbl_sec1 = tk.Label(
            content_container,
            text="DISPOSITIVOS DE SALIDA:",
            font=("Segoe UI", 8, "bold"),
            fg="#9aa5ce",
            bg="#1a1b26",
            anchor="w"
        )
        lbl_sec1.pack(fill=tk.X, pady=(4, 6))

        for dev in devices:
            self._create_volume_row(
                parent=content_container,
                icon=dev.icon,
                title=dev.clean_name,
                current_vol=dev.volume_percent,
                is_muted=dev.is_muted,
                on_change=lambda val, d_id=dev.id: self.audio_manager.set_device_volume(d_id, val),
                on_mute_toggle=lambda d_id=dev.id: self._toggle_dev_mute(d_id)
            )

        # 2. SECTION: Active App Sessions
        if sessions:
            lbl_sec2 = tk.Label(
                content_container,
                text="APLICACIONES ACTIVAS:",
                font=("Segoe UI", 8, "bold"),
                fg="#9aa5ce",
                bg="#1a1b26",
                anchor="w"
            )
            lbl_sec2.pack(fill=tk.X, pady=(12, 6))

            for s in sessions:
                self._create_volume_row(
                    parent=content_container,
                    icon="🎵" if "spotify" in s.name.lower() else "🌐" if "chrome" in s.name.lower() or "msedge" in s.name.lower() else "📱",
                    title=s.display_name,
                    current_vol=s.volume_percent,
                    is_muted=s.is_muted,
                    on_change=lambda val, pid=s.pid: self.audio_manager.set_session_volume(pid, val),
                    on_mute_toggle=lambda pid=s.pid: self._toggle_session_mute(pid)
                )

        # Bindings
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<FocusOut>", lambda e: self.close())

        # Positioning
        self.root.update_idletasks()
        w = max(420, self.root.winfo_reqwidth())
        h = self.root.winfo_reqheight()

        if self.config_manager.get("spawn_at_cursor", True):
            pt = wintypes.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            x = pt.x + 10
            y = pt.y + 10
        else:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - w) // 2
            y = (screen_h - h) // 2

        # Boundary checks
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if x + w > screen_w:
            x = screen_w - w - 15
        if y + h > screen_h:
            y = screen_h - h - 40
        if x < 0:
            x = 10
        if y < 0:
            y = 10

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.focus_force()
        self.root.mainloop()

    def _create_volume_row(self, parent, icon, title, current_vol, is_muted, on_change, on_mute_toggle):
        row = tk.Frame(parent, bg="#24283b", pady=6, padx=10, bd=0)
        row.pack(fill=tk.X, pady=3)

        # Icon
        lbl_icon = tk.Label(row, text=icon, font=("Segoe UI Emoji", 10), bg="#24283b")
        lbl_icon.pack(side=tk.LEFT, padx=(0, 6))

        # Title
        display_title = title if len(title) <= 20 else title[:18] + ".."
        lbl_title = tk.Label(
            row,
            text=display_title,
            font=("Segoe UI", 9),
            fg="#c0caf5",
            bg="#24283b",
            width=18,
            anchor="w"
        )
        lbl_title.pack(side=tk.LEFT, padx=(0, 8))

        # Volume Percent Label
        vol_var = tk.IntVar(value=current_vol)
        lbl_pct = tk.Label(
            row,
            text=f"{current_vol}%",
            font=("Consolas", 8, "bold"),
            fg="#7aa2f7" if not is_muted else "#565f89",
            bg="#24283b",
            width=4,
            anchor="e"
        )

        # Scale slider
        def _on_scale(val_str):
            v = int(float(val_str))
            vol_var.set(v)
            lbl_pct.config(text=f"{v}%")
            on_change(v)

        slider = tk.Scale(
            row,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            showvalue=False,
            variable=vol_var,
            command=_on_scale,
            bg="#24283b",
            fg="#7aa2f7",
            troughcolor="#16161e",
            activebackground="#7aa2f7",
            highlightthickness=0,
            bd=0,
            sliderrelief=tk.FLAT,
            length=130
        )
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)

        lbl_pct.pack(side=tk.LEFT, padx=(4, 8))

        # Mute button
        mute_symbol = "🔇" if is_muted else "🔊"
        btn_mute = tk.Label(
            row,
            text=mute_symbol,
            font=("Segoe UI Emoji", 11),
            bg="#24283b",
            fg="#f7768e" if is_muted else "#9ece6a",
            cursor="hand2"
        )
        btn_mute.pack(side=tk.RIGHT)

        def _handle_mute(e):
            on_mute_toggle()
            # Toggle display
            now_muted = btn_mute.cget("text") == "🔊"
            btn_mute.config(
                text="🔇" if now_muted else "🔊",
                fg="#f7768e" if now_muted else "#9ece6a"
            )
            lbl_pct.config(fg="#565f89" if now_muted else "#7aa2f7")

        btn_mute.bind("<Button-1>", _handle_mute)

        # Mouse wheel support: Hover over row or slider to scroll volume
        def _on_mousewheel(event):
            delta = 4 if event.delta > 0 else -4
            new_v = max(0, min(100, vol_var.get() + delta))
            vol_var.set(new_v)
            slider.set(new_v)
            _on_scale(str(new_v))

        for w in [row, lbl_icon, lbl_title, slider, lbl_pct]:
            w.bind("<MouseWheel>", _on_mousewheel)

    def _toggle_dev_mute(self, device_id: str):
        self.audio_manager.toggle_device_mute(device_id)

    def _toggle_session_mute(self, pid: int):
        self.audio_manager.toggle_session_mute(pid)

    def close(self):
        """Closes the mixer overlay window."""
        self._is_visible = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
