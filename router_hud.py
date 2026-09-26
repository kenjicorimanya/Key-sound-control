import tkinter as tk
from tkinter import ttk
import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger("RouterHUD")
user32 = ctypes.windll.user32

class RouterHUD:
    def __init__(self, audio_manager, config_manager):
        self.audio_manager = audio_manager
        self.config_manager = config_manager
        self.root = None
        self._is_visible = False

    def show(self):
        """Builds and displays the floating Audio Router HUD."""
        if self._is_visible and self.root:
            self.close()
            return

        # Get foreground app details before opening the HUD
        app_info = self.audio_manager.get_foreground_app()
        devices = self.audio_manager.get_playback_devices()
        current_route = self.audio_manager.policy_service.get_app_audio_device(app_info.pid)

        # Create window in main or separate thread
        self.root = tk.Tk()
        self.root.title("Key-sound-control Router")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.96)
        self.root.configure(bg="#1a1b26")

        self._is_visible = True

        # Outer border frame (modern glowing accent)
        border_frame = tk.Frame(self.root, bg="#3b4261", bd=1)
        border_frame.pack(fill=tk.BOTH, expand=True)

        main_frame = tk.Frame(border_frame, bg="#1a1b26", padx=16, pady=14)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # App Header
        header_frame = tk.Frame(main_frame, bg="#1a1b26")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        title_text = app_info.window_title if app_info.window_title else app_info.process_name
        if len(title_text) > 36:
            title_text = title_text[:34] + "..."

        lbl_app = tk.Label(
            header_frame,
            text=f"🔀 {app_info.process_name}",
            font=("Segoe UI", 11, "bold"),
            fg="#7aa2f7",
            bg="#1a1b26",
            anchor="w"
        )
        lbl_app.pack(fill=tk.X)

        if app_info.window_title:
            lbl_title = tk.Label(
                header_frame,
                text=title_text,
                font=("Segoe UI", 9),
                fg="#a9b1d6",
                bg="#1a1b26",
                anchor="w"
            )
            lbl_title.pack(fill=tk.X)

        lbl_prompt = tk.Label(
            main_frame,
            text="Selecciona la salida de audio para esta ventana:",
            font=("Segoe UI", 9, "italic"),
            fg="#565f89",
            bg="#1a1b26",
            anchor="w"
        )
        lbl_prompt.pack(fill=tk.X, pady=(0, 8))

        # Device list frame
        dev_frame = tk.Frame(main_frame, bg="#1a1b26")
        dev_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Option: Default system output
        is_default_active = (current_route is None or current_route == "")
        self._create_device_row(
            dev_frame,
            index=0,
            key_num="0",
            icon="🌐",
            name="Predeterminado de Windows",
            is_selected=is_default_active,
            on_click=lambda: self._select_route(app_info.pid, None)
        )

        # 2. Options: Each active playback device
        for idx, dev in enumerate(devices, start=1):
            key_num = str(idx) if idx <= 9 else ""
            is_active = (current_route == dev.id)
            self._create_device_row(
                dev_frame,
                index=idx,
                key_num=key_num,
                icon=dev.icon,
                name=dev.clean_name,
                is_selected=is_active,
                on_click=lambda d_id=dev.id: self._select_route(app_info.pid, d_id)
            )

        # Keyboard bindings
        self.root.bind("<Escape>", lambda e: self.close())
        self.root.bind("<FocusOut>", lambda e: self.close())
        self.root.bind("0", lambda e: self._select_route(app_info.pid, None))

        for idx, dev in enumerate(devices, start=1):
            if idx <= 9:
                self.root.bind(str(idx), lambda e, d_id=dev.id: self._select_route(app_info.pid, d_id))

        # Positioning (at mouse cursor or screen center)
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
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

        # Boundary checks to keep fully visible on screen
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

    def _create_device_row(self, parent, index, key_num, icon, name, is_selected, on_click):
        bg_col = "#24283b" if is_selected else "#1a1b26"
        hover_col = "#292e42"
        border_col = "#7aa2f7" if is_selected else "#1a1b26"

        row = tk.Frame(parent, bg=bg_col, highlightbackground=border_col, highlightthickness=1, pady=6, padx=8, cursor="hand2")
        row.pack(fill=tk.X, pady=2)

        # Key badge
        badge_text = f"[{key_num}]" if key_num else "   "
        lbl_key = tk.Label(row, text=badge_text, font=("Consolas", 9, "bold"), fg="#bb9af7", bg=bg_col)
        lbl_key.pack(side=tk.LEFT, padx=(0, 6))

        # Icon
        lbl_icon = tk.Label(row, text=icon, font=("Segoe UI Emoji", 11), bg=bg_col)
        lbl_icon.pack(side=tk.LEFT, padx=(0, 8))

        # Device Name
        lbl_name = tk.Label(row, text=name, font=("Segoe UI", 9, "bold" if is_selected else "normal"), fg="#c0caf5" if is_selected else "#a9b1d6", bg=bg_col, anchor="w")
        lbl_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Checkmark if selected
        if is_selected:
            lbl_check = tk.Label(row, text="✓ Activo", font=("Segoe UI", 9, "bold"), fg="#9ece6a", bg=bg_col)
            lbl_check.pack(side=tk.RIGHT, padx=4)

        # Click handler
        def _handle_click(e):
            on_click()

        # Hover effects
        def _on_enter(e):
            if not is_selected:
                row.configure(bg=hover_col)
                lbl_key.configure(bg=hover_col)
                lbl_icon.configure(bg=hover_col)
                lbl_name.configure(bg=hover_col)

        def _on_leave(e):
            if not is_selected:
                row.configure(bg=bg_col)
                lbl_key.configure(bg=bg_col)
                lbl_icon.configure(bg=bg_col)
                lbl_name.configure(bg=bg_col)

        for widget in [row, lbl_key, lbl_icon, lbl_name]:
            widget.bind("<Button-1>", _handle_click)
            widget.bind("<Enter>", _on_enter)
            widget.bind("<Leave>", _on_leave)

    def _select_route(self, pid: int, device_id: str | None):
        """Applies the selected audio route and closes HUD."""
        self.audio_manager.route_app(pid, device_id)
        self.close()

    def close(self):
        """Closes the HUD window."""
        self._is_visible = False
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
