#!/usr/bin/env bash
# Quick installer script for Cra Browser on Arch Linux / CachyOS
set -e

SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
fi

echo "==> Cleaning previous installation..."
$SUDO rm -f /usr/bin/cra-browser
$SUDO rm -rf /usr/lib/python3*/site-packages/cra_browser*
$SUDO rm -rf /usr/lib/cra-browser

echo "==> Setting up dependencies..."
npm install --ignore-scripts=false

# Explicitly ensure Electron engine binary is downloaded in user space before copying
if [ ! -f "node_modules/electron/dist/electron" ]; then
    echo "==> Downloading Electron engine binary..."
    if [ -f "node_modules/electron/install.js" ]; then
        node node_modules/electron/install.js
    fi
fi

echo "==> Compiling Cra Browser UI shell..."
node build.js

echo "==> Installing Cra Browser to /usr/lib/cra-browser..."
$SUDO mkdir -p /usr/lib/cra-browser /usr/bin /usr/share/applications /usr/share/icons/hicolor/scalable/apps /usr/share/metainfo

$SUDO cp -r package.json dist node_modules /usr/lib/cra-browser/
$SUDO chmod -R a+rX /usr/lib/cra-browser/
$SUDO install -Dm755 bin/cra-browser /usr/bin/cra-browser

echo "==> Installing desktop entry and icons..."
if [ -f "data/app.crabrowser.Cra.desktop" ]; then
    $SUDO cp data/app.crabrowser.Cra.desktop /usr/share/applications/
fi
if [ -f "data/app.crabrowser.Cra.metainfo.xml" ]; then
    $SUDO cp data/app.crabrowser.Cra.metainfo.xml /usr/share/metainfo/
fi
if [ -f "data/app.crabrowser.Cra.svg" ]; then
    $SUDO cp data/app.crabrowser.Cra.svg /usr/share/icons/hicolor/scalable/apps/
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    $SUDO gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    $SUDO update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo " Cra Browser (macOS Arc 1:1 Edition) installed successfully!"
echo " Launch from your application menu or run: cra-browser"
echo "=========================================================="
