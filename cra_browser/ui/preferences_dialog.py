"""Preferences window for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, Dict, Any
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from ..services.search_engines import SEARCH_ENGINES
from ..model.storage import Storage


ARCHIVE_MAP = [
    ("12 Hours", 12),
    ("24 Hours", 24),
    ("7 Days", 168),
    ("30 Days", 720),
    ("Never", 0),
]


class PreferencesDialog(Adw.PreferencesWindow):
    """Preferences and settings dialog."""

    def __init__(self, settings: Dict[str, Any], on_change: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self.settings = settings
        self.on_change = on_change
        self.set_title("Preferences")
        self.set_default_size(520, 480)

        # 1. General Page
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
        search_row.set_subtitle("Used by Command Bar and address resolution")
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
        archive_row.set_subtitle("Automatically move idle today tabs into archive")
        archive_labels = [opt[0] for opt in ARCHIVE_MAP]
        archive_row.set_model(Gtk.StringList.new(archive_labels))
        current_thresh = settings.get("auto_archive_threshold_hours", 24)
        for idx, (_, val) in enumerate(ARCHIVE_MAP):
            if val == current_thresh:
                archive_row.set_selected(idx)
                break
        archive_row.connect("notify::selected", self._on_archive_changed)
        tabs_group.add(archive_row)

        # 2. Privacy & Security Page
        priv_page = Adw.PreferencesPage()
        priv_page.set_title("Privacy & Performance")
        priv_page.set_icon_name("security-high-symbolic")
        self.add(priv_page)

        priv_group = Adw.PreferencesGroup()
        priv_group.set_title("Content Protection")
        priv_page.add(priv_group)

        adblock_row = Adw.SwitchRow()
        adblock_row.set_title("Built-in Tracker & Ad Blocking")
        adblock_row.set_subtitle("Compile 22,000+ domain blocklist into WebKit Content Filter")
        adblock_row.set_active(settings.get("adblock_enabled", True))
        adblock_row.connect("notify::active", self._on_adblock_changed)
        priv_group.add(adblock_row)

        https_row = Adw.SwitchRow()
        https_row.set_title("HTTPS-Only Mode")
        https_row.set_subtitle("Upgrade insecure HTTP requests automatically")
        https_row.set_active(settings.get("https_only", True))
        https_row.connect("notify::active", self._on_https_changed)
        priv_group.add(https_row)

        # Performance Group
        perf_group = Adw.PreferencesGroup()
        perf_group.set_title("Performance")
        priv_page.add(perf_group)

        hw_row = Adw.SwitchRow()
        hw_row.set_title("Hardware Acceleration")
        hw_row.set_subtitle("Enable GPU composition and DMA-BUF memory buffers")
        hw_row.set_active(settings.get("hardware_acceleration", True))
        hw_row.connect("notify::active", self._on_hw_changed)
        perf_group.add(hw_row)

        # Archive Management Group
        archive_group = Adw.PreferencesGroup()
        archive_group.set_title("Archive Management")
        priv_page.add(archive_group)

        clear_action_row = Adw.ActionRow()
        clear_action_row.set_title("Clear Tab Archive")
        clear_action_row.set_subtitle("Erase all stored archived tabs history")
        clear_btn = Gtk.Button(label="Clear Archive")
        clear_btn.add_css_class("destructive-action")
        clear_btn.set_valign(Gtk.Align.CENTER)
        clear_btn.connect("clicked", lambda *_: self._on_clear_archive(clear_btn))
        clear_action_row.add_suffix(clear_btn)
        archive_group.add(clear_action_row)

    def _on_engine_changed(self, row, _, engines):
        self.settings["search_engine"] = engines[row.get_selected()]
        self.on_change(self.settings)

    def _on_archive_changed(self, row, _):
        selected_idx = row.get_selected()
        if 0 <= selected_idx < len(ARCHIVE_MAP):
            self.settings["auto_archive_threshold_hours"] = ARCHIVE_MAP[selected_idx][1]
            self.on_change(self.settings)

    def _on_adblock_changed(self, row, _):
        self.settings["adblock_enabled"] = row.get_active()
        self.on_change(self.settings)

    def _on_https_changed(self, row, _):
        self.settings["https_only"] = row.get_active()
        self.on_change(self.settings)

    def _on_hw_changed(self, row, _):
        self.settings["hardware_acceleration"] = row.get_active()
        self.on_change(self.settings)

    def _on_clear_archive(self, btn: Gtk.Button):
        Storage.clear_archive()
        btn.set_sensitive(False)
        btn.set_label("Cleared!")
