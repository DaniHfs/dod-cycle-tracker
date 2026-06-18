"""Day of Dragons overlay timer with transparent window and hotkey support.
"""

import json
import os
import threading
import time
import tkinter as tk
import winsound
import keyboard


class DayOfDragonsTimer:
    """Overlay timer for Day of Dragons with keyboard hotkeys and config save/load."""

    def __init__(self, root):
        self.root = root
        self.root.title("DoD Crystal Tracker")

        self.config_path = "config.json"
        self.window_position = "+20+20"

        self.hotkeys = {
            "despawn": {"key": "F8", "label_prefix": "Active Timer"},
            "day": {"key": "F6", "label_prefix": "Sync Day"},
            "night": {"key": "F7", "label_prefix": "Sync Night"},
        }

        self.sound_enabled = True
        self.spawn_pitch = 800
        self.despawn_pitch = 1200

        self.despawn_end_time = 0
        self.spawn_beep_triggered = False
        self.despawn_beep_triggered = False
        self.current_phase_cache = None
        self.is_changing_key = False

        self.load_config()

        self.root.geometry(f"260x220{self.window_position}")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)
        self.root.config(bg="#111111")
        self.root.attributes("-alpha", 0.85)

        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.drag_window)
        self.root.bind("<ButtonRelease-1>", self.end_drag)
        self.root.bind("<Button-3>", lambda event: self.root.destroy())

        self.day_duration = 8400
        self.total_cycle = 14400
        self.start_time = time.time()

        self.title_label = tk.Label(
            root,
            text="CURRENT PHASE",
            font=("Arial", 9, "bold"),
            fg="#aaaaaa",
            bg="#111111",
        )
        self.title_label.pack(pady=(5, 0))

        self.time_label = tk.Label(
            root,
            text="00:00:00",
            font=("Arial", 18, "bold"),
            fg="#00ff00",
            bg="#111111",
        )
        self.time_label.pack()

        self.warning_label = tk.Label(
            root,
            text="✓ Mid-Cycle Phase Stable",
            font=("Arial", 10, "bold"),
            fg="#00ff00",
            bg="#111111",
        )
        self.warning_label.pack(pady=(2, 5))

        self.despawn_title_label = tk.Label(
            root,
            text="CRYSTAL ACTIVE",
            font=("Arial", 9, "bold"),
            fg="#555555",
            bg="#111111",
        )
        self.despawn_title_label.pack(pady=(5, 0))

        self.despawn_time_label = tk.Label(
            root,
            text="NO ACTIVE CRYSTAL",
            font=("Arial", 14, "bold"),
            fg="#555555",
            bg="#111111",
        )
        self.despawn_time_label.pack()

        self.key_frame = tk.Frame(root, bg="#111111")
        self.key_frame.pack(pady=(8, 5))

        for idx, (target, config) in enumerate(self.hotkeys.items()):
            config["label_widget"] = tk.Label(
                self.key_frame,
                text=f"{config['label_prefix']}: [{config['key']}]",
                font=("Arial", 8),
                fg="#888888",
                bg="#111111",
            )
            config["label_widget"].grid(row=idx, column=0, sticky="w", padx=5)

            config["button_widget"] = tk.Button(
                self.key_frame,
                text="Change",
                font=("Arial", 7),
                command=lambda t=target: self.start_key_rebind(t),
                bg="#2a2a2a",
                fg="#ffffff",
                bd=0,
            )
            config["button_widget"].grid(row=idx, column=1, pady=1)

        self.update_clock()
        threading.Thread(target=self.global_hardware_listener, daemon=True).start()

    def load_config(self):
        """Load saved hotkeys and overlay position from the config file."""
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r") as config_file:
                data = json.load(config_file)

            self.window_position = data.get("position", self.window_position)
            self.sound_enabled = data.get("sound_enabled", self.sound_enabled)
            self.spawn_pitch = data.get("spawn_pitch", self.spawn_pitch)
            self.despawn_pitch = data.get("despawn_pitch", self.despawn_pitch)

            saved_keys = data.get("keys", {})
            for target in self.hotkeys:
                if target in saved_keys:
                    self.hotkeys[target]["key"] = saved_keys[target]
        except Exception:
            pass

    def save_config(self):
        """Write current hotkeys and window position back to config.json."""
        try:
            config_data = {
                "position": f"+{self.root.winfo_x()}+{self.root.winfo_y()}",
                "keys": {target: config["key"] for target, config in self.hotkeys.items()},
                "sound_enabled": self.sound_enabled,
                "spawn_pitch": self.spawn_pitch,
                "despawn_pitch": self.despawn_pitch,
            }

            with open(self.config_path, "w") as config_file:
                json.dump(config_data, config_file, indent=4)
        except Exception:
            pass

    def play_beep(self, frequency=1000, duration=200):
        """Play a quick beep without blocking the Tkinter UI."""
        if not self.sound_enabled:
            return

        threading.Thread(
            target=lambda: winsound.Beep(frequency, duration),
            daemon=True,
        ).start()

    def start_drag(self, event):
        """Remember the mouse offset so the overlay can move smoothly."""
        self.drag_offset_x = event.x
        self.drag_offset_y = event.y

    def drag_window(self, event):
        """Move the window while the player is dragging it."""
        x = self.root.winfo_x() - self.drag_offset_x + event.x
        y = self.root.winfo_y() - self.drag_offset_y + event.y
        self.root.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        """Save the window position once dragging is finished."""
        self.save_config()

    def global_hardware_listener(self):
        """Run a background loop that catches hotkeys during play."""
        while True:
            event = keyboard.read_event()
            if event.event_type != "down" or self.is_changing_key:
                continue

            pressed_key = event.name.upper()

            if pressed_key == self.hotkeys["despawn"]["key"]:
                if self.despawn_end_time > time.time():
                    self.despawn_end_time = 0
                    self.root.after(
                        0,
                        lambda: self.despawn_title_label.config(text="CRYSTAL ACTIVE", fg="#555555"),
                    )
                    self.root.after(
                        0,
                        lambda: self.despawn_time_label.config(text="NO ACTIVE SPAWN", fg="#555555"),
                    )
                else:
                    self.despawn_end_time = time.time() + 1200
                    self.despawn_beep_triggered = False
                    self.root.after(
                        0,
                        lambda: self.despawn_title_label.config(text="⚠️ CRYSTAL DESPAWNING", fg="#ff3333"),
                    )

            elif pressed_key == self.hotkeys["day"]["key"]:
                self.start_time = time.time()

            elif pressed_key == self.hotkeys["night"]["key"]:
                self.start_time = time.time() - self.day_duration

    def start_key_rebind(self, target):
        """Begin a keybind change for the selected hotkey."""
        self.is_changing_key = True

        for config in self.hotkeys.values():
            config["button_widget"].config(state="disabled")

        self.hotkeys[target]["button_widget"].config(text="Press...", bg="#442222")
        threading.Thread(target=self.wait_for_new_key, args=(target,), daemon=True).start()

    def wait_for_new_key(self, target):
        """Wait for the next key press and assign it to the hotkey."""
        new_key_event = keyboard.read_event(allowed_types=["down"])
        self.hotkeys[target]["key"] = new_key_event.name.upper()
        self.root.after(0, self.finish_key_rebind)

    def finish_key_rebind(self):
        """Update the UI after a keybind has been changed."""
        for config in self.hotkeys.values():
            config["label_widget"].config(text=f"{config['label_prefix']}: [{config['key']}]")
            config["button_widget"].config(text="Change", state="normal", bg="#2a2a2a")

        self.is_changing_key = False
        self.save_config()

    def update_clock(self):
        """Refresh the timer display and handle phase warnings."""
        current_time = time.time()
        elapsed = (current_time - self.start_time) % self.total_cycle
        is_daytime = elapsed < self.day_duration

        if is_daytime != self.current_phase_cache:
            self.current_phase_cache = is_daytime

            if is_daytime:
                self.title_label.config(text="DAY PHASE (Elder %)", fg="#ffcc00")
                self.time_label.config(fg="#ffcc00")
            else:
                self.title_label.config(text="NIGHT PHASE (Element)", fg="#00ccff")
                self.time_label.config(fg="#00ccff")

        remaining = self.day_duration - elapsed if is_daytime else self.total_cycle - elapsed
        hours, remainder = divmod(int(remaining), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        time_into_phase = elapsed if is_daytime else elapsed - self.day_duration
        time_until_next_spawn_tick = 1800 - (time_into_phase % 1800)

        if time_until_next_spawn_tick <= 180:
            window_minutes, window_seconds = divmod(int(time_until_next_spawn_tick), 60)
            self.warning_label.config(
                text=f"🚨 SPAWN WINDOW CLOSING: {window_minutes:02d}:{window_seconds:02d}!",
                fg="#ff3333",
            )

            if not self.spawn_beep_triggered:
                self.play_beep(self.spawn_pitch, 300)
                self.spawn_beep_triggered = True
        else:
            if self.warning_label.cget("text") != "✓ Mid-Cycle Phase Stable":
                self.warning_label.config(text="✓ Mid-Cycle Phase Stable", fg="#00ff00")

            self.spawn_beep_triggered = False

        if self.despawn_end_time > current_time:
            despawn_remaining = int(self.despawn_end_time - current_time)
            despawn_minutes, despawn_seconds = divmod(despawn_remaining, 60)
            self.despawn_time_label.config(text=f"{despawn_minutes:02d}:{despawn_seconds:02d}", fg="#ff3333")
        else:
            if self.despawn_title_label.cget("text") == "⚠️ CRYSTAL DESPAWNING" and not self.despawn_beep_triggered:
                self.despawn_beep_triggered = True
                self.play_beep(self.despawn_pitch, 150)
                self.root.after(200, lambda: self.play_beep(self.despawn_pitch, 150))

            if self.despawn_title_label.cget("text") != "CRYSTAL ACTIVE":
                self.despawn_title_label.config(text="CRYSTAL ACTIVE", fg="#555555")
                self.despawn_time_label.config(text="NO ACTIVE SPAWN", fg="#555555")

        self.root.after(1000, self.update_clock)


if __name__ == "__main__":
    root = tk.Tk()
    app = DayOfDragonsTimer(root)
    root.mainloop()
