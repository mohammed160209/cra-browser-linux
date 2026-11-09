"""Arc-style Command Bar modal overlay for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, List
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..services.search_engines import is_url, resolve_input


class CommandBar(Gtk.Box):
    """Floating Command Bar (Ctrl+T / Ctrl+L) with smart search, open tabs, and commands."""

    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_close: Callable[[], None],
        get_open_tabs: Callable[[], List[dict]],
        on_action: Callable[[str], None],
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.on_navigate = on_navigate
        self.on_close = on_close
        self.get_open_tabs = get_open_tabs
        self.on_action = on_action

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(70)
        self.set_size_request(580, -1)
        self.add_css_class("cra-command-card")

        # Entry field
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search or enter URL…")
        self.entry.add_css_class("cra-command-entry")
        self.entry.connect("changed", self._on_text_changed)
        self.entry.connect("activate", self._on_activate)

        # Key controller for Escape / Up / Down
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.entry.add_controller(key_controller)
        self.append(self.entry)

        # Results list box
        self.results_box = Gtk.ListBox()
        self.results_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_box.add_css_class("boxed-list")
        self.results_box.connect("row-activated", self._on_row_activated)
        self.append(self.results_box)

        self.results_data: List[dict] = []

    def show_bar(self, initial_text: str = ""):
        self.set_visible(True)
        self.entry.set_text(initial_text)
        self.entry.grab_focus()
        self._refresh_results(initial_text)

    def hide_bar(self):
        self.set_visible(False)
        self.on_close()

    def _on_text_changed(self, entry):
        self._refresh_results(entry.get_text())

    def _refresh_results(self, text: str):
        # Clear existing
        while True:
            child = self.results_box.get_first_child()
            if not child:
                break
            self.results_box.remove(child)

        self.results_data = []
        clean = text.strip()

        if clean:
            if is_url(clean):
                self.results_data.append({
                    "type": "url",
                    "title": f"Open URL: {clean}",
                    "sub": "Navigate directly",
                    "value": resolve_input(clean),
                })
            else:
                self.results_data.append({
                    "type": "search",
                    "title": f"Search for \"{clean}\"",
                    "sub": "DuckDuckGo Search",
                    "value": resolve_input(clean),
                })

            # Check open tabs
            for tab in self.get_open_tabs():
                if clean.lower() in tab["title"].lower() or clean.lower() in tab["url"].lower():
                    self.results_data.append({
                        "type": "tab",
                        "title": f"Switch to: {tab['title']}",
                        "sub": f"{tab['space']} • {tab['url']}",
                        "value": tab["id"],
                    })
        else:
            # Common shortcuts when empty
            self.results_data.extend([
                {"type": "action", "title": "New Little Window", "sub": "Ctrl+Alt+N", "value": "new_little_window"},
                {"type": "action", "title": "Toggle Split View", "sub": "Ctrl+Shift+=", "value": "toggle_split"},
                {"type": "action", "title": "Clear Today Tabs", "sub": "Shift+Ctrl+K", "value": "clear_today"},
                {"type": "action", "title": "Settings", "sub": "Preferences", "value": "open_settings"},
            ])

        for item in self.results_data[:6]:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(10)
            box.set_margin_end(10)

            title_lbl = Gtk.Label(label=item["title"])
            title_lbl.set_halign(Gtk.Align.START)
            title_lbl.set_ellipsize(3)
            box.append(title_lbl)

            sub_lbl = Gtk.Label(label=item["sub"])
            sub_lbl.set_halign(Gtk.Align.START)
            sub_lbl.add_css_class("subtext")
            box.append(sub_lbl)

            row.set_child(box)
            self.results_box.append(row)

        first_row = self.results_box.get_row_at_index(0)
        if first_row:
            self.results_box.select_row(first_row)

    def _on_activate(self, *_):
        selected_row = self.results_box.get_selected_row()
        if selected_row:
            idx = selected_row.get_index()
            self._execute_result(self.results_data[idx])
        elif self.entry.get_text().strip():
            self.on_navigate(resolve_input(self.entry.get_text().strip()))
            self.hide_bar()

    def _on_row_activated(self, list_box, row):
        idx = row.get_index()
        if 0 <= idx < len(self.results_data):
            self._execute_result(self.results_data[idx])

    def _execute_result(self, item: dict):
        if item["type"] in ("url", "search"):
            self.on_navigate(item["value"])
        elif item["type"] == "tab":
            self.on_action(f"switch_tab:{item['value']}")
        elif item["type"] == "action":
            self.on_action(item["value"])
        self.hide_bar()

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.hide_bar()
            return True
        elif keyval == Gdk.KEY_Down:
            current = self.results_box.get_selected_row()
            idx = current.get_index() if current else -1
            next_row = self.results_box.get_row_at_index(idx + 1)
            if next_row:
                self.results_box.select_row(next_row)
            return True
        elif keyval == Gdk.KEY_Up:
            current = self.results_box.get_selected_row()
            idx = current.get_index() if current else 1
            prev_row = self.results_box.get_row_at_index(max(0, idx - 1))
            if prev_row:
                self.results_box.select_row(prev_row)
            return True
        return False
