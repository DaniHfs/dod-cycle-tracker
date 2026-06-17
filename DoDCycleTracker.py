import tkinter as tk
import time
import threading
import json
import os
import winsound
import keyboard

class DayOfDragonsTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("DoD Crystal Tracker")
        self.config_file = "config.json"
        
        # Default keybind setup
        self.hotkeys = {
            "despawn": {"key": "F8", "label_prefix": "Active Timer"},
            "day": {"key": "F6", "label_prefix": "Sync Day"},
            "night": {"key": "F7", "label_prefix": "Sync Night"}
        }
        self.window_position = "+20+20" # Standard top-left screen default

        # Sound settings are stored in config.json.
        # Open config.json if you want to change pitch values or mute sounds.
        self.sound_enabled = True
        self.spawn_pitch = 800
        self.despawn_pitch = 1200
        self.despawn_beep_triggered = False
        self.spawn_beep_triggered = False
        
        self.load_config()
        
        # Set up the transparent overlay box
        self.root.geometry(f"260x220{self.window_position}")  
        self.root.overrideredirect(True)     
        self.root.wm_attributes("-topmost", True) 
        self.root.config(bg='#111111')
        self.root.attributes("-alpha", 0.85) 
        
        # Mouse clicking and dragging logic
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        self.root.bind("<ButtonRelease-1>", self.end_drag) # Save location when let go
        
        self.is_changing_key = False
        self.despawn_end_time = 0  
        self.current_phase_cache = None 
        
        # Day and night cycle timers (in seconds)
        self.DAY_DURATION = 8400   # 2 Hours 20 Minutes
        self.total_cycle = 14400   # 4 Hours total loop
        self.start_time = time.time()
        
        # In-game phase trackers
        self.label_title = tk.Label(root, text="CURRENT PHASE", font=("Arial", 9, "bold"), fg="#aaaaaa", bg="#111111")
        self.label_title.pack(pady=(5, 0))
        
        self.label_time = tk.Label(root, text="00:00:00", font=("Arial", 18, "bold"), fg="#00ff00", bg="#111111")
        self.label_time.pack()
        
        # Upcoming spawn window warning
        self.warning_label = tk.Label(root, text="✓ Mid-Cycle Phase Stable", font=("Arial", 10, "bold"), fg="#00ff00", bg="#111111")
        self.warning_label.pack(pady=(2, 5))
        
        # Crystal active countdown
        self.despawn_title = tk.Label(root, text="CRYSTAL ACTIVE", font=("Arial", 9, "bold"), fg="#555555", bg="#111111")
        self.despawn_title.pack(pady=(5, 0))
        
        self.despawn_time = tk.Label(root, text="NO ACTIVE SPAWN", font=("Arial", 14, "bold"), fg="#555555", bg="#111111")
        self.despawn_time.pack()

        # Menu for button binds
        self.key_frame = tk.Frame(root, bg="#111111")
        self.key_frame.pack(pady=(8, 5))
        
        for idx, (target, cfg) in enumerate(self.hotkeys.items()):
            cfg["lbl_obj"] = tk.Label(self.key_frame, text=f"{cfg['label_prefix']}: [{cfg['key']}]", font=("Arial", 8), fg="#888888", bg="#111111")
            cfg["lbl_obj"].grid(row=idx, column=0, sticky="w", padx=5)
            
            cfg["btn_obj"] = tk.Button(self.key_frame, text="Change", font=("Arial", 7), command=lambda t=target: self.start_key_rebind(t), bg="#2a2a2a", fg="#ffffff", bd=0)
            cfg["btn_obj"].grid(row=idx, column=1, pady=1)

        self.update_clock()
        
        # Start looking for key presses in the background
        threading.Thread(target=self.global_hardware_listener, daemon=True).start()

    # --- SAVE AND LOAD ENGINE ---
    def load_config(self):
        """ Pull user settings if the config file exists """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.window_position = data.get("position", "+20+20")
                    self.sound_enabled = data.get("sound_enabled", self.sound_enabled)
                    self.spawn_pitch = data.get("spawn_pitch", self.spawn_pitch)
                    self.despawn_pitch = data.get("despawn_pitch", self.despawn_pitch)
                    saved_keys = data.get("keys", {})
                    for target in self.hotkeys:
                        if target in saved_keys:
                            self.hotkeys[target]["key"] = saved_keys[target]
            except Exception:
                pass # Default back to standard setup if file is broken

    def save_config(self):
        """ Save keybind choices and screen position to the file """
        try:
            config_data = {
                "position": f"+{self.root.winfo_x()}+{self.root.winfo_y()}",
                "keys": {target: cfg["key"] for target, cfg in self.hotkeys.items()},
                "sound_enabled": self.sound_enabled,
                "spawn_pitch": self.spawn_pitch,
                "despawn_pitch": self.despawn_pitch
            }
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=4)
        except Exception:
            pass

    # --- MOUSE DRAGGING LOGIC ---
    def play_beep(self, frequency=1000, duration=200):
        """Play a low-overhead beep in the background so Tkinter does not freeze."""
        if not self.sound_enabled:
            return
        threading.Thread(target=lambda: winsound.Beep(frequency, duration), daemon=True).start()

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def drag_window(self, event):
        x = self.root.winfo_x() - self.drag_x + event.x
        y = self.root.winfo_y() - self.drag_y + event.y
        self.root.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        self.save_config() # Save coordinates when player releases mouse button

    # --- MAIN HOTKEY CONTROLS ---
    def global_hardware_listener(self):
        """ Background loop that runs constantly to detect hotkeys while playing """
        while True:
            event = keyboard.read_event()
            if event.event_type == 'down' and not self.is_changing_key:
                pressed_key = event.name.upper()
                
                if pressed_key == self.hotkeys["despawn"]["key"]:
                    self.despawn_end_time = time.time() + 1200 # Set 20 min timer
                    self.despawn_beep_triggered = False
                    self.root.after(0, lambda: self.despawn_title.config(text="⚠️ CRYSTAL DESPAWNING", fg="#ff3333"))
                    
                elif pressed_key == self.hotkeys["day"]["key"]:
                    self.start_time = time.time()
                    
                elif pressed_key == self.hotkeys["night"]["key"]:
                    self.start_time = time.time() - self.DAY_DURATION

    def start_key_rebind(self, target):
        self.is_changing_key = True
        for cfg in self.hotkeys.values():
            cfg["btn_obj"].config(state="disabled")
            
        self.hotkeys[target]["btn_obj"].config(text="Press...", bg="#442222")
        threading.Thread(target=self.wait_for_new_key, args=(target,), daemon=True).start()

    def wait_for_new_key(self, target):
        new_key = keyboard.read_event(allowed_types=['down'])
        self.hotkeys[target]["key"] = new_key.name.upper()
        self.root.after(0, self.finish_key_rebind)

    def finish_key_rebind(self):
        for target, cfg in self.hotkeys.items():
            cfg["lbl_obj"].config(text=f"{cfg['label_prefix']}: [{cfg['key']}]")
            cfg["btn_obj"].config(text="Change", state="normal", bg="#2a2a2a")
        self.is_changing_key = False
        self.save_config()

    # --- CLOCK ENGINE ---
    def update_clock(self):
        current_now = time.time()
        elapsed = (current_now - self.start_time) % self.total_cycle
        
        # Work out if we are currently in day or night phase
        is_daytime = elapsed < self.DAY_DURATION
        if is_daytime != self.current_phase_cache:
            self.current_phase_cache = is_daytime
            if is_daytime:
                self.label_title.config(text="DAY PHASE (Elder %)", fg="#ffcc00")
                self.label_time.config(fg="#ffcc00")
            else:
                self.label_title.config(text="NIGHT PHASE (Element)", fg="#00ccff")
                self.label_time.config(fg="#00ccff")
        
        remaining = (self.DAY_DURATION - elapsed) if is_daytime else (self.total_cycle - elapsed)
        mins, secs = divmod(int(remaining), 60)
        hours, mins = divmod(mins, 60)
        self.label_time.config(text=f"{hours:02d}:{mins:02d}:{secs:02d}")
        
        # 30-Minute cycle tick tracker to show crystal windows
        time_into_phase = elapsed if is_daytime else (elapsed - self.DAY_DURATION)
        time_until_next_spawn_tick = 1800 - (time_into_phase % 1800)
        
        if time_until_next_spawn_tick <= 180:
            w_mins, w_secs = divmod(int(time_until_next_spawn_tick), 60)
            self.warning_label.config(text=f"🚨 SPAWN WINDOW CLOSING: {w_mins:02d}:{w_secs:02d}!", fg="#ff3333")
            if not self.spawn_beep_triggered:
                self.play_beep(self.spawn_pitch, 300)
                self.spawn_beep_triggered = True
        else:
            if self.warning_label.cget("text") != "✓ Mid-Cycle Phase Stable":
                self.warning_label.config(text="✓ Mid-Cycle Phase Stable", fg="#00ff00")
            self.spawn_beep_triggered = False
        
        # Updates active despawn countdown
        if self.despawn_end_time > current_now:
            d_mins, d_secs = divmod(int(self.despawn_end_time - current_now), 60)
            self.despawn_time.config(text=f"{d_mins:02d}:{d_secs:02d}", fg="#ff3333")
        else:
            if self.despawn_title.cget("text") == "⚠️ CRYSTAL DESPAWNING" and not self.despawn_beep_triggered:
                self.despawn_beep_triggered = True
                self.play_beep(self.despawn_pitch, 150)
                self.root.after(200, lambda: self.play_beep(self.despawn_pitch, 150))
            if self.despawn_title.cget("text") != "CRYSTAL ACTIVE":
                self.despawn_title.config(text="CRYSTAL ACTIVE", fg="#555555")
                self.despawn_time.config(text="NO ACTIVE SPAWN", fg="#555555")

        self.root.after(1000, self.update_clock)

if __name__ == "__main__":
    root = tk.Tk()
    app = DayOfDragonsTimer(root)
    root.mainloop()
