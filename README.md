# Cra Browser (Linux 1:1 macOS Edition)

<p align="center">
  <img src="data/app.crabrowser.Cra.svg" alt="Cra Logo" width="128" height="128">
</p>

A pixel-perfect native Linux clone of the macOS **Cra Browser** (open-source Arc browser replacement, [VictorKildahl/cra](https://github.com/VictorKildahl/cra)), engineered with an **HTML5/CSS3/TypeScript UI Shell** and Chromium engine via **Electron** (identical to the Zen Browser UI architecture).

Free, open-source, and designed to bring Arc's exact appearance, glassmorphism, native drag-and-drop mechanics, and multi-pane Settings app directly to Arch Linux, CachyOS, and the broader Linux desktop.

---

## 🌟 Key Parity Features

| macOS Cra Feature | Linux Port | Details |
|---|:---:|---|
| **Spaces & Glassmorphism** | ✅ | Dynamic gradient themes with frosted blur (`backdrop-filter: blur(36px)`), custom emoji, titles, and bottom dock space switcher |
| **Favorites Grid** | ✅ | 2-column quick access tiles with favicons, active indicator outline, and drag-and-drop reordering |
| **Pinned Tabs & Folders** | ✅ | Persistent tabs per space with home `savedURL`, reset-to-home mark (`↺`) when navigated away, and nested collapsible folders |
| **Today Tabs & Auto-Archive** | ✅ | Idle tab auto-archiving based on thresholds (12h, 24h, 7d, 30d) into `archive.json`, and one-click "Clear Today" (`Shift+Ctrl+K`) |
| **Native Drag & Drop** | ✅ | 1:1 implementation of `SidebarListDrop.swift`: live insertion lines, drag to pin, drag into folders, and drag onto tab center for instant split view |
| **Command Bar (`Ctrl+T` / `Ctrl+L`)** | ✅ | Centered floating glassmorphic panel, scope chips (`Tab` for Actions, `%` for Tabs), omnibox search, and live tab switcher |
| **macOS Settings App (`Ctrl+,`)** | ✅ | 1:1 replica of `SettingsWindowController.swift` (778×509px modal) with 204px left nav rail (General, Tabs, Privacy, Shortcuts, Performance, Advanced) and grouped card controls |
| **Dual Split View** | ✅ | Side-by-side or stacked split browsing, divider handle, orientation toggle, and individual audio/navigation tracking |
| **Content Blocker & Sleeping** | ✅ | Built-in 22,500+ domain ad/tracker blocker and memory-pressure tab sleep background service |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| <kbd>Ctrl</kbd> + <kbd>T</kbd> | Open Command Bar (New Tab) |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> | Open Location / Edit URL |
| <kbd>Tab</kbd> *(in Command Bar)* | Toggle **Actions** scope |
| <kbd>Ctrl</kbd> + <kbd>W</kbd> | Close active tab |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Toggle Sidebar collapse / expand |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Open macOS Settings App |
| <kbd>Shift</kbd> + <kbd>Ctrl</kbd> + <kbd>K</kbd> | Clear Today tabs into archive |
| <kbd>Ctrl</kbd> + <kbd>R</kbd> / <kbd>F5</kbd> | Reload current page |
| <kbd>Alt</kbd> + <kbd>Left</kbd> / <kbd>Alt</kbd> + <kbd>Right</kbd> | History Back / Forward |
| <kbd>Ctrl</kbd> + <kbd>+</kbd> / <kbd>-</kbd> / <kbd>0</kbd> | Zoom In / Out / Reset |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>I</kbd> | Developer Tools |

---

## 🚀 Quickstart & Installation (Arch Linux / CachyOS)

### 1. One-Click Quick Installer
```bash
cd ~/cra-browser-linux

# Run the installer (installs dependencies, builds UI shell, and sets up launcher)
./install.sh

# Launch Cra Browser!
cra-browser
```

### 2. Running Directly from Git
```bash
# Build TypeScript and assets
npm install
npm run build

# Start the browser
npm start
```

### 3. Running Automated Tests
```bash
npm test
```

---

## 📂 Configuration & Storage
All settings and sessions match Arc's schema and are stored in `~/.config/cra-browser/`:
* `sidebar.json`: Spaces, containers (Favorites, Pinned, Today), folders, and tabs.
* `settings.json`: Search engine, ad blocker, auto-archive threshold, tab sleep timer, and hardware acceleration.
* `archive.json`: Historical record of auto-archived tabs.

---

## 📜 License
MIT License. Inspired by [VictorKildahl/cra](https://github.com/VictorKildahl/cra) and Arc.
