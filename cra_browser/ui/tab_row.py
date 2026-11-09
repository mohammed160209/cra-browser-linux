"""Tab row widget for Cra Browser Linux sidebar."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from ..model.sidebar import SidebarItem


class TabRow(Gtk.Box):
    """Row representing a tab in the sidebar."""

    def __init__(
        self,
        item: SidebarItem,
        is_active: bool,
        is_pinned: bool,
        on_select: Callable[[SidebarItem], None],
        on_close: Callable[[SidebarItem], None],
        on_toggle_pin: Callable[[SidebarItem], None],
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.item = item
        self.is_active = is_active
        self.is_pinned = is_pinned
        self.on_select = on_select
        self.on_close = on_close
        self.on_toggle_pin = on_toggle_pin

        self.add_css_class("cra-tab-row")
        if is_active:
            self.add_css_class("active")

        # Click gesture for selecting the tab
        click = Gtk.GestureClick()
        click.connect("released", lambda *_: self.on_select(self.item))
        self.add_controller(click)

        # Tab icon
        self.icon = Gtk.Image.new_from_icon_name("text-html-symbolic")
        self.icon.set_pixel_size(16)
        self.append(self.icon)

        # Title label
        self.label = Gtk.Label(label=item.display_title)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.append(self.label)

        # Pin / Unpin button
        pin_icon_name = "view-pin-symbolic" if is_pinned else "view-pin-symbolic"
        self.pin_btn = Gtk.Button.new_from_icon_name(pin_icon_name)
        self.pin_btn.add_css_class("flat")
        self.pin_btn.add_css_class("cra-nav-btn")
        self.pin_btn.set_tooltip_text("Unpin Tab" if is_pinned else "Pin Tab")
        self.pin_btn.connect("clicked", lambda *_: self.on_toggle_pin(self.item))
        self.append(self.pin_btn)

        # Close button
        self.close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.close_btn.add_css_class("flat")
        self.close_btn.add_css_class("cra-nav-btn")
        self.close_btn.set_tooltip_text("Close Tab")
        self.close_btn.connect("clicked", lambda *_: self.on_close(self.item))
        self.append(self.close_btn)

    def update_title(self, title: str):
        self.label.set_text(title)
