"""Preferences window for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, Dict, Any
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from ..services.search_engines import SEARCH_ENGINES


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences and settings dialog."""

    def __init__(self, settings: Dict[str, Any], on_change: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self.settings = settings
        self.on_change = on_change
        self.set_title("Preferences")
        self.set_default_size(500, 450)

        # General Page
        gen_page = Adw.PreferencesPage()
        gen_page.set_title("General")
        gen_page.set_icon_name("preferences-system-symbolic")
        self.add(gen_page)

        # Search Engine Group
        search_group = Adw.PreferencesGroup()
        search_group.set_title("Search")
        gen_page.add(search_group)

        search_row = Adw.ComboRow()
        search_row.set_title("Default Search Engine")
        engines = list(SEARCH_ENGINES.keys())
        search_row.set_model(Gtk.StringList.new(engines))
        current_engine = settings.get("search_engine", "DuckDuckGo")
        if current_engine in engines:
            search_row.set_selected(engines.index(current_engine))
        search_row.connect("notify::selected", self._on_engine_changed, engines)
        search_group.add(search_row)

        # Tabs & Auto-archive Group
        tabs_group = Adw.PreferencesGroup()
        tabs_group.set_title("Tabs & Archiving")
        gen_page.add(tabs_group)

        archive_row = Adw.ComboRow()
        archive_row.set_title("Auto-Archive Inactive Today Tabs")
        archive_options = ["12 Hours", "24 Hours", "7 Days", "30 Days", "Never"]
        archive_row.set_model(Gtk.StringList.new(archive_options))
        tabs_group.add(archive_row)

        # Privacy Page
        priv_page = Adw.PreferencesPage()
        priv_page.set_title("Privacy & Security")
        priv_page.set_icon_name("security-high-symbolic")
        self.add(priv_page)

        priv_group = Adw.PreferencesGroup()
        priv_group.set_title("Content Protection")
        priv_page.add(priv_group)

        adblock_row = Adw.SwitchRow()
        adblock_row.set_title("Built-in Tracker & Ad Blocking")
        adblock_row.set_subtitle("Blocks requests to 22,000+ known ad and telemetry domains")
        adblock_row.set_active(settings.get("adblock_enabled", True))
        adblock_row.connect("notify::active", self._on_adblock_changed)
        priv_group.add(adblock_row)

        https_row = Adw.SwitchRow()
        https_row.set_title("HTTPS-Only Mode")
        https_row.set_active(settings.get("https_only", True))
        priv_group.add(https_row)

    def _on_engine_changed(self, row, _, engines):
        self.settings["search_engine"] = engines[row.get_selected()]
        self.on_change(self.settings)

    def _on_adblock_changed(self, row, _):
        self.settings["adblock_enabled"] = row.get_active()
        self.on_change(self.settings)
