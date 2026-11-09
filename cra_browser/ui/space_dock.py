"""Space switcher dock widget for Cra Browser Linux sidebar."""

from __future__ import annotations
from typing import Callable, List
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from ..model.space import Space


class SpaceDock(Gtk.Box):
    """Bottom dock in the sidebar for switching and managing Spaces."""

    def __init__(
        self,
        on_switch_space: Callable[[str], None],
        on_new_space: Callable[[], None],
        on_open_settings: Callable[[], None],
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.on_switch_space = on_switch_space
        self.on_new_space = on_new_space
        self.on_open_settings = on_open_settings

        self.add_css_class("cra-space-dock")

        self.spaces_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.spaces_box.set_hexpand(True)
        self.append(self.spaces_box)

        # "+" button to add space
        self.add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.add_btn.add_css_class("flat")
        self.add_btn.add_css_class("cra-nav-btn")
        self.add_btn.set_tooltip_text("New Space")
        self.add_btn.connect("clicked", lambda *_: self.on_new_space())
        self.append(self.add_btn)

        # Settings button
        self.settings_btn = Gtk.Button.new_from_icon_name("emblem-system-symbolic")
        self.settings_btn.add_css_class("flat")
        self.settings_btn.add_css_class("cra-nav-btn")
        self.settings_btn.set_tooltip_text("Settings")
        self.settings_btn.connect("clicked", lambda *_: self.on_open_settings())
        self.append(self.settings_btn)

    def set_spaces(self, spaces: List[Space], active_space_id: str):
        while True:
            child = self.spaces_box.get_first_child()
            if not child:
                break
            self.spaces_box.remove(child)

        for space in spaces:
            btn = Gtk.Button()
            btn.add_css_class("flat")
            btn.add_css_class("cra-space-pill")
            if space.id == active_space_id:
                btn.add_css_class("active")

            lbl = Gtk.Label(label=f"{space.emoji} {space.title}")
            lbl.set_ellipsize(3)
            btn.set_child(lbl)
            btn.set_tooltip_text(f"Switch to {space.title} (Ctrl+{spaces.index(space)+1})")
            btn.connect("clicked", lambda _, sid=space.id: self.on_switch_space(sid))

            self.spaces_box.append(btn)
