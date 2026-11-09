"""Little Window ('Little Arc') floating browser popup for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, Optional, List
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, Gdk, Adw, WebKit
from .browser_view import BrowserView
from ..services.search_engines import resolve_input


class LittleWindow(Adw.Window):
    """Minimal floating browser window for previewing links (Arc's Little Arc)."""

    def __init__(
        self,
        url: str = "https://duckduckgo.com",
        on_promote_to_tab: Optional[Callable[[str, Optional[str]], None]] = None,
        user_content_manager: Optional[WebKit.UserContentManager] = None,
        available_spaces: Optional[List[dict]] = None,
    ):
        super().__init__()
        self.set_title("Little Cra")
        self.set_default_size(880, 640)
        self.on_promote_to_tab = on_promote_to_tab
        self.available_spaces = available_spaces or []

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Navigation buttons
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        self.back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_btn.add_css_class("flat")
        self.back_btn.connect("clicked", lambda *_: self.browser_view.go_back())
        nav_box.append(self.back_btn)

        self.fwd_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.fwd_btn.add_css_class("flat")
        self.fwd_btn.connect("clicked", lambda *_: self.browser_view.go_forward())
        nav_box.append(self.fwd_btn)

        self.reload_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.reload_btn.add_css_class("flat")
        self.reload_btn.connect("clicked", lambda *_: self.browser_view.reload())
        nav_box.append(self.reload_btn)

        header.pack_start(nav_box)

        # URL Entry in title widget
        self.url_entry = Gtk.Entry()
        self.url_entry.set_text(url)
        self.url_entry.set_size_request(340, -1)
        self.url_entry.connect("activate", self._on_entry_activate)
        header.set_title_widget(self.url_entry)

        # Promote button (Open in Space)
        self.promote_btn = Gtk.Button(label="Open in Space ↗")
        self.promote_btn.add_css_class("suggested-action")
        self.promote_btn.set_tooltip_text("Send this page into your current space")
        self.promote_btn.connect("clicked", self._on_promote_clicked)
        header.pack_end(self.promote_btn)

        # Web view
        self.browser_view = BrowserView(
            url=url,
            on_title_changed=lambda t: self.set_title(t or "Little Cra"),
            on_url_changed=self._on_view_url_changed,
            on_nav_state_changed=self._on_nav_state_changed,
            user_content_manager=user_content_manager,
        )
        main_box.append(self.browser_view)

        # Key controller for Escape to close
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

    def _on_view_url_changed(self, new_url: str):
        if not self.url_entry.has_focus():
            self.url_entry.set_text(new_url)

    def _on_entry_activate(self, entry):
        resolved = resolve_input(entry.get_text().strip())
        self.browser_view.load_url(resolved)

    def _on_nav_state_changed(self, can_back: bool, can_fwd: bool):
        self.back_btn.set_sensitive(can_back)
        self.fwd_btn.set_sensitive(can_fwd)

    def _on_promote_clicked(self, *_):
        current_url = self.browser_view.current_url
        if not current_url:
            return

        if len(self.available_spaces) > 1:
            popover = Gtk.Popover()
            popover.set_parent(self.promote_btn)
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            box.set_margin_top(6)
            box.set_margin_bottom(6)
            box.set_margin_start(6)
            box.set_margin_end(6)

            lbl = Gtk.Label(label="Send to Space:")
            lbl.add_css_class("subtext")
            box.append(lbl)

            for s in self.available_spaces:
                s_btn = Gtk.Button(label=f"{s['emoji']} {s['title']}")
                s_btn.add_css_class("flat")
                s_btn.connect("clicked", lambda _, sid=s["id"]: self._do_promote(current_url, sid, popover))
                box.append(s_btn)

            popover.set_child(box)
            popover.popup()
        else:
            space_id = self.available_spaces[0]["id"] if self.available_spaces else None
            self._do_promote(current_url, space_id)

    def _do_promote(self, url: str, space_id: Optional[str] = None, popover: Optional[Gtk.Popover] = None):
        if popover:
            popover.popdown()
        if self.on_promote_to_tab:
            self.on_promote_to_tab(url, space_id)
        self.close()

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.close()
            return True
        return False
