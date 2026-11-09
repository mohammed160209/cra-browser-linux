"""Tests for cra_browser.services.search_engines."""

from cra_browser.services.search_engines import is_url, resolve_input


def test_is_url():
    assert is_url("https://github.com")
    assert is_url("http://archlinux.org/packages")
    assert is_url("cachyos.org")
    assert is_url("wiki.archlinux.org/title/Main_page")
    assert is_url("localhost")
    assert is_url("localhost:3000")
    assert is_url("127.0.0.1:8080")
    assert is_url("about:blank")
    assert is_url("file:///home/user/test.html")

    assert not is_url("arch linux kernel")
    assert not is_url("how to install cachyos")
    assert not is_url("!g rust programming")
    assert not is_url("")


def test_resolve_input_urls():
    assert resolve_input("https://github.com") == "https://github.com"
    assert resolve_input("archlinux.org") == "https://archlinux.org"
    assert resolve_input("localhost:8000") == "http://localhost:8000"
    assert resolve_input("127.0.0.1:3000") == "http://127.0.0.1:3000"
    assert resolve_input("about:blank") == "about:blank"


def test_resolve_input_searches():
    ddg = resolve_input("gtk4 libadwaita", "DuckDuckGo")
    assert ddg == "https://duckduckgo.com/?q=gtk4+libadwaita"

    google = resolve_input("webkitgtk 6.0", "Google")
    assert google == "https://www.google.com/search?q=webkitgtk+6.0"

    brave = resolve_input("arc browser", "Brave")
    assert brave == "https://search.brave.com/search?q=arc+browser"


def test_resolve_input_bangs():
    assert resolve_input("!g python asyncio") == "https://www.google.com/search?q=python+asyncio"
    assert resolve_input("!gh VictorKildahl/cra") == "https://github.com/search?q=VictorKildahl%2Fcra"
    assert resolve_input("!w Linux") == "https://en.wikipedia.org/wiki/Special:Search?search=Linux"
    assert resolve_input("!aw wayland") == "https://wiki.archlinux.org/index.php?search=wayland"
