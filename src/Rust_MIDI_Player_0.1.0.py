import bisect
import ctypes
import gc
import json
import math
import os
import sys
import threading
import time
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilenames

import keyboard
import mido
from mido import MidiFile, get_output_names, open_output
from tkinterdnd2 import TkinterDnD, DND_FILES


APP_NAME = "Rust MIDI Player"
APP_AUTHOR = "By Hamish336"
APP_VERSION = "0.1.0"
DONATE_URL = "http://bit.ly/4vN4Zae"

README_TEXT = r"""# Rust MIDI Player

A lightweight, stable MIDI player designed specifically for Rust.

Built for reliable timing, low overhead, and clean playback so you can load a song and play without fighting reconnect issues or inconsistent behaviour.

Current focus: smooth solo playback.
Future focus: band sync, drift correction, advanced routing, and stronger playlist tools.

---

**Quick Topics**

- What this app does
- Key features
- Default shortcuts
- MIDI port rule
- Future band sync note
- Build icon files

---

**Key Features**

- Stable real-time MIDI playback engine
- Persistent MIDI connection during normal use
- Soft-close / reconnect behaviour to reduce Rust restart issues
- Speed control with 1.00 as normal real-time playback
- Playback volume and transpose controls
- Drag and drop MIDI files
- Playlist and Favorites system
- Auto Play Next Song
- Channel mute controls with scanned note counts
- Per-song mute memory for Favorites
- Temporary session mute memory for playlist-only songs
- Optional global shortcuts with rebind support
- Adjustable UI scale, song-name font size, and app refresh rate

---

**Default Shortcuts**

- F9  = Play / Pause
- F10 = Next Song
- F11 = Previous Song

---

**Important MIDI Port Rule**

Select the correct MIDI port before pressing Play.

Changing MIDI ports after playback has started usually requires restarting the app. If Rust still does not receive MIDI after restarting the app, restart Rust as well.

---

**Band Sync Foundation**

The MIDI engine is anchored to real time. If Rust hitches, alt-tabs, or visually stutters, the app is designed to keep the song position tracking real time instead of drifting behind.

This is important for future band-sync features, because players need timing that can recover from local frame drops and stay aligned to a shared clock.

---

**Icon Files For Builds**

- appicon.ico = runtime window icon while the app is open
- exeicon.ico = build-time EXE icon used by PyInstaller
"""

USER_GUIDE_TEXT = r"""# User Guide

**Quick Topics**

- Best setup order
- MIDI port rule
- Playback controls
- Channel mute / song fixing
- Favorites and saved mutes
- Settings
- Best playback habits
- Shortcuts
- Installation

---

**1. Best Setup Order**

1. Start LoopMIDI and make sure your virtual MIDI port exists.
2. Open Rust MIDI Player.
3. Select the correct MIDI port before pressing Play, or set it as the default in Settings.
4. Open Rust and select the same MIDI input in Rust.
5. Drag and drop MIDI files into the Playlist, or use + ADD MIDI.
6. Add your most-used songs to Favorites if you want them remembered between sessions.
7. Load, scan, and set up songs before playing when possible.
8. Press Play/Pause or use your configured shortcut.

---

**2. Important MIDI Port Rule**

Select the correct MIDI port before playback.

Changing the selected MIDI port after playback has started usually requires restarting the app before playing through a different port. If Rust still does not detect MIDI after the app restarts, restart Rust as well.

---

**3. Playback Controls**

- Play/Pause starts, pauses, or resumes the selected song.
- Next and Previous move through the active Playlist or Favorites tab.
- Reset stops playback and returns the song to the beginning.
- Speed 1.00 is normal real-time playback.
- Play Volume changes MIDI note velocity before sending notes to Rust.
- Transpose shifts notes up or down in semitones.
- Auto Play Next Song continues to the next track when a song finishes.
- The main buttons show your current shortcut bindings, such as Play/Pause (F9).

---

**4. Channel Mute / Song Fixing**

Some MIDI files contain extra channels that double notes, trigger unwanted sounds, or make a song sound wrong in Rust.

- Use the channel buttons at the bottom of the app to mute problem channels.
- The number under each channel shows how many notes were found on that channel.
- Favorites remember their channel mute settings permanently.
- Playlist-only songs remember mutes temporarily until the app restarts or the playlist is cleared.
- Some MIDI files simply do not suit certain Rust instruments. Channel mute, speed, volume, and transpose are included to help make more songs playable.

---

**5. Favorites and Saved Settings**

- Favorites are linked to the original MIDI file path.
- Moving, renaming, or deleting a favorited MIDI file can break that Favorite and its saved mute settings.
- Keep MIDI files used in Favorites in the same folder/path after adding them.
- Playlist-only mute memory is session-based and clears when the app restarts or the playlist is cleared.

The app remembers Favorites, loaded track, playback settings, active tab, window size/position, default port, UI scale, song font size, app refresh rate, shortcut settings, and Favorites mute selections.

---

**6. Settings**

- Default Port saves your preferred MIDI output.
- UI Scale changes the overall app size and is best applied after restarting the app.
- Song Name Font Size changes song names inside Playlist and Favorites.
- App Refresh Rate controls how often the app UI updates:
  - 50 ms Quality = smoothest counter/progress display, useful for testing.
  - 125 ms Normal = default refresh rate.
  - 250 ms Balanced = less UI refresh work.
  - 500 ms Performance = lowest UI refresh work, but progress updates less often.
- Global Shortcuts can be disabled if alt-tabbing or focus changes cause stutters.

---

**7. Best Playback Habits**

- Start the MIDI app before launching Rust when possible.
- Select your port before playback.
- Load and scan songs before pressing Play.
- Avoid opening Settings while a song is playing.
- Avoid dragging, resizing, minimizing, or alt-tabbing during playback if your system is prone to stutters.
- Avoid adding songs or Favorites during playback, because MIDI scanning can cause small performance spikes.
- See the Rust Optimization tab for gc.buffer, -popupwindow, and Rust settings guidance.

**Alt-Tab Note**

Alt-tabbing can affect what you hear in Rust because Rust may hitch during focus changes. The MIDI engine is still designed to keep playback position tracking real time, which is important for future Band sync.

---

**8. Default Shortcuts**

- F9  = Play / Pause
- F10 = Next Song
- F11 = Previous Song

---

**9. Installation**

1. Download and install LoopMIDI.
2. Open LoopMIDI and create a virtual MIDI port.
3. Restart your PC if the port is not detected reliably.
4. Open Rust MIDI Player and select the LoopMIDI port.
5. Select the same MIDI input inside Rust.
"""

RUST_OPTIMIZATION_TEXT = r"""# Rust Optimization, Reduce Stutters for Smooth Music Performances.

**Quick Topics**

- Start with gc.buffer (Try it!)
- Try -popupwindow borderless mode (Try it!)
- Lower Rust settings if needed
- Avoid heavy actions during playback
- Global shortcuts and alt-tabbing
- Optional Task Manager priority tuning
- Optional app refresh rate tuning

---

**1. Start With Rust Garbage Collection**

Rust can briefly freeze when its own garbage collection runs. This is controlled by Rust, not by the MIDI app.

Start by setting a larger GC buffer. This is often enough to reduce mid-song stutters.

Open the Rust console with F1 and enter one of these commands:

- gc.collect      = run this before a song to clear used game memory
- gc.buffer 1024  = 1 GB buffer, safer starting point for 8-16 GB RAM
- gc.buffer 2048  = 2 GB buffer, good general test value for 16 GB RAM
- gc.buffer 4096  = 4 GB buffer, good starting point for many 32 GB systems
- gc.buffer 8192  = 8 GB buffer, good starting point for many 64 GB systems
- gc.buffer 12288 = 12 GB buffer, optional for 64 GB+ systems with plenty of free RAM

Do not spam gc.collect during songs. Use it before playback or during safe downtime.

---

**2. Try Borderless Mode With -popupwindow**

If fullscreen focus changes or alt-tabbing cause stutters, try forcing Rust into borderless window mode.

In Steam:

1. Right-click Rust.
2. Click Properties.
3. Find Launch Options.
4. Add this:

-popupwindow

What it does:

- Forces Rust into a borderless window style.
- Can make alt-tabbing smoother.
- May reduce focus-change stutters on some systems.
- Can improve smoothness if normal fullscreen behaves badly.

Alt-tabbing can still affect playback because Rust may hitch during focus changes. The MIDI engine is designed to keep tracking real time instead of drifting behind, which is important for future Band sync.

---

**3. Reduce Rust Settings If Needed**

If Rust is already struggling, MIDI playback may feel worse during frame drops or GC hitches.

Try lowering settings that increase memory, object, or scene load:

- Graphics Quality
- Object Quality
- Tree Quality
- Terrain Quality
- Shadow Distance
- Draw Distance
- Max Gibs

Also close unnecessary background programs before playing music.

---

**4. Best Playback Habits**

For smoothest playback:

- Load and scan songs before playing.
- Avoid adding songs during playback.
- Avoid opening Settings during playback.
- Avoid dragging, resizing, minimizing, or alt-tabbing if your system stutters.
- Let songs finish or stop playback before changing lots of settings.

---

**5. Global Shortcuts and Alt-Tabbing**

Global shortcuts use a system-wide keyboard hook so Play/Pause, Next, and Previous can work while Rust is focused.

On some systems, keyboard hooks and focus changes can add stutters.

If alt-tab stutters are excessive:

1. Try -popupwindow first.
2. Disable Global Shortcuts in Settings.
3. Use the app buttons instead.

---

**6. Optional Task Manager Priority**

If Rust stutters during songs:

1. Open Task Manager.
2. Go to Details.
3. Right-click RustClient.exe.
4. Set priority to High.
5. Optional: set Rust MIDI Player.exe to Below normal.

This can help Windows favour Rust while the MIDI app keeps timing anchored to real time.

---

**7. Optional App Refresh Rate**

In Settings, try:

- 250 ms Balanced
- 500 ms Performance

This reduces UI refresh work. Playback timing stays anchored to real time.

You can also test 50 ms Quality if you want the smoothest counter/progress display while testing.
"""

TROUBLESHOOTING_TEXT = r"""# Troubleshooting

**Quick Topics**

- Critical MIDI port rule
- Rust not receiving MIDI
- MIDI port not showing
- MIDI stops working after app restart
- Song sounds wrong or doubled
- Stutters during playback
- Alt-tab stutters
- Favorites / saved mutes
- Playlist mute memory

---

**1. Critical MIDI Port Rule**

Select the correct MIDI port before pressing Play.

Changing MIDI ports after playback has started usually requires restarting the app. If Rust still does not receive MIDI after restarting the app, restart Rust as well.

---

**2. Rust Not Receiving MIDI Input**

- Confirm LoopMIDI is running and the port is active.
- Confirm the same MIDI port is selected in Rust and in the app.
- Restart the app if you changed ports after playback started.
- Restart Rust if the app was restarted and Rust no longer detects MIDI input.

---

**3. MIDI Port Not Showing / Not Detected**

- Make sure LoopMIDI is running before opening the app.
- Restart the app.
- Restart your PC if the port still does not appear.
- You can also restart the Windows MIDI Service:
  1. Press Win + R
  2. Type services.msc
  3. Find Windows MIDI Service
  4. Restart the service

---

**4. MIDI Stops Working After Restarting the App**

The app uses a soft-close / reconnect process to reduce this problem.

Rust may still occasionally lose MIDI input after the app has been restarted, especially if playback has already occurred. If this happens, restart Rust to restore MIDI detection.

---

**5. Song Sounds Incorrect / Doubled Notes**

Some MIDI files contain channels that double notes or trigger unwanted sounds.

- Use the Channel Mute buttons to find and mute the problem channels.
- The number under each channel shows how many notes were found on that channel.
- Many songs sound better with one or two channels muted.
- Some MIDI files simply do not suit certain Rust instruments.

Speed, volume, transpose, and channel mute are included to help make more songs playable.

---

**6. Stutters During Playback**

See the Rust Optimization tab first.

Recommended order:

1. Set gc.buffer in Rust.
2. Try -popupwindow in Steam Launch Options.
3. Reduce heavy Rust settings.
4. Avoid alt-tabbing, resizing, or adding songs during playback.
5. Try 250 ms Balanced or 500 ms Performance app refresh rate.

The app keeps MIDI playback anchored to real time. If Rust visually stutters, playback timing is designed to continue tracking real time rather than drifting behind.

---

**7. Alt-Tab Stutters**

Alt-tabbing can affect what you hear because Rust may hitch during focus changes.

- Try -popupwindow in Rust Launch Options.
- Disable Global Shortcuts in Settings if needed.
- Avoid alt-tabbing during playback on systems that are prone to focus-change hitches.

This does not mean the MIDI timing engine has lost sync. The engine is designed to keep tracking real time, which is important for future Band sync.

---

**8. Avoid Adding Songs During Playback**

Adding songs or adding Favorites scans MIDI files to calculate channel note counts.

This can cause small performance spikes. Best practice is to load and set up your songs first, then start playback.

---

**9. Favorites / Saved Mutes Missing**

Favorites and saved Favorites mute settings are linked to the original MIDI file path.

If you move, rename, or delete a MIDI file after adding it to Favorites, the app may no longer find it.

Keep favorited MIDI files in the same folder/path after adding them to the app.

---

**10. Playlist Song Mutes Not Remembered After Restart**

Playlist-only song mutes are session-based.

They are intentionally cleared when the app restarts or when the playlist is cleared.
"""

LICENSE_TEXT = r"""Rust MIDI Player License
Copyright (c) 2026 Hamish Eagling (Hamish336)

All Rights Reserved

------------------------------------------------------------------

1. Personal Use License

This software is provided free of charge for personal, non-commercial use only.

You are permitted to:
- Download and use this software for its intended purpose
- Share the official download link provided by the author

------------------------------------------------------------------

2. Donations

This software may include optional donation links.

Donations are voluntary and:
- Do NOT grant ownership rights
- Do NOT grant redistribution rights
- Do NOT grant access to source code

All rights remain with the author regardless of donation.

------------------------------------------------------------------

3. Restrictions

You may NOT, without explicit written permission from the author:

- Redistribute, re-upload, mirror, or share this software (in whole or in part)
  on any website, platform, or service

- Modify, adapt, decompile, reverse engineer, or create derivative works

- Sell, license, bundle, or use this software for any commercial purpose

- Remove, alter, or obscure any branding, credits, or ownership notices

------------------------------------------------------------------

4. Official Distribution

This software may only be distributed through official channels provided by the author.

Any unofficial or modified distribution is strictly prohibited.

------------------------------------------------------------------

5. Ownership

This software, including all code, design, and functionality, remains the sole
intellectual property of:

Hamish Eagling (Hamish336)

------------------------------------------------------------------

6. No Warranty

This software is provided "as is", without warranty of any kind, express or implied.

The author is not liable for any damages, loss, or issues arising from use of
this software.

------------------------------------------------------------------

7. Termination

This license is automatically terminated if you violate any of these terms.

Upon termination, you must delete all copies of the software in your possession.

------------------------------------------------------------------

8. Contact

For permissions, inquiries, or licensing requests, contact the author directly.
"""


def enable_high_precision_timer():
    try:
        ctypes.windll.winmm.timeBeginPeriod(1)
    except Exception:
        pass


def disable_high_precision_timer():
    try:
        ctypes.windll.winmm.timeEndPeriod(1)
    except Exception:
        pass      

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
        except Exception:
            base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def apply_window_icon(window):
    icon_path = resource_path("assets/appicon.ico")
    if not os.path.exists(icon_path):
        return
    try:
        window.iconbitmap(default=icon_path)
    except Exception as e:
        print("Icon load error:", e)


def set_dark_title_bar(window):
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)

        # Windows 11 / newer Windows 10 builds
        if ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(value),
            ctypes.sizeof(value),
        ) != 0:
            # Older Windows 10 builds
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                19,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )
    except Exception as e:
        print("Dark title bar not supported:", e)


class Transport:
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"


class DarkScrollbar(tk.Canvas):
    def __init__(
        self,
        parent,
        command,
        bg="#151515",
        trough="#101010",
        thumb="#5f1e15",
        active="#8d2f20",
        width=12,
    ):
        super().__init__(
            parent,
            width=width,
            highlightthickness=0,
            bd=0,
            relief="flat",
            bg=bg,
        )
        self.command = command
        self.trough = trough
        self.thumb = thumb
        self.active = active
        self.first = 0.0
        self.last = 1.0
        self.dragging = False
        self.hover = False

        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", lambda e: self.set_hover(True))
        self.bind("<Leave>", lambda e: self.set_hover(False))

    def set_hover(self, value):
        self.hover = value
        self.redraw()

    def set(self, first, last):
        self.first = max(0.0, min(1.0, float(first)))
        self.last = max(0.0, min(1.0, float(last)))
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = max(1, self.winfo_width())
        h = max(1, self.winfo_height())

        self.create_rectangle(0, 0, w, h, fill=self.trough, outline=self.trough)

        span = max(0.02, self.last - self.first)
        thumb_h = max(24, int(span * h))
        y1 = int(self.first * h)
        y2 = min(h, y1 + thumb_h)

        color = self.active if (self.hover or self.dragging) else self.thumb
        self.create_rectangle(1, y1, w - 1, y2, fill=color, outline=color)

    def on_click(self, event):
        self.dragging = True
        self.on_drag(event)

    def on_drag(self, event):
        h = max(1, self.winfo_height())
        span = max(0.02, self.last - self.first)
        new_first = (event.y / h) - (span / 2.0)
        new_first = max(0.0, min(1.0 - span, new_first))
        self.command("moveto", new_first)

    def on_release(self, event):
        self.dragging = False
        self.redraw()


class MidiPlayer:
    def __init__(self):
        self.outport = None
        self.connected_port_name = ""
        self.state = Transport.STOPPED

        self.tempo = 1.0
        self.transpose = 0
        self.volume = 1.0
        self.auto_play_next = False
        self.speed_calibration = 1.0

        self.total_time = 1.0
        self.events = []
        self.event_times = []
        self.seek_index = 0
        self.used_channels = set()
        self.muted_channels = set()

        self.thread = None
        self.lock = threading.Lock()

        self.anchor_time = time.perf_counter()
        self.anchor_playhead = 0.0

        self.on_track_finished = None

        self.stop_event = threading.Event()
        self.wake_event = threading.Event()

        self.lookahead = 0.018
        self.min_sleep = 0.002
        self.max_sleep = 0.02
        self.idle_sleep = 0.10

    def _wake_worker(self):
        self.wake_event.set()

    def _ensure_worker(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.wake_event.clear()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def _send_cc(self, channel, control, value=0):
        if not self.outport:
            return
        try:
            self.outport.send(
                mido.Message("control_change", channel=channel, control=control, value=value)
            )
        except Exception:
            pass

    def panic_channel(self, channel):
        self._send_cc(channel, 123, 0)
        self._send_cc(channel, 120, 0)
        self._send_cc(channel, 64, 0)

    def connect(self, port_name):
        if self.outport:
            return True

        for attempt in range(4):
            try:
                ports = get_output_names()
                exact = [p for p in ports if p == port_name]
                if exact:
                    chosen = exact[0]
                else:
                    partial = [p for p in ports if port_name and port_name in p]
                    chosen = partial[0] if len(partial) == 1 else None

                if not chosen:
                    time.sleep(0.10)
                    continue

                self.outport = open_output(chosen)
                self.connected_port_name = chosen
                return True

            except Exception as e:
                print(f"MIDI connect error (attempt {attempt + 1}):", e)
                time.sleep(0.12)

        return False

    def reconnect(self, port_name):
        try:
            if self.outport:
                try:
                    self.panic()
                    time.sleep(0.08)
                except Exception:
                    pass

                try:
                    self.outport.close()
                except Exception:
                    pass

                self.outport = None
                self.connected_port_name = ""

            time.sleep(0.15)
            return self.connect(port_name)

        except Exception as e:
            print("MIDI reconnect error:", e)
            return False

    def panic(self):
        if not self.outport:
            return
        for ch in range(16):
            self.panic_channel(ch)

    def close(self):
        self.stop()
        time.sleep(0.12)

        self.stop_event.set()
        self._wake_worker()

        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=0.5)
            except Exception:
                pass

        if self.outport:
            try:
                self.outport.close()
            except Exception:
                pass

        time.sleep(0.10)

        try:
            gc.enable()
        except Exception:
            pass

        self.outport = None
        self.connected_port_name = ""

    def current_playhead(self):
        effective_tempo = self.tempo * self.speed_calibration
        if self.state == Transport.PLAYING:
            return max(
                0.0,
                min(
                    self.anchor_playhead + (time.perf_counter() - self.anchor_time) * effective_tempo,
                    self.total_time,
                ),
            )
        return max(0.0, min(self.anchor_playhead, self.total_time))

    def build_events(self, filepath):
        mid = MidiFile(filepath)
        self.events = []
        self.event_times = []
        self.used_channels = set()
        t = 0.0

        for msg in mid:
            t += float(msg.time)
            if msg.is_meta:
                continue

            if hasattr(msg, "channel"):
                self.used_channels.add(msg.channel)

            self.events.append((t, msg))
            self.event_times.append(t)

        self.total_time = max(t, 1.0)

    def rebuild_seek_index(self, playhead):
        self.seek_index = bisect.bisect_left(self.event_times, playhead)

    def start_playback(self, filepath):
        if not filepath:
            return False

        try:
            self.build_events(filepath)
        except Exception as e:
            print("Failed to load MIDI:", e)
            return False

        with self.lock:
            self.anchor_playhead = 0.0
            self.anchor_time = time.perf_counter()
            self.rebuild_seek_index(0.0)
            self.state = Transport.PLAYING

        self.panic()
        try:
            gc.disable()
        except Exception:
            pass

        self._ensure_worker()
        self._wake_worker()
        return True

    def pause(self):
        with self.lock:
            if self.state == Transport.PLAYING:
                self.anchor_playhead = self.current_playhead()
                self.anchor_time = time.perf_counter()
                self.state = Transport.PAUSED
        self._wake_worker()

    def resume(self):
        with self.lock:
            if self.state == Transport.PAUSED:
                self.anchor_time = time.perf_counter()
                self.state = Transport.PLAYING
        self._ensure_worker()
        self._wake_worker()

    def stop(self):
        with self.lock:
            self.state = Transport.STOPPED
            self.anchor_playhead = 0.0
            self.anchor_time = time.perf_counter()
            self.rebuild_seek_index(0.0)

        self.panic()
        try:
            gc.enable()
        except Exception:
            pass
        self._wake_worker()

    def seek(self, t):
        with self.lock:
            target = max(0.0, min(float(t), self.total_time))
            self.anchor_playhead = target
            self.anchor_time = time.perf_counter()
            self.rebuild_seek_index(target)

        self.panic()
        self._wake_worker()

    def set_speed(self, value):
        with self.lock:
            current = self.current_playhead()
            self.tempo = max(0.05, float(value))
            self.anchor_playhead = current
            self.anchor_time = time.perf_counter()
        self._wake_worker()

    def set_transpose(self, value):
        with self.lock:
            self.transpose = int(float(value))
        self._wake_worker()

    def set_volume(self, value):
        with self.lock:
            self.volume = max(0.0, min(2.0, float(value)))
        self._wake_worker()

    def set_muted_channels(self, channels):
        with self.lock:
            self.muted_channels = set(int(ch) for ch in channels if 0 <= int(ch) <= 15)
        self.panic()
        self._wake_worker()

    def toggle_mute(self, ch):
        need_panic = False
        with self.lock:
            if ch in self.muted_channels:
                self.muted_channels.remove(ch)
            else:
                self.muted_channels.add(ch)
                need_panic = True
        if need_panic:
            self.panic_channel(ch)
        self._wake_worker()

    def loop(self):
        while not self.stop_event.is_set():
            to_send = []
            do_finish_callback = False
            wait_time = self.idle_sleep

            with self.lock:
                state = self.state

                if state == Transport.PLAYING:
                    playhead = self.current_playhead()

                    if playhead >= self.total_time:
                        self.anchor_playhead = self.total_time
                        self.state = Transport.STOPPED
                        do_finish_callback = True
                        wait_time = self.idle_sleep
                    else:
                        due_time = playhead + self.lookahead
                        tempo = max(0.05, self.tempo * self.speed_calibration)
                        transpose = self.transpose
                        volume = self.volume
                        muted_channels = set(self.muted_channels)

                        while self.seek_index < len(self.events) and self.events[self.seek_index][0] <= due_time:
                            _, raw_msg = self.events[self.seek_index]
                            msg = raw_msg

                            channel = getattr(msg, "channel", None)
                            is_note_on = msg.type == "note_on" and getattr(msg, "velocity", 0) > 0

                            if channel is not None and is_note_on and channel in muted_channels:
                                self.seek_index += 1
                                continue

                            if msg.type in ("note_on", "note_off"):
                                transposed_note = max(0, min(127, msg.note + transpose))
                                if transposed_note != msg.note:
                                    msg = msg.copy(note=transposed_note)

                            if is_note_on and volume != 1.0:
                                new_vel = max(1, min(127, int(msg.velocity * volume)))
                                if new_vel != msg.velocity:
                                    msg = msg.copy(velocity=new_vel)

                            to_send.append(msg)
                            self.seek_index += 1

                        if self.seek_index < len(self.events):
                            next_event_time = self.events[self.seek_index][0]
                            remaining = max(0.0, next_event_time - playhead - self.lookahead)
                            wait_time = min(self.max_sleep, max(self.min_sleep, remaining / max(tempo, 0.05)))
                        else:
                            remaining = max(0.0, self.total_time - playhead)
                            wait_time = min(self.max_sleep, max(self.min_sleep, remaining / max(tempo, 0.05)))

                else:
                    wait_time = self.idle_sleep

            if to_send and self.outport:
                for msg in to_send:
                    try:
                        self.outport.send(msg)
                    except Exception as e:
                        print("MIDI send error:", e)

            if do_finish_callback:
                try:
                    gc.enable()
                except Exception:
                    pass

                if self.on_track_finished:
                    try:
                        self.on_track_finished()
                    except Exception as e:
                        print("Track finished callback error:", e)

            self.wake_event.wait(timeout=wait_time)
            self.wake_event.clear()


class PlaylistState:
    def __init__(self):
        self.items = []
        self.selected_index = None

    def clear(self):
        self.items.clear()
        self.selected_index = None

    def set_items(self, items):
        self.items = list(items)
        if not self.items:
            self.selected_index = None
        elif self.selected_index is None or self.selected_index >= len(self.items):
            self.selected_index = 0

    def add(self, filepath):
        if filepath not in self.items:
            self.items.append(filepath)
        if self.selected_index is None and self.items:
            self.selected_index = 0

    def remove(self, filepath):
        if filepath not in self.items:
            return

        idx = self.items.index(filepath)
        self.items.remove(filepath)

        if not self.items:
            self.selected_index = None
        elif self.selected_index is not None:
            if self.selected_index > idx:
                self.selected_index -= 1
            elif self.selected_index >= len(self.items):
                self.selected_index = len(self.items) - 1

    def select(self, index):
        if 0 <= index < len(self.items):
            self.selected_index = index

    def selected_path(self):
        if self.selected_index is None:
            return None
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None

    def index_of(self, filepath):
        try:
            return self.items.index(filepath)
        except ValueError:
            return None

    def next_index(self):
        if not self.items:
            return None
        if self.selected_index is None:
            return 0
        return (self.selected_index + 1) % len(self.items)

    def previous_index(self):
        if not self.items:
            return None
        if self.selected_index is None:
            return 0
        return (self.selected_index - 1) % len(self.items)


class App:
    def __init__(self, root):
        self.root = root
        self.player = MidiPlayer()
        self.player.on_track_finished = self.on_track_finished
        self.user_dragging = False

        self.playlist = PlaylistState()
        self.favorites = PlaylistState()
        self.active_source = "playlist"

        self.current_track_path = None
        self.current_track_source = None
        self.track_channel_stats = {}
        self.session_track_mute_settings = {}

        self.settings_path = "rust_midi_player_settings.json"
        self.settings_data = self.load_settings()
        self.ui_scale = float(self.settings_data.get("ui_scale", 1.0))
        self.song_font_size = int(self.settings_data.get("song_font_size", 12))
        self.ui_refresh_ms = int(self.settings_data.get("ui_refresh_ms", 125))

        self.bg = "#090909"
        self.panel = "#151515"
        self.panel2 = "#1b1b1b"
        self.border = "#2b2b2b"
        self.border2 = "#3a241d"
        self.red = "#b6402c"
        self.red2 = "#8d2f20"
        self.red3 = "#5f1e15"
        self.text = "#d6d0cb"
        self.subtle = "#8f8780"
        self.muted = "#353535"
        self.list_bg = "#0f0f0f"

        self._last_now_text = None
        self._last_channel_state = None
        self.hotkey_handles = []

        self._setup_styles()

        self.root.title(APP_NAME)

        # Runtime app window icon. The final EXE icon is set at build time with exeicon.ico.
        apply_window_icon(self.root)

        self._apply_window_geometry()
        self.root.configure(bg=self.bg)
        set_dark_title_bar(self.root)

        self._build_scrollable_shell()
        self._build_ui()
        self._restore_saved_favorites_only()
        self.refresh_ports()
        self._restore_runtime_settings()
        self.refresh_playlist_views()
        self.apply_shortcut_settings()
        self.update()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def path_is_favorite(self, filepath):
        return filepath in self.favorites.items

    def register_hotkeys(self):
        if not self.settings_data.get("shortcuts_enabled", True):
            return

        shortcuts = self.settings_data.get("shortcuts", {})
        play_pause = shortcuts.get("play_pause", "F9").strip()
        next_track = shortcuts.get("next_track", "F10").strip()
        previous_track = shortcuts.get("previous_track", "F11").strip()

        try:
            if play_pause:
                handle = keyboard.add_hotkey(play_pause, self.toggle)
                self.hotkey_handles.append(handle)
            if next_track:
                handle = keyboard.add_hotkey(next_track, self.play_next)
                self.hotkey_handles.append(handle)
            if previous_track:
                handle = keyboard.add_hotkey(previous_track, self.play_previous)
                self.hotkey_handles.append(handle)
        except Exception as e:
            print("Hotkey register error:", e)

    def unregister_hotkeys(self):
        for handle in self.hotkey_handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception as e:
                print("Hotkey cleanup error:", e)
        self.hotkey_handles.clear()

    def apply_shortcut_settings(self):
        self.unregister_hotkeys()
        self.register_hotkeys()

    def update_transport_button_labels(self):
        if not hasattr(self, "transport_buttons"):
            return
        shortcuts = self.settings_data.get("shortcuts", {})
        pp = shortcuts.get("play_pause", "F9")
        nx = shortcuts.get("next_track", "F10")
        pr = shortcuts.get("previous_track", "F11")
        labels = {
            "play_pause": f"▶ PLAY/PAUSE ({pp})",
            "next_track": f"⏭ NEXT ({nx})",
            "previous_track": f"⏮ PREVIOUS ({pr})",
        }
        for key, label in labels.items():
            btn = self.transport_buttons.get(key)
            if btn:
                btn.configure(text=label)

    def scan_midi_channels(self, filepath):
        stats = {
            "used_channels": set(),
            "note_counts": {i: 0 for i in range(16)},
        }

        try:
            mid = MidiFile(filepath)
            for msg in mid:
                if msg.is_meta:
                    continue

                channel = getattr(msg, "channel", None)
                if channel is None:
                    continue

                stats["used_channels"].add(channel)

                if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                    stats["note_counts"][channel] += 1

        except Exception as e:
            print(f"Channel scan failed for {filepath}:", e)

        return stats

    def ensure_track_scanned(self, filepath):
        if not filepath:
            return
        if filepath in self.track_channel_stats:
            return
        self.track_channel_stats[filepath] = self.scan_midi_channels(filepath)

    def get_display_track_path(self):
        selected = self.current_state().selected_path()
        if selected:
            return selected
        if self.current_track_path:
            return self.current_track_path
        return None

    def get_display_track_stats(self):
        path = self.get_display_track_path()
        if not path:
            return {
                "used_channels": set(),
                "note_counts": {i: 0 for i in range(16)},
            }

        self.ensure_track_scanned(path)
        return self.track_channel_stats.get(
            path,
            {
                "used_channels": set(),
                "note_counts": {i: 0 for i in range(16)},
            },
        )

    def get_saved_mute_state_for_path(self, filepath):
        if not filepath:
            return set()

        persistent = self.settings_data.get("track_mute_settings", {})
        if filepath in persistent:
            return {int(ch) for ch in persistent[filepath] if 0 <= int(ch) <= 15}

        if filepath in self.session_track_mute_settings:
            return {int(ch) for ch in self.session_track_mute_settings[filepath] if 0 <= int(ch) <= 15}

        return set()

    def save_current_track_mute_state(self):
        if not self.current_track_path:
            return

        muted_sorted = sorted(self.player.muted_channels)

        if self.path_is_favorite(self.current_track_path):
            mute_map = self.settings_data.setdefault("track_mute_settings", {})
            mute_map[self.current_track_path] = muted_sorted
            self.session_track_mute_settings.pop(self.current_track_path, None)
        else:
            self.session_track_mute_settings[self.current_track_path] = muted_sorted

    def apply_track_mute_state(self, filepath):
        persistent = self.settings_data.setdefault("track_mute_settings", {})
        if filepath in persistent:
            self.player.set_muted_channels(persistent[filepath])
        elif filepath in self.session_track_mute_settings:
            self.player.set_muted_channels(self.session_track_mute_settings[filepath])
        else:
            self.player.set_muted_channels(set())

        self._last_channel_state = None

    def toggle_channel_mute(self, ch):
        display_path = self.get_display_track_path()
        if not display_path:
            return

        preview = self.get_saved_mute_state_for_path(display_path)

        if display_path == self.current_track_path:
            preview = set(self.player.muted_channels)

        if ch in preview:
            preview.remove(ch)
        else:
            preview.add(ch)

        if self.path_is_favorite(display_path):
            self.settings_data.setdefault("track_mute_settings", {})[display_path] = sorted(preview)
            self.session_track_mute_settings.pop(display_path, None)
        else:
            self.session_track_mute_settings[display_path] = sorted(preview)

        if display_path == self.current_track_path:
            self.player.set_muted_channels(preview)

        self.save_settings()
        self._last_channel_state = None

    def _sanitize_speed(self, value):
        try:
            v = float(value)
        except Exception:
            return 1.0
        return v if v > 0 else 1.0

    def _sanitize_volume(self, value):
        try:
            v = float(value)
        except Exception:
            return 1.0
        return v if v > 0 else 1.0

    def load_settings(self):
        default = {
            "default_port": "",
            "favorites": [],
            "ui_scale": 1.1,
            "song_font_size": 12,
            "ui_refresh_ms": 125,
            "auto_play_next": False,
            "speed": 1.0,
            "volume": 1.0,
            "transpose": 0,
            "active_tab": "playlist",
            "window_geometry": "",
            "playlist_selected_index": None,
            "favorites_selected_index": None,
            "current_track_path": None,
            "current_track_source": None,
            "track_mute_settings": {},
            "shortcuts_enabled": True,
            "shortcuts": {
                "play_pause": "F9",
                "next_track": "F10",
                "previous_track": "F11",
            },
        }
        if not os.path.exists(self.settings_path):
            return default

        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return default

            merged = default.copy()
            merged.update(data)

            try:
                merged["ui_scale"] = float(merged.get("ui_scale", 1.0))
            except Exception:
                merged["ui_scale"] = 1.0
            if merged["ui_scale"] not in (0.8, 0.9, 1.0, 1.1, 1.2, 1.3):
                merged["ui_scale"] = 1.0

            try:
                merged["song_font_size"] = int(merged.get("song_font_size", 12))
            except Exception:
                merged["song_font_size"] = 12
            merged["song_font_size"] = max(8, min(16, merged["song_font_size"]))

            try:
                merged["ui_refresh_ms"] = int(merged.get("ui_refresh_ms", 125))
            except Exception:
                merged["ui_refresh_ms"] = 125
            if merged["ui_refresh_ms"] not in (50, 125, 250, 500):
                merged["ui_refresh_ms"] = 125

            merged["auto_play_next"] = bool(merged.get("auto_play_next", False))
            merged["speed"] = self._sanitize_speed(merged.get("speed", 1.0))
            merged["volume"] = self._sanitize_volume(merged.get("volume", 1.0))
            merged["transpose"] = int(merged.get("transpose", 0))
            merged["track_mute_settings"] = dict(merged.get("track_mute_settings", {}))
            merged["shortcuts_enabled"] = bool(merged.get("shortcuts_enabled", True))

            shortcuts = default["shortcuts"].copy()
            shortcuts.update(merged.get("shortcuts", {}))
            merged["shortcuts"] = shortcuts

            current_track = merged.get("current_track_path")
            if current_track and not os.path.exists(current_track):
                merged["current_track_path"] = None
                merged["current_track_source"] = None

            valid_mute_map = {}
            for path, muted in merged["track_mute_settings"].items():
                if os.path.exists(path):
                    try:
                        valid_mute_map[path] = [int(ch) for ch in muted if 0 <= int(ch) <= 15]
                    except Exception:
                        pass
            merged["track_mute_settings"] = valid_mute_map

            return merged
        except Exception as e:
            print("Failed to load settings:", e)
            return default

    def save_settings(self):
        try:
            geometry = self.root.geometry()
        except Exception:
            geometry = ""

        current_speed = self._sanitize_speed(self.speed.get() if hasattr(self, "speed") else 1.0)
        current_volume = self._sanitize_volume(self.volume.get() if hasattr(self, "volume") else 1.0)

        data = {
            "default_port": self.port.get().strip() if hasattr(self, "port") else self.settings_data.get("default_port", ""),
            "favorites": [p for p in self.favorites.items if os.path.exists(p)],
            "ui_scale": float(self.settings_data.get("ui_scale", self.ui_scale)),
            "song_font_size": int(self.settings_data.get("song_font_size", self.song_font_size)),
            "ui_refresh_ms": int(self.settings_data.get("ui_refresh_ms", self.ui_refresh_ms)),
            "auto_play_next": bool(self.auto_next_var.get()) if hasattr(self, "auto_next_var") else False,
            "speed": current_speed,
            "volume": current_volume,
            "transpose": int(float(self.transpose.get())) if hasattr(self, "transpose") else 0,
            "active_tab": self.active_source,
            "window_geometry": geometry,
            "playlist_selected_index": self.playlist.selected_index,
            "favorites_selected_index": self.favorites.selected_index,
            "current_track_path": self.current_track_path if self.current_track_path and os.path.exists(self.current_track_path) else None,
            "current_track_source": self.current_track_source if self.current_track_path and os.path.exists(self.current_track_path) else None,
            "track_mute_settings": self.settings_data.get("track_mute_settings", {}),
            "shortcuts_enabled": bool(self.settings_data.get("shortcuts_enabled", True)),
            "shortcuts": dict(self.settings_data.get("shortcuts", {})),
        }

        try:
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Failed to save settings:", e)

    def s(self, value):
        return max(1, int(round(value * self.ui_scale)))

    def _apply_window_geometry(self):
        saved = self.settings_data.get("window_geometry", "")
        if saved:
            try:
                self.root.geometry(saved)
                return
            except Exception:
                pass
        self.root.geometry(f"{self.s(960)}x{self.s(980)}")

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Rust.TCombobox",
            fieldbackground=self.panel2,
            background=self.panel2,
            foreground=self.text,
            bordercolor=self.border2,
            lightcolor=self.panel2,
            darkcolor=self.panel2,
            arrowcolor=self.text,
            relief="flat",
            padding=0,
        )
        style.map(
            "Rust.TCombobox",
            fieldbackground=[
                ("readonly", self.panel2),
                ("!disabled", self.panel2),
            ],
            foreground=[
                ("readonly", self.text),
                ("!disabled", self.text),
            ],
            background=[
                ("readonly", self.panel2),
                ("!disabled", self.panel2),
            ],
            selectbackground=[
                ("readonly", self.panel2),
                ("!disabled", self.panel2),
            ],
            selectforeground=[
                ("readonly", self.text),
                ("!disabled", self.text),
            ],
        )
        try:
            self.root.option_add("*TCombobox*Listbox.background", self.panel2)
            self.root.option_add("*TCombobox*Listbox.foreground", self.text)
            self.root.option_add("*TCombobox*Listbox.selectBackground", self.red3)
            self.root.option_add("*TCombobox*Listbox.selectForeground", "#f5e7e1")
        except Exception:
            pass
        style.configure(
            "Rust.TNotebook",
            background=self.panel,
            borderwidth=0,
            tabmargins=(0, 0, 0, 0),
        )
        style.layout("Rust.TNotebook", [("Notebook.client", {"sticky": "nswe"})])
        style.configure(
            "Rust.TNotebook.Tab",
            background=self.panel2,
            foreground=self.subtle,
            padding=(self.s(10), self.s(4)),
            borderwidth=0,
        )
        style.map(
            "Rust.TNotebook.Tab",
            background=[("selected", self.red3)],
            foreground=[("selected", "#f5e7e1")],
        )

    def _build_scrollable_shell(self):
        self.outer = tk.Frame(self.root, bg=self.bg)
        self.outer.pack(fill="both", expand=True)

        self.app_canvas = tk.Canvas(
            self.outer,
            bg=self.bg,
            highlightthickness=0,
            bd=0,
            relief="flat",
        )
        self.app_scroll = DarkScrollbar(
            self.outer,
            command=self.app_canvas.yview,
            bg=self.bg,
            trough=self.panel,
            thumb=self.red3,
            active=self.red2,
            width=self.s(12),
        )
        self.app_canvas.configure(yscrollcommand=self.app_scroll.set)

        self.app_scroll.pack(side="right", fill="y")
        self.app_canvas.pack(side="left", fill="both", expand=True)

        self.main = tk.Frame(self.app_canvas, bg=self.bg)
        self.main_window = self.app_canvas.create_window((0, 0), window=self.main, anchor="nw")

        self.main.bind("<Configure>", self._on_main_configure)
        self.app_canvas.bind("<Configure>", self._on_canvas_configure)
        self.app_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_main_configure(self, event=None):
        self.app_canvas.configure(scrollregion=self.app_canvas.bbox("all"))

        first, _ = self.app_canvas.yview()
        if first < 0.001:
            self.app_canvas.yview_moveto(0)

    def _on_canvas_configure(self, event):
        self.app_canvas.itemconfigure(self.main_window, width=event.width)

    def _on_mousewheel(self, event):
        first, last = self.app_canvas.yview()

        # Prevent scrolling above the top and leaving a blank gap.
        if event.delta > 0 and first <= 0:
            self.app_canvas.yview_moveto(0)
            return

        # Prevent scrolling below the bottom.
        if event.delta < 0 and last >= 1:
            self.app_canvas.yview_moveto(1)
            return

        self.app_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def make_panel(self, parent, compact=False):
        return tk.Frame(
            parent,
            bg=self.panel if not compact else self.panel2,
            highlightbackground=self.border2 if not compact else self.border,
            highlightthickness=1,
            bd=0,
        )

    def make_section_title(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=parent["bg"],
            fg=self.subtle,
            font=("Segoe UI", self.s(9), "bold"),
        ).pack(anchor="w", padx=self.s(10), pady=(self.s(4), self.s(1)))

    def make_scale(self, parent, **kwargs):
        return tk.Scale(
            parent,
            orient=tk.HORIZONTAL,
            bg=parent["bg"],
            fg=self.text,
            troughcolor="#232323",
            activebackground=self.red,
            highlightthickness=0,
            sliderrelief="flat",
            bd=0,
            width=self.s(10),
            sliderlength=self.s(16),
            font=("Segoe UI", self.s(9)),
            **kwargs,
        )

    def make_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.red3,
            fg=self.text,
            activebackground=self.red2,
            activeforeground="#f7ece8",
            relief="flat",
            bd=0,
            padx=self.s(10),
            pady=self.s(6),
            font=("Segoe UI", self.s(9), "bold"),
            highlightthickness=1,
            highlightbackground=self.border2,
            cursor="hand2",
        )

    def make_flat_text_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=parent["bg"],
            fg=self.red,
            activebackground=parent["bg"],
            activeforeground=self.red2,
            relief="flat",
            bd=0,
            padx=self.s(4),
            pady=0,
            font=("Segoe UI", self.s(9), "bold"),
            highlightthickness=0,
            cursor="hand2",
        )

    def make_donate_button(self, parent, small=False):
        return tk.Button(
            parent,
            text="❤ PayPal Donate",
            command=lambda: webbrowser.open(DONATE_URL),
            bg=self.red,
            fg="#f7ece8",
            activebackground=self.red2,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=self.s(8 if small else 10),
            pady=self.s(3 if small else 6),
            font=("Segoe UI", self.s(8 if small else 9), "bold"),
            highlightthickness=1,
            highlightbackground=self.border2,
            cursor="hand2",
        )

    def draw_waterwheel_icon(self, canvas):
        canvas.delete("all")
        w = int(canvas["width"])
        h = int(canvas["height"])

        cx = (w / 2.0) - 1
        cy = (h / 2.0) - 1

        line_color = "#f7ece8"
        rim_r = min(w, h) * 0.285
        hub_r = rim_r * 0.34
        outer_r = rim_r + self.s(2)

        canvas.create_oval(
            cx - rim_r,
            cy - rim_r,
            cx + rim_r,
            cy + rim_r,
            outline=line_color,
            width=max(2, self.s(2)),
        )

        canvas.create_oval(
            cx - hub_r,
            cy - hub_r,
            cx + hub_r,
            cy + hub_r,
            outline=line_color,
            width=max(2, self.s(2)),
        )

        dot_r = max(2, self.s(2))
        canvas.create_oval(
            cx - dot_r,
            cy - dot_r,
            cx + dot_r,
            cy + dot_r,
            fill=line_color,
            outline=line_color,
        )

        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            x1 = cx + math.cos(angle) * (hub_r * 0.65)
            y1 = cy + math.sin(angle) * (hub_r * 0.65)
            x2 = cx + math.cos(angle) * (rim_r - self.s(2))
            y2 = cy + math.sin(angle) * (rim_r - self.s(2))
            canvas.create_line(
                x1, y1, x2, y2,
                fill=line_color,
                width=max(2, self.s(2)),
                capstyle=tk.ROUND,
            )

        paddle_len = self.s(5)
        for angle_deg in range(0, 360, 45):
            angle = math.radians(angle_deg)
            x = cx + math.cos(angle) * outer_r
            y = cy + math.sin(angle) * outer_r
            px = math.cos(angle + math.pi / 2) * paddle_len
            py = math.sin(angle + math.pi / 2) * paddle_len
            canvas.create_line(
                x - px, y - py, x + px, y + py,
                fill=line_color,
                width=max(2, self.s(2)),
                capstyle=tk.ROUND,
            )

        stand_top_y = cy + rim_r + self.s(2)
        stand_bottom_y = h - self.s(8)
        left_x = cx - rim_r * 0.72
        right_x = cx + rim_r * 0.72

        canvas.create_line(
            left_x, stand_top_y,
            left_x - self.s(4), stand_bottom_y,
            fill=line_color,
            width=max(2, self.s(2)),
            capstyle=tk.ROUND,
        )
        canvas.create_line(
            right_x, stand_top_y,
            right_x + self.s(4), stand_bottom_y,
            fill=line_color,
            width=max(2, self.s(2)),
            capstyle=tk.ROUND,
        )
        canvas.create_line(
            left_x - self.s(7), stand_bottom_y,
            right_x + self.s(7), stand_bottom_y,
            fill=line_color,
            width=max(2, self.s(2)),
            capstyle=tk.ROUND,
        )

    def _build_list_panel(self, parent):
        outer = tk.Frame(parent, bg=self.list_bg)
        outer.pack(fill="both", expand=True)

        content = tk.Frame(outer, bg=self.list_bg)
        content.pack(fill="both", expand=True, padx=self.s(4), pady=self.s(4))

        list_frame = tk.Frame(content, bg=self.list_bg)
        list_frame.pack(fill="both", expand=True)

        listbox = tk.Listbox(
            list_frame,
            bg=self.list_bg,
            fg=self.text,
            selectbackground=self.red3,
            selectforeground="#f5e7e1",
            highlightthickness=1,
            highlightbackground="#1e1e1e",
            relief="flat",
            bd=0,
            activestyle="none",
            height=14,
            font=("Segoe UI", self.song_font_size),
        )

        scrollbar = DarkScrollbar(
            list_frame,
            command=listbox.yview,
            bg=self.list_bg,
            trough=self.panel,
            thumb=self.red3,
            active=self.red2,
            width=self.s(12),
        )
        listbox.configure(yscrollcommand=scrollbar.set)

        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        empty_frame = tk.Frame(content, bg=self.list_bg)

        empty_icon = tk.Label(
            empty_frame,
            text="♫",
            bg=self.list_bg,
            fg="#d7d7d7",
            font=("Segoe UI Symbol", self.s(34), "bold"),
        )
        empty_icon.pack(pady=(self.s(40), self.s(8)))

        empty_title = tk.Label(
            empty_frame,
            text="",
            bg=self.list_bg,
            fg=self.subtle,
            font=("Segoe UI", self.s(13), "bold"),
        )
        empty_title.pack()

        empty_sub = tk.Label(
            empty_frame,
            text="",
            bg=self.list_bg,
            fg=self.subtle,
            font=("Segoe UI", self.s(10)),
        )
        empty_sub.pack(pady=(self.s(6), 0))

        return {
            "outer": outer,
            "list_frame": list_frame,
            "listbox": listbox,
            "empty_frame": empty_frame,
            "empty_title": empty_title,
            "empty_sub": empty_sub,
        }

    def _build_ui(self):
        top_bar = tk.Frame(self.main, bg=self.bg)
        top_bar.pack(fill="x", pady=(self.s(10), self.s(8)), padx=self.s(14))

        left_cluster = tk.Frame(top_bar, bg=self.bg)
        left_cluster.pack(side="left")

        port_wrap = self.make_panel(left_cluster, compact=True)
        port_wrap.pack(side="left", anchor="nw")

        tk.Label(
            port_wrap,
            text="MIDI PORT",
            bg=port_wrap["bg"],
            fg=self.subtle,
            font=("Segoe UI", self.s(8), "bold"),
        ).pack(anchor="w", padx=self.s(8), pady=(self.s(6), self.s(2)))

        self.port = ttk.Combobox(port_wrap, width=18, style="Rust.TCombobox")
        self.port.pack(padx=self.s(8), pady=(0, self.s(8)))

        settings_wrap = tk.Frame(
            left_cluster,
            bg=self.red3,
            highlightbackground=self.border2,
            highlightthickness=1,
            bd=0,
            width=self.s(58),
            height=self.s(58),
        )
        settings_wrap.pack(side="left", padx=(self.s(8), 0))
        settings_wrap.pack_propagate(False)

        self.settings_canvas = tk.Canvas(
            settings_wrap,
            width=self.s(58),
            height=self.s(58),
            bg=self.red3,
            highlightthickness=0,
            bd=0,
            relief="flat",
            cursor="hand2",
        )
        self.settings_canvas.pack(fill="both", expand=True)
        self.draw_waterwheel_icon(self.settings_canvas)
        self.settings_canvas.bind("<Button-1>", lambda e: self.open_settings())

        band_wrap = tk.Frame(top_bar, bg=self.bg)
        band_wrap.place(relx=0.5, rely=0.5, anchor="center")

        self.band_button = tk.Button(
            band_wrap,
            text="BAND",
            command=lambda: messagebox.showinfo(
                "Band Sync",
                "Band and multiplayer sync features are coming soon."
            ),
            bg=self.red3,
            fg="#f7ece8",
            activebackground=self.red2,
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=self.s(30),
            pady=self.s(8),
            font=("Segoe UI", self.s(13), "bold"),
            highlightthickness=1,
            highlightbackground=self.border2,
            cursor="hand2",
        )
        self.band_button.pack()

        tk.Label(
            band_wrap,
            text="Coming soon",
            bg=self.bg,
            fg=self.subtle,
            font=("Segoe UI", self.s(8), "bold"),
        ).pack(pady=(self.s(2), 0))

        brand_wrap = tk.Frame(top_bar, bg=self.bg)
        brand_wrap.pack(side="right", anchor="ne")

        tk.Label(
            brand_wrap,
            text=APP_NAME.upper(),
            bg=self.bg,
            fg=self.red,
            font=("Segoe UI", self.s(11), "bold"),
        ).pack(anchor="e")

        meta_row = tk.Frame(brand_wrap, bg=self.bg)
        meta_row.pack(anchor="e")

        tk.Label(
            meta_row,
            text=APP_AUTHOR,
            bg=self.bg,
            fg=self.subtle,
            font=("Segoe UI", self.s(8)),
        ).pack(side="left")

        tk.Label(
            meta_row,
            text=f"   •   Version {APP_VERSION}",
            bg=self.bg,
            fg=self.subtle,
            font=("Segoe UI", self.s(8)),
        ).pack(side="left")

        donate_holder = tk.Frame(brand_wrap, bg=self.bg)
        donate_holder.pack(anchor="e", pady=(self.s(4), 0))
        self.make_donate_button(donate_holder, small=True).pack(anchor="e")

        now_panel = self.make_panel(self.main)
        now_panel.pack(fill="x", pady=(0, self.s(8)), padx=self.s(14))

        now_header = tk.Frame(now_panel, bg=now_panel["bg"], height=self.s(24))
        now_header.pack(fill="x", padx=self.s(10), pady=(self.s(3), self.s(1)))
        now_header.pack_propagate(False)

        tk.Label(
            now_header,
            text="NOW PLAYING",
            bg=now_panel["bg"],
            fg=self.subtle,
            font=("Segoe UI", self.s(9), "bold"),
        ).pack(side="left", anchor="w")

        self.auto_next_var = tk.BooleanVar(value=False)
        self.auto_next_cb = tk.Checkbutton(
            now_header,
            text="Auto Play Next Song",
            variable=self.auto_next_var,
            command=self.on_toggle_auto_next,
            bg=now_panel["bg"],
            fg=self.text,
            activebackground=now_panel["bg"],
            activeforeground="#f7ece8",
            selectcolor=now_panel["bg"],
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", self.s(9), "bold"),
            padx=0,
            pady=0,
            cursor="hand2",
        )
        self.auto_next_cb.place(relx=0.5, rely=0.0, anchor="n")

        self.now = tk.Label(
            now_panel,
            text="No track loaded",
            bg=now_panel["bg"],
            fg=self.red,
            font=("Segoe UI", self.s(15), "bold"),
        )
        self.now.pack(pady=(0, self.s(2)))

        self.seek = self.make_scale(now_panel, from_=0, to=1, resolution=0.01)
        self.seek.pack(fill="x", padx=self.s(12), pady=(0, self.s(6)))
        self.seek.bind("<ButtonPress-1>", self.start_drag)
        self.seek.bind("<ButtonRelease-1>", self.end_drag)

        speed_panel = self.make_panel(self.main)
        speed_panel.pack(fill="x", pady=(0, self.s(5)), padx=self.s(14))
        self.make_section_title(speed_panel, "SPEED")
        self.speed = self.make_scale(
            speed_panel,
            from_=0.0,
            to=2.0,
            resolution=0.01,
            command=self.set_speed,
        )
        self.speed.set(1.0)
        self.speed.pack(fill="x", padx=self.s(12), pady=(0, self.s(3)))

        volume_panel = self.make_panel(self.main)
        volume_panel.pack(fill="x", pady=(0, self.s(5)), padx=self.s(14))
        self.make_section_title(volume_panel, "PLAY VOLUME")
        self.volume = self.make_scale(
            volume_panel,
            from_=0.0,
            to=2.0,
            resolution=0.01,
            command=self.set_volume,
        )
        self.volume.set(1.0)
        self.volume.pack(fill="x", padx=self.s(12), pady=(0, self.s(3)))

        transpose_panel = self.make_panel(self.main)
        transpose_panel.pack(fill="x", pady=(0, self.s(5)), padx=self.s(14))
        self.make_section_title(transpose_panel, "TRANSPOSE")
        self.transpose = self.make_scale(
            transpose_panel,
            from_=-24,
            to=24,
            resolution=1,
            command=self.set_transpose,
        )
        self.transpose.set(0)
        self.transpose.pack(fill="x", padx=self.s(12), pady=(0, self.s(3)))

        controls_panel = self.make_panel(self.main)
        controls_panel.pack(fill="x", pady=(0, self.s(6)), padx=self.s(14))

        btn_row = tk.Frame(controls_panel, bg=controls_panel["bg"])
        btn_row.pack(fill="x", padx=self.s(8), pady=self.s(8))

        shortcuts = self.settings_data.get("shortcuts", {})
        pp = shortcuts.get("play_pause", "F9")
        nx = shortcuts.get("next_track", "F10")
        pr = shortcuts.get("previous_track", "F11")

        buttons = [
            ("play_pause", f"▶ PLAY/PAUSE ({pp})", self.toggle),
            ("next_track", f"⏭ NEXT ({nx})", self.play_next),
            ("previous_track", f"⏮ PREVIOUS ({pr})", self.play_previous),
            ("reset", "⟲ RESET", self.stop_current),
            ("add", "＋ ADD MIDI", self.add_files_dialog),
        ]

        self.transport_buttons = {}
        for i, (key, label, cmd) in enumerate(buttons):
            btn_row.grid_columnconfigure(i, weight=1, uniform="transport")
            b = self.make_button(btn_row, label, cmd)
            b.grid(row=0, column=i, padx=self.s(3), sticky="ew")
            self.transport_buttons[key] = b

        playlist_panel = self.make_panel(self.main)
        playlist_panel.pack(fill="both", expand=True, pady=(0, self.s(8)), padx=self.s(14))
        self.make_section_title(playlist_panel, "PLAYLIST")

        self.notebook = ttk.Notebook(playlist_panel, style="Rust.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=self.s(12), pady=(0, self.s(8)))

        self.playlist_tab = tk.Frame(self.notebook, bg=self.list_bg)
        self.favorites_tab = tk.Frame(self.notebook, bg=self.list_bg)
        self.notebook.add(self.playlist_tab, text="Playlist")
        self.notebook.add(self.favorites_tab, text="Favorites ♻")

        self.playlist_view = self._build_list_panel(self.playlist_tab)
        self.favorites_view = self._build_list_panel(self.favorites_tab)

        self.playlist_view["listbox"].bind("<<ListboxSelect>>", self.on_playlist_select)
        self.favorites_view["listbox"].bind("<<ListboxSelect>>", self.on_favorites_select)
        self.playlist_view["listbox"].bind("<Double-Button-1>", lambda e: self.play_selected_from_active_tab())
        self.favorites_view["listbox"].bind("<Double-Button-1>", lambda e: self.play_selected_from_active_tab())

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        playlist_bottom = tk.Frame(self.playlist_tab, bg=self.list_bg)
        playlist_bottom.pack(fill="x", padx=self.s(6), pady=(self.s(4), self.s(6)))

        self.add_fav_btn = self.make_flat_text_button(
            playlist_bottom,
            "♻ Add Selected to Favorites",
            self.add_selected_to_favorites,
        )
        self.add_fav_btn.pack(side="left")

        self.clear_playlist_btn = self.make_flat_text_button(
            playlist_bottom,
            "💥 Clear Playlist",
            self.clear_playlist,
        )
        self.clear_playlist_btn.pack(side="right")

        fav_bottom = tk.Frame(self.favorites_tab, bg=self.list_bg)
        fav_bottom.pack(fill="x", padx=self.s(6), pady=(self.s(4), self.s(6)))

        self.remove_fav_btn = self.make_flat_text_button(
            fav_bottom,
            "♻ Remove Selected Favorite",
            self.remove_selected_favorite,
        )
        self.remove_fav_btn.pack(side="left")

        for widget in (
            self.playlist_tab,
            self.playlist_view["outer"],
            self.playlist_view["listbox"],
            self.favorites_tab,
            self.favorites_view["outer"],
            self.favorites_view["listbox"],
        ):
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self.drop)

        channels_panel = self.make_panel(self.main)
        channels_panel.pack(fill="x", side="bottom", pady=(0, self.s(8)), padx=self.s(14))
        self.make_section_title(channels_panel, "CHANNEL MUTE / SCANNED NOTE COUNTS")

        ch_row = tk.Frame(channels_panel, bg=channels_panel["bg"])
        ch_row.pack(fill="x", padx=self.s(8), pady=(0, self.s(8)))

        self.channel_labels = []
        for ch in range(16):
            ch_row.grid_columnconfigure(ch, weight=1, uniform="channels")
            lbl = tk.Label(
                ch_row,
                text=f"{ch+1}\n0",
                bg=self.red3,
                fg=self.text,
                width=5,
                height=2,
                font=("Segoe UI", self.s(8), "bold"),
                relief="flat",
                bd=0,
                highlightthickness=1,
                highlightbackground=self.border2,
            )
            lbl.grid(row=0, column=ch, padx=self.s(2), sticky="ew")
            lbl.bind("<Button-1>", lambda e, c=ch: self.toggle_channel_mute(c))
            self.channel_labels.append(lbl)

    def _restore_runtime_settings(self):
        self.player.auto_play_next = bool(self.settings_data.get("auto_play_next", False))
        self.auto_next_var.set(self.player.auto_play_next)

        speed = self._sanitize_speed(self.settings_data.get("speed", 1.0))
        volume = self._sanitize_volume(self.settings_data.get("volume", 1.0))
        transpose = int(self.settings_data.get("transpose", 0))

        self.speed.set(speed)
        self.volume.set(volume)
        self.transpose.set(transpose)

        self.player.set_speed(speed)
        self.player.set_volume(volume)
        self.player.set_transpose(transpose)

        saved_tab = self.settings_data.get("active_tab", "playlist")
        if saved_tab == "favorites":
            self.active_source = "favorites"
            self.notebook.select(self.favorites_tab)
        else:
            self.active_source = "playlist"
            self.notebook.select(self.playlist_tab)

        p_idx = self.settings_data.get("playlist_selected_index")
        f_idx = self.settings_data.get("favorites_selected_index")
        if isinstance(p_idx, int):
            self.playlist.selected_index = p_idx
        if isinstance(f_idx, int):
            self.favorites.selected_index = f_idx

        self.current_track_path = self.settings_data.get("current_track_path")
        self.current_track_source = self.settings_data.get("current_track_source")

        if self.current_track_path:
            self.ensure_track_scanned(self.current_track_path)
            self.apply_track_mute_state(self.current_track_path)

    def current_state(self):
        return self.playlist if self.active_source == "playlist" else self.favorites

    def get_state_by_source(self, source):
        return self.playlist if source == "playlist" else self.favorites

    def on_tab_changed(self, event=None):
        current = self.notebook.select()
        if current == str(self.playlist_tab):
            self.active_source = "playlist"
        else:
            self.active_source = "favorites"
        self._update_favorite_button_text()
        self._last_channel_state = None

    def on_toggle_auto_next(self):
        self.player.auto_play_next = bool(self.auto_next_var.get())

    def _set_view_empty(self, view, title_text, sub_text):
        view["list_frame"].pack_forget()
        view["empty_title"].configure(text=title_text)
        view["empty_sub"].configure(text=sub_text)
        view["empty_frame"].pack(fill="both", expand=True)

    def _set_view_list(self, view):
        view["empty_frame"].pack_forget()
        view["list_frame"].pack(fill="both", expand=True)

    def refresh_playlist_views(self):
        self._refresh_single_view(
            self.playlist_view,
            self.playlist,
            empty_title="DRAG AND DROP MIDI FILES HERE",
            empty_sub="or click '+ ADD MIDI' to add files",
        )
        self._refresh_single_view(
            self.favorites_view,
            self.favorites,
            empty_title="NO FAVORITES SAVED YET",
            empty_sub="",
        )
        self._update_favorite_button_text()

    def _refresh_single_view(self, view, state, empty_title, empty_sub):
        listbox = view["listbox"]
        listbox.delete(0, tk.END)

        if not state.items:
            self._set_view_empty(view, empty_title, empty_sub)
            return

        self._set_view_list(view)

        for path in state.items:
            listbox.insert(tk.END, os.path.basename(path))

        if state.selected_index is not None and 0 <= state.selected_index < len(state.items):
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(state.selected_index)
            listbox.see(state.selected_index)

    def _update_favorite_button_text(self):
        path = self.playlist.selected_path()
        if path and path in self.favorites.items:
            self.add_fav_btn.configure(text="♻ Remove Selected from Favorites")
        else:
            self.add_fav_btn.configure(text="♻ Add Selected to Favorites")

    def on_playlist_select(self, event=None):
        selection = self.playlist_view["listbox"].curselection()
        if selection:
            self.playlist.select(selection[0])
            self._update_favorite_button_text()
            self._last_channel_state = None

    def on_favorites_select(self, event=None):
        selection = self.favorites_view["listbox"].curselection()
        if selection:
            self.favorites.select(selection[0])
            self._last_channel_state = None

    def add_files_dialog(self):
        files = askopenfilenames(filetypes=[("MIDI Files", "*.mid")])
        if not files:
            return

        for f in files:
            self.playlist.add(f)
            self.ensure_track_scanned(f)

        self.active_source = "playlist"
        self.notebook.select(self.playlist_tab)
        self.refresh_playlist_views()
        self._last_channel_state = None

    def drop(self, event):
        files = self.root.tk.splitlist(event.data)
        added = False

        for f in files:
            if f.lower().endswith(".mid"):
                self.playlist.add(f)
                self.ensure_track_scanned(f)
                added = True

        if added:
            self.active_source = "playlist"
            self.notebook.select(self.playlist_tab)
            self.refresh_playlist_views()
            self._last_channel_state = None

    def add_selected_to_favorites(self):
        path = self.playlist.selected_path()
        if not path:
            return

        if path in self.favorites.items:
            self.favorites.remove(path)

            persistent = self.settings_data.setdefault("track_mute_settings", {})
            if path in persistent:
                self.session_track_mute_settings[path] = list(persistent[path])
                del persistent[path]
        else:
            self.favorites.add(path)
            self.ensure_track_scanned(path)

            if path in self.session_track_mute_settings:
                self.settings_data.setdefault("track_mute_settings", {})[path] = list(self.session_track_mute_settings[path])
                del self.session_track_mute_settings[path]
            elif self.current_track_path == path:
                self.settings_data.setdefault("track_mute_settings", {})[path] = sorted(self.player.muted_channels)
            else:
                self.settings_data.setdefault("track_mute_settings", {}).setdefault(path, [])

        self.save_settings()
        self.refresh_playlist_views()

    def remove_selected_favorite(self):
        path = self.favorites.selected_path()
        if not path:
            return

        persistent = self.settings_data.setdefault("track_mute_settings", {})
        if path in persistent:
            self.session_track_mute_settings[path] = list(persistent[path])
            del persistent[path]

        self.favorites.remove(path)
        self.save_settings()
        self.refresh_playlist_views()
        self._last_channel_state = None

    def clear_playlist(self):
        self.player.stop()
        self.current_track_path = None
        self.current_track_source = None
        self.playlist.clear()
        self.session_track_mute_settings.clear()
        self.refresh_playlist_views()
        self._last_channel_state = None
        self.player.set_muted_channels(set())

    def refresh_ports(self):
        ports = get_output_names()
        self.port["values"] = ports
        if not ports:
            return

        preferred = self.settings_data.get("default_port", "")
        if preferred and preferred in ports:
            self.port.set(preferred)
        elif len(ports) > 1:
            self.port.set(ports[1])
        else:
            self.port.set(ports[0])

    def _restore_saved_favorites_only(self):
        valid_favs = []
        for path in self.settings_data.get("favorites", []):
            if os.path.exists(path):
                valid_favs.append(path)
        self.favorites.set_items(valid_favs)
        for path in valid_favs:
            self.ensure_track_scanned(path)
        self.save_settings()

    def selected_path_from_active_tab(self):
        return self.current_state().selected_path()

    def _mark_current_track(self, filepath, source):
        self.current_track_path = filepath
        self.current_track_source = source
        self.ensure_track_scanned(filepath)
        state = self.get_state_by_source(source)
        idx = state.index_of(filepath)
        if idx is not None:
            state.select(idx)

    def _selected_track_is_different_from_current(self):
        selected_path = self.selected_path_from_active_tab()
        return bool(selected_path and selected_path != self.current_track_path)

    def play_selected_from_active_tab(self):
        filepath = self.selected_path_from_active_tab()
        if not filepath:
            return False

        self.save_current_track_mute_state()

        if not self.player.outport:
            if not self.player.connect(self.port.get()):
                if not self.player.reconnect(self.port.get()):
                    messagebox.showerror("MIDI Port", "Could not connect to the selected MIDI port.")
                    return False

        started = self.player.start_playback(filepath)
        if not started:
            messagebox.showerror("MIDI File", "Could not load or play the selected MIDI file.")
            return False

        self._mark_current_track(filepath, self.active_source)
        self.apply_track_mute_state(filepath)
        self.refresh_playlist_views()
        self.save_settings()
        self._last_channel_state = None
        return True

    def toggle(self):
        if self.player.state == Transport.PLAYING:
            self.player.pause()
            return

        if self.player.state == Transport.PAUSED:
            if self._selected_track_is_different_from_current():
                self.play_selected_from_active_tab()
            else:
                self.player.resume()
            return

        self.play_selected_from_active_tab()

    def _source_for_transport_nav(self):
        if self.current_track_source and self.player.state in (Transport.PLAYING, Transport.PAUSED):
            return self.current_track_source
        return self.active_source

    def play_next(self):
        self.save_current_track_mute_state()
        source = self._source_for_transport_nav()
        state = self.get_state_by_source(source)
        idx = state.next_index()
        if idx is None:
            return
        state.select(idx)
        self.refresh_playlist_views()
        self.play_from_source_selection(source)

    def play_previous(self):
        self.save_current_track_mute_state()
        source = self._source_for_transport_nav()
        state = self.get_state_by_source(source)
        idx = state.previous_index()
        if idx is None:
            return
        state.select(idx)
        self.refresh_playlist_views()
        self.play_from_source_selection(source)

    def play_from_source_selection(self, source):
        state = self.get_state_by_source(source)
        filepath = state.selected_path()
        if not filepath:
            return False

        self.save_current_track_mute_state()

        if not self.player.outport:
            if not self.player.connect(self.port.get()):
                if not self.player.reconnect(self.port.get()):
                    messagebox.showerror("MIDI Port", "Could not connect to the selected MIDI port.")
                    return False

        started = self.player.start_playback(filepath)
        if not started:
            messagebox.showerror("MIDI File", "Could not load or play the selected MIDI file.")
            return False

        self._mark_current_track(filepath, source)
        self.apply_track_mute_state(filepath)
        self.refresh_playlist_views()
        self.save_settings()
        self._last_channel_state = None
        return True

    def stop_current(self):
        self.player.stop()

    def on_track_finished(self):
        if self.player.auto_play_next:
            self.root.after(0, self.play_next)

    def set_speed(self, v):
        self.player.set_speed(self._sanitize_speed(v))

    def set_volume(self, v):
        self.player.set_volume(self._sanitize_volume(v))

    def set_transpose(self, v):
        self.player.set_transpose(float(v))

    def start_drag(self, event):
        self.user_dragging = True

    def end_drag(self, event):
        self.user_dragging = False
        self.player.seek(self.seek.get())

    def _make_text_tab(self, tabs, title, content):
        frame = tk.Frame(tabs, bg=self.panel)
        tabs.add(frame, text=title)

        text_widget = tk.Text(
            frame,
            bg="#101010",
            fg=self.text,
            wrap="word",
            relief="flat",
            bd=0,
            font=("Consolas", self.s(10)),
            insertbackground=self.text,
        )
        scroll = tk.Scrollbar(frame, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scroll.set)

        text_widget.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        bold_font = ("Consolas", self.s(10), "bold")
        heading_font = ("Consolas", self.s(12), "bold")
        text_widget.tag_configure("bold", font=bold_font)
        text_widget.tag_configure(
            "heading",
            font=heading_font,
            foreground="#f5e7e1",
            spacing1=self.s(6),
            spacing3=self.s(4),
        )

        for line in content.splitlines(True):
            stripped = line.strip()

            if stripped.startswith("# "):
                text_widget.insert("end", stripped[2:] + "\n", "heading")
                continue

            if stripped.startswith("**") and stripped.endswith("**") and stripped.count("**") == 2:
                text_widget.insert("end", stripped[2:-2] + "\n", "heading")
                continue

            if "**" in line:
                parts = line.split("**")
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        text_widget.insert("end", part, "bold")
                    else:
                        text_widget.insert("end", part)
            else:
                text_widget.insert("end", line)

        text_widget.config(state="disabled")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        apply_window_icon(win)
        win.title(f"{APP_NAME} Settings")
        win.geometry(f"{self.s(820)}x{self.s(880)}")
        win.configure(bg=self.panel)
        set_dark_title_bar(win)
        win.resizable(True, True)

        top = tk.Frame(win, bg=self.panel)
        top.pack(fill="x", padx=self.s(14), pady=(self.s(14), self.s(8)))

        tk.Label(
            top,
            text="Default Port Selection",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", self.s(10), "bold"),
        ).grid(row=0, column=0, sticky="w")

        port_box = ttk.Combobox(top, width=34, style="Rust.TCombobox")
        ports = get_output_names()
        port_box["values"] = ports
        port_box.grid(row=1, column=0, sticky="w", pady=(self.s(6), self.s(12)))

        saved = self.settings_data.get("default_port", "")
        if saved and saved in ports:
            port_box.set(saved)
        elif self.port.get():
            port_box.set(self.port.get())

        tk.Label(
            top,
            text="UI Scale",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", self.s(10), "bold"),
        ).grid(row=0, column=1, sticky="w", padx=(self.s(20), 0))

        ui_scale_box = ttk.Combobox(top, width=12, style="Rust.TCombobox", state="readonly")
        ui_scale_box["values"] = ["0.8", "0.9", "1.0", "1.1", "1.2", "1.3"]
        ui_scale_box.set(str(self.settings_data.get("ui_scale", self.ui_scale)))
        ui_scale_box.grid(row=1, column=1, sticky="w", padx=(self.s(20), 0), pady=(self.s(6), self.s(12)))

        visual_panel = tk.Frame(win, bg=self.panel)
        visual_panel.pack(fill="x", padx=self.s(14), pady=(0, self.s(8)))

        tk.Label(
            visual_panel,
            text="Song Name Font Size",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", self.s(10), "bold"),
        ).grid(row=0, column=0, sticky="w")

        song_font_box = ttk.Combobox(visual_panel, width=12, style="Rust.TCombobox", state="readonly")
        song_font_box["values"] = ["8", "9", "10", "11", "12", "13", "14", "15", "16"]
        song_font_box.set(str(self.settings_data.get("song_font_size", self.song_font_size)))
        song_font_box.grid(row=1, column=0, sticky="w", pady=(self.s(6), self.s(10)))

        tk.Label(
            visual_panel,
            text="App Refresh Rate",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", self.s(10), "bold"),
        ).grid(row=0, column=1, sticky="w", padx=(self.s(20), 0))

        refresh_box = ttk.Combobox(visual_panel, width=22, style="Rust.TCombobox", state="readonly")
        refresh_options = {
            "50 ms (Quality)": 50,
            "125 ms (Normal)": 125,
            "250 ms (Balanced)": 250,
            "500 ms (Performance)": 500,
        }
        refresh_box["values"] = list(refresh_options.keys())
        current_refresh = int(self.settings_data.get("ui_refresh_ms", self.ui_refresh_ms))
        selected_refresh_label = "125 ms (Normal)"
        for label, value in refresh_options.items():
            if value == current_refresh:
                selected_refresh_label = label
                break
        refresh_box.set(selected_refresh_label)
        refresh_box.grid(row=1, column=1, sticky="w", padx=(self.s(20), 0), pady=(self.s(6), self.s(10)))

        tk.Label(
            visual_panel,
            text="UI Scale applies best after restarting the app. Song font size and refresh rate apply immediately after saving.",
            bg=self.panel,
            fg=self.subtle,
            justify="left",
            wraplength=self.s(760),
            font=("Segoe UI", self.s(8)),
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, self.s(4)))

        shortcuts_panel = tk.Frame(win, bg=self.panel)
        shortcuts_panel.pack(fill="x", padx=self.s(14), pady=(0, self.s(8)))

        tk.Label(
            shortcuts_panel,
            text="Global Shortcuts",
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", self.s(10), "bold"),
        ).grid(row=0, column=0, sticky="w")

        shortcuts_enabled_var = tk.BooleanVar(value=bool(self.settings_data.get("shortcuts_enabled", True)))
        shortcuts_enabled_cb = tk.Checkbutton(
            shortcuts_panel,
            text="Enabled",
            variable=shortcuts_enabled_var,
            bg=self.panel,
            fg=self.text,
            activebackground=self.panel,
            activeforeground="#f7ece8",
            selectcolor=self.red3,
            highlightthickness=0,
            bd=0,
            font=("Segoe UI", self.s(9), "bold"),
            padx=self.s(8),
            pady=self.s(4),
        )
        shortcuts_enabled_cb.grid(row=0, column=1, sticky="w", padx=(self.s(10), 0))

        shortcut_values = self.settings_data.get("shortcuts", {})
        play_pause_var = tk.StringVar(value=shortcut_values.get("play_pause", "F9"))
        next_var = tk.StringVar(value=shortcut_values.get("next_track", "F10"))
        previous_var = tk.StringVar(value=shortcut_values.get("previous_track", "F11"))

        tk.Label(shortcuts_panel, text="Play / Pause", bg=self.panel, fg=self.subtle, font=("Segoe UI", self.s(9), "bold")).grid(row=1, column=0, sticky="w", pady=(self.s(8), 0))
        play_pause_entry = tk.Entry(shortcuts_panel, textvariable=play_pause_var, bg="#101010", fg=self.text, insertbackground=self.text, relief="flat", bd=0, font=("Segoe UI", self.s(9)), width=14)
        play_pause_entry.grid(row=1, column=1, sticky="w", padx=(self.s(10), 0), pady=(self.s(8), 0))

        tk.Label(shortcuts_panel, text="Next", bg=self.panel, fg=self.subtle, font=("Segoe UI", self.s(9), "bold")).grid(row=2, column=0, sticky="w", pady=(self.s(8), 0))
        next_entry = tk.Entry(shortcuts_panel, textvariable=next_var, bg="#101010", fg=self.text, insertbackground=self.text, relief="flat", bd=0, font=("Segoe UI", self.s(9)), width=14)
        next_entry.grid(row=2, column=1, sticky="w", padx=(self.s(10), 0), pady=(self.s(8), 0))

        tk.Label(shortcuts_panel, text="Previous", bg=self.panel, fg=self.subtle, font=("Segoe UI", self.s(9), "bold")).grid(row=3, column=0, sticky="w", pady=(self.s(8), 0))
        previous_entry = tk.Entry(shortcuts_panel, textvariable=previous_var, bg="#101010", fg=self.text, insertbackground=self.text, relief="flat", bd=0, font=("Segoe UI", self.s(9)), width=14)
        previous_entry.grid(row=3, column=1, sticky="w", padx=(self.s(10), 0), pady=(self.s(8), 0))

        shortcuts_panel.grid_columnconfigure(2, weight=1)
        rust_console_panel = tk.Frame(
            shortcuts_panel,
            bg="#101010",
            highlightbackground=self.border2,
            highlightthickness=1,
            bd=0,
        )
        rust_console_panel.grid(
            row=0,
            column=2,
            rowspan=4,
            sticky="nsew",
            padx=(self.s(70), 0),
            pady=(0, self.s(2)),
        )

        tk.Label(
            rust_console_panel,
            text="Rust Console (F1) Commands",
            bg="#101010",
            fg=self.text,
            font=("Segoe UI", self.s(9), "bold"),
        ).pack(anchor="w", padx=self.s(8), pady=(self.s(6), 0))

        tk.Label(
            rust_console_panel,
            text="Useful Rust console commands. Full setup guide is in the Rust Optimization tab.",
            bg="#101010",
            fg=self.subtle,
            justify="left",
            wraplength=self.s(390),
            font=("Segoe UI", self.s(8)),
        ).pack(anchor="w", padx=self.s(8), pady=(self.s(1), self.s(4)))

        console_commands = (
            "gc.collect      - run this before a song to clear game memory.\n"
            "gc.buffer 1024  - 1 GB buffer, 8-16 GB RAM\n"
            "gc.buffer 2048  - 2 GB buffer, 16 GB RAM\n"
            "gc.buffer 4096  - 4 GB buffer, ideal for 32 GB RAM\n"
            "gc.buffer 8192  - 8 GB buffer, 64 GB RAM"
        )
        console_box = tk.Text(
            rust_console_panel,
            height=5,
            width=52,
            bg="#0b0b0b",
            fg=self.text,
            insertbackground=self.text,
            relief="flat",
            bd=0,
            wrap="none",
            font=("Consolas", self.s(8)),
        )
        console_box.pack(fill="both", expand=True, padx=self.s(8), pady=(0, self.s(8)))
        console_box.insert("1.0", console_commands)
        console_box.config(state="disabled")

        info = tk.Label(
            win,
            text="Session saving is enabled. Favorites, loaded track, playback settings, active tab, window size/position, default port, UI scale, song font size, app refresh rate, shortcut settings, and Favorites mute selections are remembered. Playlist-only song mutes are saved temporarily for the current session.",
            bg=self.panel,
            fg=self.subtle,
            justify="left",
            wraplength=self.s(760),
            font=("Segoe UI", self.s(8)),
        )
        info.pack(anchor="w", padx=self.s(14), pady=(0, self.s(8)))

        donate_row = tk.Frame(win, bg=self.panel)
        donate_row.pack(fill="x", padx=self.s(14), pady=(0, self.s(8)))
        tk.Label(donate_row, text="Support Development", bg=self.panel, fg=self.text, font=("Segoe UI", self.s(9), "bold")).pack(side="left")
        self.make_donate_button(donate_row, small=False).pack(side="left", padx=(self.s(10), 0))

        tabs = ttk.Notebook(win)
        tabs.pack(fill="both", expand=True, padx=self.s(14), pady=(0, self.s(10)))
        self._make_text_tab(tabs, "README", README_TEXT)
        self._make_text_tab(tabs, "User Guide", USER_GUIDE_TEXT)
        self._make_text_tab(tabs, "Rust Optimization", RUST_OPTIMIZATION_TEXT)
        self._make_text_tab(tabs, "Troubleshooting", TROUBLESHOOTING_TEXT)
        self._make_text_tab(tabs, "License", LICENSE_TEXT)

        bottom = tk.Frame(win, bg=self.panel)
        bottom.pack(fill="x", padx=self.s(14), pady=(0, self.s(12)))
        tk.Label(
            bottom,
            text=f"{APP_NAME}  •  Version {APP_VERSION}  •  © 2026 Hamish Eagling (Hamish336)  •  Personal use only - see LICENSE.txt",
            bg=self.panel,
            fg=self.subtle,
            font=("Segoe UI", self.s(8)),
        ).pack(side="left")

        btn_row = tk.Frame(bottom, bg=self.panel)
        btn_row.pack(side="right")

        def save_and_close():
            old_ui_scale = float(self.settings_data.get("ui_scale", self.ui_scale))
            self.settings_data["default_port"] = port_box.get().strip()

            try:
                self.settings_data["ui_scale"] = float(ui_scale_box.get())
            except Exception:
                self.settings_data["ui_scale"] = 1.0

            try:
                self.song_font_size = max(8, min(16, int(song_font_box.get())))
            except Exception:
                self.song_font_size = 12
            self.settings_data["song_font_size"] = self.song_font_size

            self.ui_refresh_ms = refresh_options.get(refresh_box.get(), 125)
            self.settings_data["ui_refresh_ms"] = self.ui_refresh_ms

            self.settings_data["shortcuts_enabled"] = bool(shortcuts_enabled_var.get())
            self.settings_data["shortcuts"] = {
                "play_pause": play_pause_var.get().strip() or "F9",
                "next_track": next_var.get().strip() or "F10",
                "previous_track": previous_var.get().strip() or "F11",
            }

            for view in (getattr(self, "playlist_view", None), getattr(self, "favorites_view", None)):
                if view and "listbox" in view:
                    view["listbox"].configure(font=("Segoe UI", self.song_font_size))

            self.save_settings()
            self.refresh_ports()
            self.apply_shortcut_settings()
            self.update_transport_button_labels()
            win.destroy()

            if float(self.settings_data["ui_scale"]) != old_ui_scale:
                messagebox.showinfo("Settings Saved", "Settings saved. UI Scale changes apply best after restarting the app.")
            else:
                messagebox.showinfo("Settings Saved", "Settings saved.")

        self.make_button(btn_row, "Save", save_and_close).pack(side="left", padx=self.s(4))
        self.make_button(btn_row, "Close", win.destroy).pack(side="left", padx=self.s(4))

    def update(self):
        self.seek.config(to=max(self.player.total_time, 1))

        if not self.user_dragging:
            self.seek.set(self.player.current_playhead())

        if self.current_track_path:
            base = os.path.basename(self.current_track_path)
            if self.player.state != Transport.STOPPED:
                now_text = f"{self.player.state.upper()} - {base}"
            else:
                now_text = f"Loaded: {base}"
        else:
            now_text = "No track loaded"

        if now_text != self._last_now_text:
            self.now.config(text=now_text)
            self._last_now_text = now_text

        display_path = self.get_display_track_path()
        display_stats = self.get_display_track_stats()
        used_channels = display_stats["used_channels"]
        note_counts = display_stats["note_counts"]
        preview_muted_channels = self.get_saved_mute_state_for_path(display_path)

        if display_path == self.current_track_path:
            preview_muted_channels = set(self.player.muted_channels)

        channel_state = tuple(
            (
                note_counts[ch],
                ch in used_channels,
                ch in preview_muted_channels,
            )
            for ch in range(16)
        )

        if channel_state != self._last_channel_state:
            for ch in range(16):
                used = ch in used_channels
                muted = ch in preview_muted_channels
                count = note_counts[ch]

                if muted:
                    bg = self.muted
                    border = self.border
                elif used:
                    bg = self.red
                    border = self.border2
                else:
                    bg = self.red3
                    border = self.border

                self.channel_labels[ch].config(
                    text=f"{ch+1}\n{count}",
                    bg=bg,
                    highlightbackground=border,
                )

            self._last_channel_state = channel_state

        self.root.after(self.ui_refresh_ms, self.update)

    def on_close(self):
        try:
            self.save_current_track_mute_state()
            self.save_settings()
        except Exception as e:
            print("Save on close error:", e)

        self.unregister_hotkeys()

        try:
            self.player.close()
        except Exception as e:
            print("Player close error:", e)

        self.root.destroy()


if __name__ == "__main__":
    enable_high_precision_timer()
    try:
        root = TkinterDnD.Tk()
        app = App(root)
        root.mainloop()
    finally:
        disable_high_precision_timer()