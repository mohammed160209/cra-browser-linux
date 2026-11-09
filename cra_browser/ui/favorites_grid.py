"""Favorites grid widget for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, List, Optional
from urllib.parse import urlparse
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.sidebar import SidebarItem


def get_site_monogram(item: SidebarItem) -> str:
    """Generate a clean 1-3 letter monogram for a favorite site."""
    if item.title:
        words = item.title.strip().split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        return item.title[:2].upper()
    if item.tab_data and item.tab_data.url:
        netloc = urlparse(item.tab_data.url).netloc.replace("www.", "")
        if netloc:
            parts = netloc.split(".")
            return parts[0][:2].upper()
    return "🌐"


class FavoritesGrid(Gtk.Box):
    """Grid displaying favorite site tiles in the sidebar."""

    def __init__(
        self,
        on_select: Callable[[SidebarItem], None],
        on_remove: Callable[[SidebarItem], None],
        on_open_split: Optional[Callable[[SidebarItem], None]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.on_select = on_select
        self.on_remove = on_remove
        self.on_open_split = on_open_split
        self.active_tab_id: Optional[str] = None

        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_valign(Gtk.Align.START)
        self.flow_box.set_max_children_per_line(4)
        self.flow_box.set_min_children_per_line(2)
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_homogeneous(True)
        self.flow_box.set_column_spacing(6)
        self.flow_box.set_row_spacing(6)

        self.append(self.flow_box)

    def set_favorites(self, items: List[SidebarItem], active_tab_id: Optional[str] = None):
        """Populate the grid with favorite items."""
        self.active_tab_id = active_tab_id
        while True:
            child = self.flow_box.get_first_child()
            if not child:
                break
            self.flow_box.remove(child)

        for item in items:
            btn = Gtk.Button()
            btn.add_css_class("cra-favorite-tile")
            is_active = (item.id == active_tab_id)
            if is_active:
                btn.add_css_class("active-favorite")

            btn.set_tooltip_text(f"{item.display_title}\n{item.tab_data.url if item.tab_data else ''}")

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_halign(Gtk.Align.CENTER)
            box.set_valign(Gtk.Align.CENTER)

            # Monogram / Icon pill
            monogram = get_site_monogram(item)
            icon_lbl = Gtk.Label(label=monogram)
            icon_lbl.add_css_class("cra-favorite-monogram")
            box.append(icon_lbl)

            lbl = Gtk.Label(label=item.display_title[:10])
            lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            lbl.add_css_class("subtext")
            box.append(lbl)

            btn.set_child(box)
            btn.connect("clicked", lambda _, it=item: self.on_select(it))

            # Right click context menu
            right_click = Gtk.GestureClick()
            right_click.set_button(3)
            right_click.connect("pressed", lambda g, n, x, y, it=item, b=btn: self._on_right_click(b, it))
            btn.add_controller(right_click)

            self.flow_box.append(btn)

    def _on_right_click(self, btn: Gtk.Button, item: SidebarItem):
        popover = Gtk.Popover()
        popover.set_parent(btn)
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)

        btn_open = Gtk.Button(label="Open")
        btn_open.add_css_class("flat")
        btn_open.connect("clicked", lambda *_: (popover.popdown(), self.on_select(item)))
        menu_box.append(btn_open)

        if self.on_open_split:
            btn_split = Gtk.Button(label="Open in Split View")
            btn_split.add_css_class("flat")
            btn_split.connect("clicked", lambda *_: (popover.popdown(), self.on_open_split(item)))
            menu_box.append(btn_split)

        btn_remove = Gtk.Button(label="Remove from Favorites")
        btn_remove.add_css_class("flat")
        btn_remove.add_css_class("destructive-action")
        btn_remove.connect("clicked", lambda *_: (popover.popdown(), self.on_remove(item)))
        menu_box.append(btn_remove)

        popover.set_child(menu_box)
        popover.popup()
