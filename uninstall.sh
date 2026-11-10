#!/usr/bin/env bash
# Complete uninstaller script for Cra Browser on Linux
set -e

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

echo "==> Removing system binaries and app files..."
$SUDO rm -f /usr/bin/cra-browser
$SUDO rm -rf /usr/lib/cra-browser
$SUDO rm -rf /usr/lib/python3*/site-packages/cra_browser*
$SUDO rm -rf /usr/lib/python3*/site-packages/cra-browser*
$SUDO rm -rf /usr/share/cra-browser

echo "==> Removing desktop launchers and icons..."
$SUDO rm -f /usr/share/applications/app.crabrowser.Cra.desktop
$SUDO rm -f /usr/share/metainfo/app.crabrowser.Cra.metainfo.xml
$SUDO rm -f /usr/share/icons/hicolor/scalable/apps/app.crabrowser.Cra.svg
$SUDO rm -f /usr/share/glib-2.0/schemas/app.crabrowser.Cra.gschema.xml

# Remove package if installed via pacman
if command -v pacman >/dev/null 2>&1; then
    $SUDO pacman -Rns --noconfirm cra-browser-linux-git 2>/dev/null || true
    $SUDO pacman -Rns --noconfirm cra-browser 2>/dev/null || true
fi

echo "==> Removing user configuration, session, and cache..."
rm -rf "$HOME/.config/cra-browser"
rm -rf "$HOME/.cache/cra-browser"
rm -rf "$HOME/.local/share/cra-browser"

echo "==> Updating desktop databases and icon caches..."
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $SUDO gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    $SUDO update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi
if command -v glib-compile-schemas >/dev/null 2>&1; then
    $SUDO glib-compile-schemas /usr/share/glib-2.0/schemas 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo " Cra Browser has been completely uninstalled from your system."
echo " If you wish to delete the source folder as well, run:"
echo "   rm -rf ~/cra-browser-linux"
echo "=========================================================="
