import threading
import time
import logging
import keyboard
import mouse

logger = logging.getLogger("InputListener")

class InputListener:
    def __init__(self, on_router_trigger, on_mixer_trigger):
        self.on_router_trigger = on_router_trigger
        self.on_mixer_trigger = on_mixer_trigger
        
        self.router_hotkey = "alt+a"
        self.mixer_hotkey = "alt+v"
        
        self._running = False
        self._keyboard_hooks = []
        self._mouse_hook = None
        self._lock = threading.Lock()

    def update_hotkeys(self, router_hotkey: str, mixer_hotkey: str):
        """Updates active hotkeys dynamically."""
        with self._lock:
            self.router_hotkey = router_hotkey.lower().strip()
            self.mixer_hotkey = mixer_hotkey.lower().strip()
            self._rebind()

    def _is_mouse_button(self, hotkey: str) -> bool:
        return hotkey in ["xbutton1", "xbutton2", "mouse4", "mouse5", "middle", "wheel"]

    def _rebind(self):
        """Clears existing hooks and registers new triggers."""
        try:
            # Unhook keyboard hotkeys
            for h in self._keyboard_hooks:
                try:
                    keyboard.remove_hotkey(h)
                except Exception:
                    pass
            self._keyboard_hooks.clear()

            # Unhook mouse
            if self._mouse_hook:
                try:
                    mouse.unhook(self._mouse_hook)
                except Exception:
                    pass
                self._mouse_hook = None

            # Bind Router Hotkey
            if not self._is_mouse_button(self.router_hotkey):
                try:
                    hk = keyboard.add_hotkey(self.router_hotkey, self._safe_router_trigger)
                    self._keyboard_hooks.append(hk)
                    logger.info(f"Keyboard router hotkey registered: {self.router_hotkey}")
                except Exception as e:
                    logger.error(f"Failed to register keyboard router hotkey '{self.router_hotkey}': {e}")

            # Bind Mixer Hotkey
            if not self._is_mouse_button(self.mixer_hotkey):
                try:
                    hk = keyboard.add_hotkey(self.mixer_hotkey, self._safe_mixer_trigger)
                    self._keyboard_hooks.append(hk)
                    logger.info(f"Keyboard mixer hotkey registered: {self.mixer_hotkey}")
                except Exception as e:
                    logger.error(f"Failed to register keyboard mixer hotkey '{self.mixer_hotkey}': {e}")

            # If either uses mouse, hook mouse events
            if self._is_mouse_button(self.router_hotkey) or self._is_mouse_button(self.mixer_hotkey):
                self._mouse_hook = mouse.hook(self._on_mouse_event)
                logger.info(f"Mouse listener registered for buttons: {self.router_hotkey}, {self.mixer_hotkey}")

        except Exception as e:
            logger.error(f"Error rebinding input hooks: {e}")

    def _safe_router_trigger(self):
        try:
            threading.Thread(target=self.on_router_trigger, daemon=True).start()
        except Exception as e:
            logger.error(f"Error executing router trigger: {e}")

    def _safe_mixer_trigger(self):
        try:
            threading.Thread(target=self.on_mixer_trigger, daemon=True).start()
        except Exception as e:
            logger.error(f"Error executing mixer trigger: {e}")

    def _on_mouse_event(self, event):
        """Processes low-level mouse button clicks (XButton1, XButton2, middle)."""
        if not isinstance(event, mouse.ButtonEvent) or event.event_type != mouse.DOWN:
            return

        btn = event.button.lower() if isinstance(event.button, str) else str(event.button).lower()
        
        # Normalize button names
        btn_normalized = btn
        if btn in ["x", "x1", "mouse4", "back"]:
            btn_normalized = "xbutton1"
        elif btn in ["x2", "mouse5", "forward"]:
            btn_normalized = "xbutton2"

        if btn_normalized == self.router_hotkey or btn == self.router_hotkey:
            self._safe_router_trigger()
        elif btn_normalized == self.mixer_hotkey or btn == self.mixer_hotkey:
            self._safe_mixer_trigger()

    def start(self, router_hotkey: str, mixer_hotkey: str):
        self._running = True
        self.update_hotkeys(router_hotkey, mixer_hotkey)

    def stop(self):
        self._running = False
        with self._lock:
            for h in self._keyboard_hooks:
                try:
                    keyboard.remove_hotkey(h)
                except Exception:
                    pass
            self._keyboard_hooks.clear()

            if self._mouse_hook:
                try:
                    mouse.unhook(self._mouse_hook)
                except Exception:
                    pass
                self._mouse_hook = None

    @staticmethod
    def record_input(callback, timeout: float = 10.0):
        """
        Records the next key combination or mouse button pressed by the user.
        Executes callback(result_str).
        """
        def _worker():
            recorded = [None]
            done = threading.Event()

            def _on_key(e):
                if done.is_set():
                    return
                # Ignore key release
                if e.event_type == keyboard.KEY_DOWN:
                    # If it's a lone modifier, wait for full combo
                    if e.name in ["ctrl", "alt", "shift", "windows", "left ctrl", "right ctrl", "left alt", "right alt"]:
                        return
                    
                    # Construct combo
                    combo = []
                    if keyboard.is_pressed("ctrl"):
                        combo.append("ctrl")
                    if keyboard.is_pressed("alt"):
                        combo.append("alt")
                    if keyboard.is_pressed("shift"):
                        combo.append("shift")
                    if keyboard.is_pressed("windows"):
                        combo.append("win")

                    key_name = e.name.lower()
                    if key_name not in combo:
                        combo.append(key_name)

                    recorded[0] = "+".join(combo)
                    done.set()

            def _on_mouse(e):
                if done.is_set():
                    return
                if isinstance(e, mouse.ButtonEvent) and e.event_type == mouse.DOWN:
                    btn = e.button.lower() if isinstance(e.button, str) else str(e.button).lower()
                    if btn in ["x", "x1", "mouse4", "back"]:
                        recorded[0] = "xbutton1"
                        done.set()
                    elif btn in ["x2", "mouse5", "forward"]:
                        recorded[0] = "xbutton2"
                        done.set()
                    elif btn in ["middle", "wheel"]:
                        recorded[0] = "middle"
                        done.set()

            kb_hook = keyboard.hook(_on_key)
            ms_hook = mouse.hook(_on_mouse)

            done.wait(timeout=timeout)

            try:
                keyboard.unhook(kb_hook)
            except Exception:
                pass
            try:
                mouse.unhook(ms_hook)
            except Exception:
                pass

            result = recorded[0] if recorded[0] else ""
            callback(result)

        threading.Thread(target=_worker, daemon=True).start()
