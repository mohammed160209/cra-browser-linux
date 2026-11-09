"""Arc-style Command Bar modal overlay for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, List, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..services.search_engines import is_url, resolve_input


def fuzzy_score(query: str, target: str) -> int:
    """Calculate a simple match score for ranking search results."""
    q = query.lower()
    t = target.lower()
    if not q:
        return 0
    if q == t:
        return 100
    if t.startswith(q):
        return 80
    if f"/{q}" in t or f".{q}" in t or f" {q}" in t:
        return 60
    if q in t:
        return 40
    # Check subsequence
    qi = 0
    for char in t:
        if qi < len(q) and char == q[qi]:
            qi += 1
    if qi == len(q):
        return 20
    return 0


class CommandBar(Gtk.Box):
    """Floating Command Bar (Ctrl+T / Ctrl+L) with smart search, open tabs, scopes, and actions."""

    def __init__(
        self,
        on_navigate: Callable[[str], None],
        on_close: Callable[[], None],
        get_open_tabs: Callable[[], List[dict]],
        on_action: Callable[[str], None],
        get_search_engine: Optional[Callable[[], str]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.on_navigate = on_navigate
        self.on_close = on_close
        self.get_open_tabs = get_open_tabs
        self.on_action = on_action
        self.get_search_engine = get_search_engine
        self.active_scope: Optional[str] = None  # None | "actions" | "tabs"

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(80)
        self.set_size_request(620, -1)
        self.add_css_class("cra-command-card")

        # Input Row (contains scope pill + entry)
        self.input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.input_row.add_css_class("cra-command-input-container")

        # Scope indicator pill (e.g. "[Actions]" or "[Tabs]")
        self.scope_pill = Gtk.Button(label="Actions")
        self.scope_pill.add_css_class("cra-scope-pill")
        self.scope_pill.set_visible(False)
        self.scope_pill.connect("clicked", lambda *_: self.exit_scope())
        self.input_row.append(self.scope_pill)

        # Entry field
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search or enter URL…")
        self.entry.set_hexpand(True)
        self.entry.add_css_class("cra-command-entry")
        self.entry.connect("changed", self._on_text_changed)
        self.entry.connect("activate", self._on_activate)

        # Key controller for Escape / Up / Down / Tab / Backspace
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.entry.add_controller(key_controller)
        self.input_row.append(self.entry)

        self.append(self.input_row)

        # Results list box
        self.results_box = Gtk.ListBox()
        self.results_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_box.add_css_class("boxed-list")
        self.results_box.add_css_class("cra-command-results")
        self.results_box.connect("row-activated", self._on_row_activated)
        self.append(self.results_box)

        self.results_data: List[dict] = []

    def show_bar(self, initial_text: str = ""):
        self.set_visible(True)
        self.active_scope = None
        self.scope_pill.set_visible(False)
        self.entry.set_text(initial_text)
        self.entry.grab_focus()
        self._refresh_results(initial_text)

    def hide_bar(self):
        self.set_visible(False)
        self.active_scope = None
        self.scope_pill.set_visible(False)
        self.on_close()

    def enter_scope(self, scope_name: str):
        self.active_scope = scope_name
        self.scope_pill.set_label(scope_name.capitalize())
        self.scope_pill.set_visible(True)
        self.entry.set_text("")
        self._refresh_results("")

    def exit_scope(self):
        self.active_scope = None
        self.scope_pill.set_visible(False)
        self.entry.set_text("")
        self._refresh_results("")

    def _on_text_changed(self, entry):
        text = entry.get_text()
        # If user types "%", enter tabs scope
        if text.startswith("%") and self.active_scope != "tabs":
            self.enter_scope("tabs")
            return
        self._refresh_results(text)

    def _get_engine_name(self) -> str:
        if self.get_search_engine:
            return self.get_search_engine()
        return "DuckDuckGo"

    def _refresh_results(self, text: str):
        # Clear existing
        while True:
            child = self.results_box.get_first_child()
            if not child:
                break
            self.results_box.remove(child)

        self.results_data = []
        clean = text.strip()
        engine = self._get_engine_name()

        all_actions = [
            {"type": "action", "title": "New Little Window", "sub": "Ctrl+Alt+N", "value": "new_little_window", "score": 90},
            {"type": "action", "title": "Toggle Split View", "sub": "Ctrl+Shift+=", "value": "toggle_split", "score": 85},
            {"type": "action", "title": "Flip Split Orientation", "sub": "Horizontal ↔ Vertical", "value": "flip_split", "score": 75},
            {"type": "action", "title": "Clear Today Tabs", "sub": "Shift+Ctrl+K", "value": "clear_today", "score": 80},
            {"type": "action", "title": "New Space", "sub": "Create and style a new space", "value": "new_space", "score": 70},
            {"type": "action", "title": "New Folder", "sub": "Create folder in pinned section", "value": "new_folder", "score": 68},
            {"type": "action", "title": "Pin Current Tab", "sub": "Ctrl+D", "value": "pin_tab", "score": 65},
            {"type": "action", "title": "Reset Tab to Home", "sub": "Return pinned tab to home", "value": "reset_home", "score": 60},
            {"type": "action", "title": "Preferences / Settings", "sub": "Ctrl+,", "value": "open_settings", "score": 50},
            {"type": "action", "title": "Developer Tools", "sub": "Ctrl+Shift+I", "value": "toggle_devtools", "score": 45},
            {"type": "action", "title": "View Archive", "sub": "Open archived tabs", "value": "view_archive", "score": 40},
        ]

        if self.active_scope == "actions":
            # Show only filtered actions
            for act in all_actions:
                score = fuzzy_score(clean, act["title"]) if clean else act.get("score", 50)
                if not clean or score > 0:
                    act_copy = dict(act)
                    act_copy["score"] = score
                    self.results_data.append(act_copy)
            self.results_data.sort(key=lambda x: x["score"], reverse=True)

        elif self.active_scope == "tabs":
            # Show only open tabs across spaces
            for tab in self.get_open_tabs():
                score = max(fuzzy_score(clean, tab["title"]), fuzzy_score(clean, tab["url"]), fuzzy_score(clean, tab["space"]))
                if not clean or score > 0:
                    self.results_data.append({
                        "type": "tab",
                        "title": f"Switch to: {tab['title']}",
                        "sub": f"{tab['space']} • {tab['url']}",
                        "value": tab["id"],
                        "score": score,
                    })
            self.results_data.sort(key=lambda x: x["score"], reverse=True)

        else:
            # Normal command bar search: URL / Search / Tabs / Actions
            if clean:
                if is_url(clean):
                    self.results_data.append({
                        "type": "url",
                        "title": f"Open URL: {clean}",
                        "sub": "Navigate directly",
                        "value": resolve_input(clean, engine),
                        "score": 100,
                    })
                else:
                    self.results_data.append({
                        "type": "search",
                        "title": f"Search for \"{clean}\"",
                        "sub": f"{engine} Search",
                        "value": resolve_input(clean, engine),
                        "score": 95,
                    })

                # Matching open tabs
                for tab in self.get_open_tabs():
                    score = max(fuzzy_score(clean, tab["title"]), fuzzy_score(clean, tab["url"]), fuzzy_score(clean, tab["space"]))
                    if score > 0:
                        self.results_data.append({
                            "type": "tab",
                            "title": f"Switch to: {tab['title']}",
                            "sub": f"{tab['space']} • {tab['url']}",
                            "value": tab["id"],
                            "score": score + 5,
                        })

                # Matching actions
                for act in all_actions:
                    score = fuzzy_score(clean, act["title"])
                    if score > 0:
                        act_copy = dict(act)
                        act_copy["score"] = score
                        self.results_data.append(act_copy)

                self.results_data.sort(key=lambda x: x.get("score", 0), reverse=True)
            else:
                # Default quick suggestions when empty
                self.results_data = all_actions[:5]

        # Render rows (max 7)
        for item in self.results_data[:7]:
            row = Gtk.ListBoxRow()
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row_box.set_margin_top(7)
            row_box.set_margin_bottom(7)
            row_box.set_margin_start(12)
            row_box.set_margin_end(12)

            # Icon
            icon_name = "web-browser-symbolic"
            if item["type"] == "tab":
                icon_name = "tab-new-symbolic"
            elif item["type"] == "action":
                icon_name = "system-run-symbolic"
            elif item["type"] == "search":
                icon_name = "system-search-symbolic"

            icon = Gtk.Image.new_from_icon_name(icon_name)
            icon.set_pixel_size(18)
            row_box.append(icon)

            text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            text_box.set_hexpand(True)

            title_lbl = Gtk.Label(label=item["title"])
            title_lbl.set_halign(Gtk.Align.START)
            title_lbl.set_ellipsize(3)
            text_box.append(title_lbl)

            sub_lbl = Gtk.Label(label=item["sub"])
            sub_lbl.set_halign(Gtk.Align.START)
            sub_lbl.add_css_class("subtext")
            sub_lbl.set_ellipsize(3)
            text_box.append(sub_lbl)

            row_box.append(text_box)

            # Badge for actions / tabs
            if item["type"] == "tab":
                badge = Gtk.Label(label="TAB")
                badge.add_css_class("cra-badge")
                row_box.append(badge)
            elif item["type"] == "action" and "Ctrl" in item["sub"]:
                badge = Gtk.Label(label=item["sub"])
                badge.add_css_class("cra-badge")
                row_box.append(badge)

            row.set_child(row_box)
            self.results_box.append(row)

        first_row = self.results_box.get_row_at_index(0)
        if first_row:
            self.results_box.select_row(first_row)

    def _on_activate(self, *_):
        selected_row = self.results_box.get_selected_row()
        if selected_row:
            idx = selected_row.get_index()
            if 0 <= idx < len(self.results_data):
                self._execute_result(self.results_data[idx])
                return
        text = self.entry.get_text().strip()
        if text:
            self.on_navigate(resolve_input(text, self._get_engine_name()))
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
            if self.active_scope:
                self.exit_scope()
            else:
                self.hide_bar()
            return True
        elif keyval == Gdk.KEY_Tab and not self.entry.get_text().strip() and not self.active_scope:
            # Arc parity: Tab on empty field enters Actions scope!
            self.enter_scope("actions")
            return True
        elif keyval == Gdk.KEY_BackSpace and not self.entry.get_text() and self.active_scope:
            # Backspace on empty query exits scope
            self.exit_scope()
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
