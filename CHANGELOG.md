# Changelog

All notable changes to this project will be documented in this file.

---

## 0.1.0 – Initial Release

First public release of Rust MIDI Player, focused on stability, clean playback, and a reliable foundation for future band sync features.

---

### Core Playback

* Stable real-time MIDI playback engine
* Playback timing anchored to real time (not frame-dependent)
* Playback remains accurate even during Rust GC stutters (critical for future band sync)
* Persistent MIDI connection during normal use
* Soft-close and reconnect system to reduce Rust MIDI detection issues after app restarts
* Built-in panic/reset handling to prevent stuck notes

---

### Controls and Playback Features

* Speed control with accurate real-time default (1.00)
* Playback volume adjustment (velocity scaling)
* Transpose support (real-time pitch shifting)
* Seek bar with smooth playback tracking
* Play, Pause, Reset, Next, and Previous controls
* Auto Play Next Song option

---

### Playlist and Favorites

* Drag and drop MIDI file support
* Playlist system with selection and navigation
* Favorites system with persistent storage
* Add/remove Favorites directly from Playlist
* Playlist clearing option

---

### Channel Control

* Per-channel mute system
* Scanned note counts displayed per channel
* Channel mute used to correct doubled or incorrect MIDI playback
* Favorites store per-song mute configurations
* Playlist-only songs use session-based mute memory

---

### Settings and Customisation

* Default MIDI port selection
* UI Scale setting for full application resizing
* Song Name Font Size setting (default set to 12)
* App Refresh Rate settings:

  * 50 ms (Quality)
  * 125 ms (Normal)
  * 250 ms (Balanced)
  * 500 ms (Performance)
* Optional global shortcuts with rebind support
* Shortcut labels displayed directly on control buttons
* Dedicated **Rust Optimization tab**

---

### Performance and Stability

* Reduced UI update load to minimise interference with Rust performance
* Python garbage collection disabled during playback and restored after stopping
* MIDI event scheduling with lookahead buffering for consistent timing
* Optimised behaviour for lower-end or stressed systems
* Fixed scroll overshoot bug (no more blank gap at top)

---

### User Interface

* Dark Rust-themed UI
* Playback bar integrated into “Now Playing”
* Improved layout and spacing
* Larger, clearer playlist area
* Increased Settings tab readability
* Added **Band button (top center)** with "Coming soon"
* Custom app icon (appicon.ico)
* EXE icon support (exeicon.ico)
* Scrollable interface for smaller screens

---

### User Experience

* Designed for plug-and-play use
* Reduced need to restart Rust during normal use
* Improved stability when switching songs
* Clear playback state and controls
* Better in-app guidance via Settings tabs

---

### Documentation

* Full README with setup and usage guide
* Dedicated troubleshooting guide
* Rust Optimization guidance (GC buffer + -popupwindow)
* Rust console GC commands documented
* Clear explanation of MIDI limitations and compatibility

---

### Rust Integration Notes

* Built specifically for Rust MIDI behaviour
* Handles:

  * MIDI disconnects between songs
  * Port instability
  * Playback inconsistencies
* Playback remains time-accurate during Rust GC stutters
* Supports `-popupwindow` for improved borderless performance

---

### Known Limitations

* Some MIDI files may not sound correct due to Rust instrument mapping
* Channel muting may be required for best results
* Rust may require restart if MIDI input is lost
* Alt-tabbing may cause stutters on some systems (timing remains accurate)
* Windows 10 compatibility not fully tested
* Band sync not yet implemented

---

### Future Plans

* Band and multiplayer sync system
* Drift correction between players
* Advanced MIDI routing
* Per-instrument channel presets
* Expanded playlist features
* Live keyboard input mode
* Full UI overhaul

---
