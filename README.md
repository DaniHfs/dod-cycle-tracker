# Day of Dragons - Crystal & Cycle Tracker Overlay

A super lightweight, performance-friendly screen overlay for *Day of Dragons* to help make eldering much easier. It accurately tracks the game's internal 4-hour day/night loop, warns you when server-side crystal spawn ticks are wrapping up, and features a manual decay timer you can trigger from full-screen.

It runs entirely in the background.

## Features

* **Zero Performance Impact:** Built using native code frames so it won't tank your in-game FPS.
* **Phase Alerts:** Tracks the 2h 20m Day phase (Elder % crystals) and the 1h 40m Night phase (Elemental crystals).
* **Spawn Window Warning:** Automatically flashes an alert on your HUD when an active 30-minute server crystal spawn window is closing.
* **Sound Alerts:** Plays a low-overhead warning beep when the spawn window is closing and a double-beep when the active crystal timer expires.
* **Custom Keybinds:** Change the hotkeys directly from the overlay interface to whatever matches your keyboard setup.
* **Auto-Save Layout:** Remembers your exact screen location and key settings between sessions so you never have to re-drag or re-bind it.

---

## Why are manual inputs required?

*Day of Dragons* utilizes strict server-side authority and anti-cheat protection. The game hides active crystal coordinates and exact server loop timers from your computer's local memory to block cheating scripts.

This overlay is 100% clean and safe to use. It **does not** read the game's private memory or intercept network data. It relies entirely on your manual sync taps to line up its math engine with your server, keeping your game account completely safe from automated anti-cheat bans.

---

## How to Use It (For Players)

1. Download the latest **`DoDCycleTracker.exe`** from the [Releases Section](./releases).
2. Double-click the file to launch it. Click and drag anywhere on the dark overlay background to move it onto a clean spot on your screen or a second monitor.
3. Set your *Day of Dragons* video settings to **Borderless Windowed** mode. (Exclusive Fullscreen blocks desktop overlays from sitting on top of the game screen).
4. **Syncing the Clock:** The moment you log into your server and see the cycle shift (e.g., Night turns to Dawn, or Day turns to Dusk), tap your assigned sync hotkey to line up the timer perfectly with the server's time loop.
5. **Tracking Spawns:** When a teammate calls out an active crystal spawn in chat, hit your **Active Timer** hotkey to instantly kick off a 20-minute visual despawn ring.

### ⌨️ Default Keybinds

* **F6:** Sync Day Start
* **F7:** Sync Night Start
* **F8:** Start 20-Min Crystal Active Timer

---

## Setting Custom Keybinds

* Click the **"Change"** button next to any action on the overlay.
* The button will turn dark red and read **"Press..."**
* Hit any key on your keyboard. The overlay will register it instantly, bind it globally, and save it to a local `config.json` file.

---

## Sound Settings

The generated `config.json` also includes sound settings. You can open it directly to mute sounds with `"sound_enabled": false` or adjust `spawn_pitch` and `despawn_pitch` values in Hz.

---

## For Developers & Building from Source Code

If you prefer to run it manually via Python or want to inspect the source code, make sure you have Python 3.10+ installed and grab the keyboard listener dependency:

```bash
pip install keyboard
```

To compile this script back down into a standalone, one-click portable executable, install PyInstaller:

```bash
pip install pyinstaller
```

Then compile it using this specific optimization command:

```bash
pyinstaller --onefile --noconsole --uac-admin tracker.py
```

*Note: The `--uac-admin` flag is necessary so Windows permits the script to listen for your hotkeys while you are actively clicking around inside the heavy game client.*

---

## License

This tool is open-source and released under the **MIT License**. Feel free to fork the repository, make UI tweaks, or add features for your own server community!
