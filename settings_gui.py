import tkinter as tk
from tkinter import ttk, messagebox
import logging
from input_listener import InputListener

logger = logging.getLogger("SettingsGUI")

class SettingsWindow:
    def __init__(self, config_manager, input_listener, audio_manager):
        self.config_manager = config_manager
        self.input_listener = input_listener
        self.audio_manager = audio_manager
        self.root = None

    def show(self):
        if self.root:
            self.root.lift()
            return

        self.root = tk.Tk()
        self.root.title("Key-sound-control - Configuración")
        self.root.geometry("480x520")
        self.root.configure(bg="#1a1b26")
        self.root.resizable(False, False)

        # Center on screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 480) // 2
        y = (sh - 520) // 2
        self.root.geometry(f"+{x}+{y}")

        main_frame = tk.Frame(self.root, bg="#1a1b26", padx=24, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        lbl_head = tk.Label(
            main_frame,
            text="🎧 Key-sound-control",
            font=("Segoe UI", 16, "bold"),
            fg="#7aa2f7",
            bg="#1a1b26"
        )
        lbl_head.pack(anchor="w")

        lbl_sub = tk.Label(
            main_frame,
            text="Configura tus atajos de teclado, botones de ratón y preferencias.",
            font=("Segoe UI", 9),
            fg="#a9b1d6",
            bg="#1a1b26"
        )
        lbl_sub.pack(anchor="w", pady=(2, 16))

        # 1. Hotkey Section
        sec_hotkeys = tk.LabelFrame(
            main_frame,
            text="  Atajos y Botones de Activación  ",
            font=("Segoe UI", 9, "bold"),
            fg="#bb9af7",
            bg="#1a1b26",
            padx=12,
            pady=12,
            bd=1,
            relief=tk.GROOVE
        )
        sec_hotkeys.pack(fill=tk.X, pady=(0, 16))

        # Router Hotkey Row
        self.router_btn_text = tk.StringVar(value=self.config_manager.get("router_hotkey", "alt+a").upper())
        self._create_hotkey_picker(
            sec_hotkeys,
            label="Selector de Salida (Router HUD):",
            str_var=self.router_btn_text,
            config_key="router_hotkey"
        )

        # Mixer Hotkey Row
        self.mixer_btn_text = tk.StringVar(value=self.config_manager.get("mixer_hotkey", "alt+v").upper())
        self._create_hotkey_picker(
            sec_hotkeys,
            label="Mezclador de Volumen (Mixer HUD):",
            str_var=self.mixer_btn_text,
            config_key="mixer_hotkey"
        )

        lbl_hint = tk.Label(
            sec_hotkeys,
            text="💡 Tip: Puedes presionar combinaciones de teclas (ej. Alt+A) o botones extra del ratón (Mouse 4/5).",
            font=("Segoe UI", 8, "italic"),
            fg="#565f89",
            bg="#1a1b26",
            wraplength=400,
            justify="left"
        )
        lbl_hint.pack(fill=tk.X, pady=(10, 0))

        # 2. Preferences Section
        sec_prefs = tk.LabelFrame(
            main_frame,
            text="  Comportamiento  ",
            font=("Segoe UI", 9, "bold"),
            fg="#bb9af7",
            bg="#1a1b26",
            padx=12,
            pady=12,
            bd=1,
            relief=tk.GROOVE
        )
        sec_prefs.pack(fill=tk.X, pady=(0, 16))

        self.var_cursor = tk.BooleanVar(value=self.config_manager.get("spawn_at_cursor", True))
        chk_cursor = tk.Checkbutton(
            sec_prefs,
            text="Mostrar menús flotantes junto al cursor del ratón",
            variable=self.var_cursor,
            command=self._on_change_cursor,
            bg="#1a1b26",
            fg="#c0caf5",
            selectcolor="#24283b",
            activebackground="#1a1b26",
            activeforeground="#7aa2f7",
            font=("Segoe UI", 9)
        )
        chk_cursor.pack(anchor="w", pady=3)

        self.var_startup = tk.BooleanVar(value=self.config_manager.get("start_with_windows", False))
        chk_startup = tk.Checkbutton(
            sec_prefs,
            text="Iniciar automáticamente con Windows",
            variable=self.var_startup,
            command=self._on_change_startup,
            bg="#1a1b26",
            fg="#c0caf5",
            selectcolor="#24283b",
            activebackground="#1a1b26",
            activeforeground="#7aa2f7",
            font=("Segoe UI", 9)
        )
        chk_startup.pack(anchor="w", pady=3)

        # 3. Actions Section
        btn_reset = tk.Button(
            main_frame,
            text="🔄 Restablecer todas las apps al audio predeterminado",
            font=("Segoe UI", 9),
            bg="#24283b",
            fg="#f7768e",
            activebackground="#292e42",
            activeforeground="#f7768e",
            bd=0,
            pady=6,
            cursor="hand2",
            command=self._reset_all_routes
        )
        btn_reset.pack(fill=tk.X, pady=(4, 16))

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.mainloop()

    def _create_hotkey_picker(self, parent, label, str_var, config_key):
        row = tk.Frame(parent, bg="#1a1b26")
        row.pack(fill=tk.X, pady=6)

        lbl = tk.Label(row, text=label, font=("Segoe UI", 9), fg="#c0caf5", bg="#1a1b26")
        lbl.pack(side=tk.LEFT)

        btn = tk.Button(
            row,
            textvariable=str_var,
            font=("Consolas", 9, "bold"),
            bg="#24283b",
            fg="#7aa2f7",
            activebackground="#3b4261",
            activeforeground="#7aa2f7",
            bd=1,
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            width=14
        )
        btn.pack(side=tk.RIGHT)

        def _start_recording():
            btn.config(text="Pulsa una tecla...", fg="#e0af68")
            
            def _on_recorded(key_res):
                if key_res:
                    self.config_manager.set(config_key, key_res)
                    str_var.set(key_res.upper())
                    self.input_listener.update_hotkeys(
                        self.config_manager.get("router_hotkey"),
                        self.config_manager.get("mixer_hotkey")
                    )
                else:
                    str_var.set(self.config_manager.get(config_key).upper())
                btn.config(textvariable=str_var, fg="#7aa2f7")

            InputListener.record_input(_on_recorded, timeout=8.0)

        btn.config(command=_start_recording)

    def _on_change_cursor(self):
        self.config_manager.set("spawn_at_cursor", self.var_cursor.get())

    def _on_change_startup(self):
        val = self.var_startup.get()
        self.config_manager.set_start_with_windows(val)

    def _reset_all_routes(self):
        if messagebox.askyesno("Confirmar", "¿Deseas restablecer todas las asignaciones de audio de aplicaciones al dispositivo predeterminado?"):
            ok = self.audio_manager.policy_service.clear_all_custom_routes()
            if ok:
                messagebox.showinfo("Éxito", "Se restablecieron las salidas de audio a los valores predeterminados de Windows.")
            else:
                messagebox.showwarning("Aviso", "No se pudieron restablecer o no había ninguna regla activa.")

    def close(self):
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None
