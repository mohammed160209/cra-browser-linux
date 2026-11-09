"""Little Window ('Little Arc') floating browser popup for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, Adw, WebKit
from .browser_view import BrowserView


class LittleWindow(Adw.Window):
    """Minimal floating browser window for previewing links (Arc's Little Arc)."""

    def __init__(
        self,
        url: str = "https://duckduckgo.com",
        on_promote_to_tab: Optional[Callable[[str], None]] = None,
        user_content_manager: Optional[WebKit.UserContentManager] = None,
    ):
        super().__init__()
        self.set_title("Little Cra")
        self.set_default_size(860, 640)
        self.on_promote_to_tab = on_promote_to_tab

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        # Promote button
        promote_btn = Gtk.Button(label="Open in Space")
        promote_btn.add_css_class("flat")
        promote_btn.set_tooltip_text("Send this page into your current space")
        promote_btn.connect("clicked", self._on_promote)
        header.pack_start(promote_btn)

        # Web view
        self.browser_view = BrowserView(
            url=url,
            on_title_changed=lambda t: self.set_title(t or "Little Cra"),
            user_content_manager=user_content_manager,
        )
        main_box.append(self.browser_view)

    def _on_promote(self, *_):
        current_url = self.browser_view.current_url
        if self.on_promote_to_tab and current_url:
            self.on_promote_to_tab(current_url)
            self.close()
