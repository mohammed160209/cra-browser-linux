# Cra Browser for Linux

This preview uses C++ and Chromium Embedded Framework with CEF Views. It follows the workflow of [Cra on macOS](https://github.com/VictorKildahl/cra) and pins the same CEF version. It uses the stock Linux CEF binary and Alloy-style views to support multiple browsing panes in one window. The macOS application ships a custom Chromium build, so the two engines do not have identical capabilities.

## Install on CachyOS or Arch Linux

Install the x86-64 package with `sudo pacman -U ./cra-browser-cef-0.2.2-2-x86_64.pkg.tar.zst`, then launch **Cra Browser (Chromium Preview)** or run `cra-browser-cef`. The package has a separate desktop entry and stores its data under `$XDG_DATA_HOME/cra-browser-cef` (normally `~/.local/share/cra-browser-cef`).

To build from this branch on Arch, install `base-devel`, `git`, `cmake`, and `ninja`, then run `makepkg -si`. The package recipe verifies the CEF archive against its pinned SHA-256.

For development, extract the pinned CEF archive and run:

```sh
cmake -S . -B build -G Ninja -DCEF_ROOT=/absolute/path/to/extracted/cef \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr
cmake --build build
DESTDIR="$PWD/stage" cmake --install build
./stage/usr/lib/cra-browser-cef/cra-browser
```

## Preview workflows

- Ctrl+T opens the command bar for a new tab. Ctrl+L opens it with the current address selected. Type to search open tabs or the archive, then use Up/Down and Enter to switch or restore. Ctrl+W archives the active tab or closes the focused secondary pane.
- Ctrl+D pins or unpins the active tab. `/home` navigates to the pinned address.
- Use the Space dock to switch or create a Space. A tab’s ··· menu pins it, adds it to the Favorites tiles, moves it to a folder, or opens it in Split View.
- Ctrl+E toggles the second pane. `/split example.org` navigates it. `/little` opens the current URL in a small window.
- Ctrl+Shift+T reopens the last archived tab in its original Space and preserves its pinned or favorite state. Ctrl+Shift+K archives Today tabs in the current Space.
- The sidebar can open an archived tab. Spaces have separate Chromium cookie stores. `/private` opens an ephemeral window. Chromium cookies and Cra's tab list survive restarts.

## Parity status

The first Linux milestone covers the Chromium host, tab and Space state, basic pinned tabs and favorites, an archive, and two browsing panes. Visual polish, profile management, Arc import, extension management, downloads UI, Chromium session-history restore, tab sleep, content blocking and the macOS CEF patches still need implementation and testing. The notes in `docs/` describe Arc and macOS Cra behavior.

For a Chromium smoke test, launch the staged executable with `--cra-smoke-test` and a disposable `XDG_DATA_HOME` under an X11 or Wayland desktop. It loads a local fixture and exits.
