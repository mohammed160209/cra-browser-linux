#!/usr/bin/env bash
# Quick installer script for Cra Browser on Arch Linux / CachyOS
set -e

echo "==> Installing Cra Browser for Arch Linux / CachyOS..."
sudo python setup.py install --root=/ --optimize=1

echo "==> Updating desktop and icon caches..."
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    sudo gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    sudo update-desktop-database -q /usr/share/applications 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo " Cra Browser installed successfully!"
echo " Launch from your application menu or run: cra-browser"
echo "=========================================================="
