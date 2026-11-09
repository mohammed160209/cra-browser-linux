# Cra Browser (Linux Port)

<p align="center">
  <img src="data/app.crabrowser.Cra.svg" alt="Cra Logo" width="128" height="128">
</p>

A native Linux browser with an Arc-style sidebar instead of a tab strip, built with **GTK4**, **Libadwaita**, and **WebKitGTK 6.0**.

Free, open-source, and designed to bring Arc / [Cra](https://github.com/VictorKildahl/cra)'s workflow directly to Arch Linux, CachyOS, and the broader Linux desktop.

---

## Features

| Arc / Cra Feature | Cra Linux |
|---|:---:|
| **Spaces** | ✅ (Custom emoji, title, and theme gradient presets) |
| **Pinned Tabs** | ✅ (Remember home URL, reset when navigated away) |
| **Today Tabs & Auto-Archive** | ✅ (Auto-archive inactive tabs, clear today button) |
| **Favorites Grid** | ✅ (Quick-access icon tiles) |
| **Command Bar (`Ctrl+T` / `Ctrl+L`)** | ✅ (Floating modal overlay for search, tab switching, and actions) |
| **Split View (`Ctrl+Shift+=`)** | ✅ (Side-by-side tab browsing) |
| **Little Window / Little Arc (`Ctrl+Alt+N`)** | ✅ (Floating mini-browser for peeking links) |
| **Built-in Content Blocker** | ✅ (22,000+ domain tracker blocklist) |
| **Native Wayland & Libadwaita** | ✅ (Hardware acceleration, kinetic gestures, dynamic space themes) |

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Ctrl</kbd> + <kbd>T</kbd> / <kbd>Ctrl</kbd> + <kbd>L</kbd> | Open Command Bar (Search, navigate, or switch tab) |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close current tab |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Show or hide the sidebar |
| <kbd>Ctrl</kbd> + <kbd>D</kbd> | Pin or unpin current tab |
| <kbd>Ctrl</kbd> + <kbd>1</kbd>…<kbd>9</kbd> | Switch to Space 1 through 9 |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>=</kbd> | Toggle Split View |
| <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>N</kbd> | New Little Window |
| <kbd>Shift</kbd> + <kbd>Ctrl</kbd> + <kbd>K</kbd> | Clear Today tabs |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> / <kbd>F5</kbd> | Reload page |
| <kbd>Alt</kbd> + <kbd>Left</kbd> / <kbd>Alt</kbd> + <kbd>Right</kbd> | Go Back / Forward |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>I</kbd> | Web Inspector / Developer Tools |

---

## Installation & Running

### Running Directly from Source
```bash
# Ensure dependencies are installed (on CachyOS / Arch Linux):
sudo pacman -S gtk4 libadwaita webkitgtk-6.0 python-gobject

# Launch Cra Browser
./bin/cra-browser
```

### Installing via PKGBUILD (Arch Linux / CachyOS)
```bash
makepkg -si
```

### Cloud / Codespaces
Open this repository in **GitHub Codespaces** or any devcontainer environment; the `.devcontainer` configuration automatically installs dependencies and sets up virtual display forwarding.

---

## License
MIT License. Inspired by [VictorKildahl/cra](https://github.com/VictorKildahl/cra) and Arc.
