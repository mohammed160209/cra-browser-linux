"""Tests verifying packaging assets and configuration."""

from pathlib import Path
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).parent.parent


def test_desktop_file():
    desktop_path = REPO_ROOT / "data" / "app.crabrowser.Cra.desktop"
    assert desktop_path.exists()
    content = desktop_path.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in content
    assert "Name=Cra Browser" in content
    assert "Exec=cra-browser %U" in content
    assert "Icon=app.crabrowser.Cra" in content
    assert "Categories=Network;WebBrowser;" in content


def test_metainfo_xml():
    metainfo_path = REPO_ROOT / "data" / "app.crabrowser.Cra.metainfo.xml"
    assert metainfo_path.exists()
    tree = ET.parse(metainfo_path)
    root = tree.getroot()
    assert root.tag == "component"
    id_elem = root.find("id")
    assert id_elem is not None
    assert id_elem.text == "app.crabrowser.Cra"


def test_svg_icon():
    svg_path = REPO_ROOT / "data" / "app.crabrowser.Cra.svg"
    assert svg_path.exists()
    tree = ET.parse(svg_path)
    assert tree.getroot().tag.endswith("svg")


def test_blocklist():
    blocklist_path = REPO_ROOT / "data" / "blocklist" / "domains.txt"
    assert blocklist_path.exists()
    lines = blocklist_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) > 10000


def test_pkgbuild():
    pkgbuild_path = REPO_ROOT / "PKGBUILD"
    assert pkgbuild_path.exists()
    content = pkgbuild_path.read_text(encoding="utf-8")
    assert "pkgname=cra-browser-linux-git" in content
    assert "gtk4" in content
    assert "libadwaita" in content
    assert "webkitgtk-6.0" in content
    assert "python-gobject" in content


def test_bin_executable():
    bin_path = REPO_ROOT / "bin" / "cra-browser"
    assert bin_path.exists()
    content = bin_path.read_text(encoding="utf-8")
    assert "#!/usr/bin/env python3" in content
    assert "main()" in content
