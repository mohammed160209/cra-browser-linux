"""Favorites grid widget for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, List
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from ..model.sidebar import SidebarItem


class FavoritesGrid(Gtk.Box):
    """Grid displaying favorite items in the sidebar."""

    def __init__(self, on_select: Callable[[SidebarItem], None], on_remove: Callable[[SidebarItem], None]):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.on_select = on_select
        self.on_remove = on_remove

        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_max_children_per_line(4)
        self.flow_box.set_min_children_per_line(2)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_homogeneous(True)
        self.flow_box.set_column_spacing(6)
        self.flow_box.set_row_spacing(6)

        self.append(self.flow_box)

    def set_favorites(self, items: List[SidebarItem]):
        """Populate the grid with favorite items."""
        # Clear existing children
        while True:
            child = self.flow_box.get_first_child()
            if not child:
                break
            self.flow_box.remove(child)

        for item in items:
            btn = Gtk.Button()
            btn.add_css_class("cra-favorite-tile")
            btn.set_tooltip_text(item.display_title)

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_halign(Gtk.Align.CENTER)

            icon = Gtk.Image.new_from_icon_name("web-browser-symbolic")
            icon.set_pixel_size(20)
            box.append(icon)

            lbl = Gtk.Label(label=item.display_title[:10])
            lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            lbl.add_css_class("subtext")
            box.append(lbl)

            btn.set_child(box)
            btn.connect("clicked", lambda _, it=item: self.on_select(it))

            self.flow_box.append(btn)
