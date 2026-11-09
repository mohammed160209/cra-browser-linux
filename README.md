# Cra Browser (Linux Port)

<p align="center">
  <img src="data/app.crabrowser.Cra.svg" alt="Cra Logo" width="128" height="128">
</p>

A native Linux browser with an Arc-style sidebar instead of a tab strip, built with **GTK4**, **Libadwaita**, and **WebKitGTK 6.0**.

Free, open-source, and designed to bring Arc / [Cra](https://github.com/VictorKildahl/cra)'s workflow directly to Arch Linux, CachyOS, and the broader Linux desktop.

---

## Features

| Arc / Cra Feature | Cra Linux | Details |
|---|:---:|---|
| **Spaces** | ✅ | Custom emoji, title, gradient presets (*Ink*, *Phantom*, *Moss*, *Ember*, *Gold*, *Brand*, *Parchment*, *Light Sun*, *Sunset*), and fast switching (`Ctrl+1..9`) |
| **Pinned Tabs & Folders** | ✅ | Persistent tabs per space, remembers home `savedURL`, shows reset-to-home indicator when navigated elsewhere, custom rename, and collapsible nested folders |
| **Today Tabs & Auto-Archive** | ✅ | Idle tab auto-archiving based on thresholds (12h, 24h, 7d, 30d, Never) into `archive.json`, and one-click "Clear Today" (`Shift+Ctrl+K`) |
| **Favorites Grid** | ✅ | Quick-access site tiles with favicons/monograms, right-click context menu, and active site highlight |
| **Command Bar (`Ctrl+T` / `Ctrl+L`)** | ✅ | Centered floating modal overlay with elevation shadow, URL/search detection with bang shortcuts (`!g`, `!ddg`, `!gh`, `!w`, `!aw`), live fuzzy tab switcher across all spaces, and Arc scope navigation (`Tab` enters Actions, `%` enters Tabs) |
| **Split View (`Ctrl+Shift+=`)** | ✅ | Dual-pane split browsing (side-by-side or stacked), draggable divider handle, pane flipping, and independent navigation history |
| **Little Window / Little Arc (`Ctrl+Alt+N`)** | ✅ | Floating popup window with navigation bar and "Open in Space" promotion menu |
| **Built-in Content Blocker** | ✅ | 22,000+ domain tracker blocklist compiled into WebKit's native `WebKit.UserContentFilter` |
| **Native Wayland & Libadwaita** | ✅ | Hardware acceleration, DMA-BUF, contrast-aware dynamic themes, and client-side window controls |

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Ctrl</kbd> + <kbd>T</kbd> / <kbd>Ctrl</kbd> + <kbd>L</kbd> | Open Command Bar (Search, navigate, switch tab, or run action) |
| <kbd>Tab</kbd> *(in empty Command Bar)* | Enter **Actions** scope |
| <kbd>%</kbd> *(in Command Bar)* | Enter **Tabs** search scope |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close current tab (or focused split pane) |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Show or hide the sidebar (floating restore button available) |
| <kbd>Ctrl</kbd> + <kbd>D</kbd> | Pin or unpin current tab |
| <kbd>Ctrl</kbd> + <kbd>1</kbd>…<kbd>9</kbd> | Switch to Space 1 through 9 |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>=</kbd> | Toggle Split View |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>-</kbd> | Close secondary Split View pane |
| <kbd>Ctrl</kbd> + <kbd>Alt</kbd> + <kbd>N</kbd> | New Little Window ("Little Arc") |
| <kbd>Shift</kbd> + <kbd>Ctrl</kbd> + <kbd>K</kbd> | Clear Today tabs into archive |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Open Preferences dialog |
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

### Running Test Suite
```bash
pytest
```

---

## Architecture & Configuration
Configuration and session data follow Arc's schema and are saved in `~/.config/cra-browser/`:
* `sidebar.json`: Spaces, containers (Favorites, Pinned, Today), nested folders, and tabs.
* `settings.json`: Default search engine, ad blocker, auto-archive threshold, HTTPS-only mode, and hardware acceleration.
* `archive.json`: Historical record of auto-archived and manually cleared tabs.

Reference documentation reverse-engineered from Arc and Cra is located in [`docs/arc-reverse-engineering.md`](docs/arc-reverse-engineering.md) and [`docs/arc-parity.md`](docs/arc-parity.md).

---

## License
MIT License. Inspired by [VictorKildahl/cra](https://github.com/VictorKildahl/cra) and Arc.
