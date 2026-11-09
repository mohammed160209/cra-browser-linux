"""Collapsible Arc/Cra-style sidebar for Cra Browser Linux."""

from __future__ import annotations
from typing import Callable, List, Optional
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from ..model.sidebar import SidebarDocument, SidebarItem
from ..model.space import Space
from .favorites_grid import FavoritesGrid
from .tab_row import TabRow
from .folder_row import FolderRow
from .space_dock import SpaceDock


class Sidebar(Gtk.Box):
    """Arc/Cra vertical sidebar with Favorites, Pinned tabs, Folders, Today tabs, and Space dock."""

    def __init__(
        self,
        doc: SidebarDocument,
        on_tab_selected: Callable[[SidebarItem], None],
        on_tab_closed: Callable[[SidebarItem], None],
        on_toggle_pin: Callable[[SidebarItem], None],
        on_space_switched: Callable[[str], None],
        on_new_space_requested: Callable[[], None],
        on_open_command_bar: Callable[[], None],
        on_clear_today: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_go_back: Callable[[], None],
        on_go_forward: Callable[[], None],
        on_reload: Callable[[], None],
        on_toggle_sidebar: Callable[[], None],
        on_reset_home: Optional[Callable[[SidebarItem], None]] = None,
        on_make_home: Optional[Callable[[SidebarItem], None]] = None,
        on_rename_item: Optional[Callable[[SidebarItem, str], None]] = None,
        on_new_tab_requested: Optional[Callable[[], None]] = None,
        on_new_folder_requested: Optional[Callable[[Optional[str]], None]] = None,
        on_open_split: Optional[Callable[[SidebarItem], None]] = None,
        on_edit_space: Optional[Callable[[str], None]] = None,
        on_delete_space: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.doc = doc
        self.on_tab_selected = on_tab_selected
        self.on_tab_closed = on_tab_closed
        self.on_toggle_pin = on_toggle_pin
        self.on_space_switched = on_space_switched
        self.on_new_space_requested = on_new_space_requested
        self.on_open_command_bar = on_open_command_bar
        self.on_clear_today = on_clear_today
        self.on_open_settings = on_open_settings
        self.on_go_back = on_go_back
        self.on_go_forward = on_go_forward
        self.on_reload = on_reload
        self.on_toggle_sidebar = on_toggle_sidebar
        self.on_reset_home = on_reset_home
        self.on_make_home = on_make_home
        self.on_rename_item = on_rename_item
        self.on_new_tab_requested = on_new_tab_requested
        self.on_new_folder_requested = on_new_folder_requested
        self.on_open_split = on_open_split
        self.on_edit_space = on_edit_space
        self.on_delete_space = on_delete_space

        self.set_size_request(260, -1)
        self.add_css_class("cra-sidebar")

        # 1. Top Navigation Controls
        self.nav_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.nav_header.set_margin_top(8)
        self.nav_header.set_margin_bottom(6)
        self.nav_header.set_margin_start(8)
        self.nav_header.set_margin_end(8)

        self.back_btn = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_btn.add_css_class("flat")
        self.back_btn.add_css_class("cra-nav-btn")
        self.back_btn.set_tooltip_text("Back (Alt+Left)")
        self.back_btn.connect("clicked", lambda *_: self.on_go_back())
        self.nav_header.append(self.back_btn)

        self.fwd_btn = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.fwd_btn.add_css_class("flat")
        self.fwd_btn.add_css_class("cra-nav-btn")
        self.fwd_btn.set_tooltip_text("Forward (Alt+Right)")
        self.fwd_btn.connect("clicked", lambda *_: self.on_go_forward())
        self.nav_header.append(self.fwd_btn)

        self.reload_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.reload_btn.add_css_class("flat")
        self.reload_btn.add_css_class("cra-nav-btn")
        self.reload_btn.set_tooltip_text("Reload (Ctrl+R / F5)")
        self.reload_btn.connect("clicked", lambda *_: self.on_reload())
        self.nav_header.append(self.reload_btn)

        # URL context pill
        self.url_btn = Gtk.Button()
        self.url_btn.add_css_class("cra-url-pill")
        self.url_btn.set_hexpand(True)
        self.url_label = Gtk.Label(label="Search or enter URL…")
        self.url_label.set_ellipsize(3)
        self.url_btn.set_child(self.url_label)
        self.url_btn.set_tooltip_text("Open Command Bar (Ctrl+T / Ctrl+L)")
        self.url_btn.connect("clicked", lambda *_: self.on_open_command_bar())
        self.nav_header.append(self.url_btn)

        # Hide sidebar button
        self.hide_btn = Gtk.Button.new_from_icon_name("sidebar-show-symbolic")
        self.hide_btn.add_css_class("flat")
        self.hide_btn.add_css_class("cra-nav-btn")
        self.hide_btn.set_tooltip_text("Hide Sidebar (Ctrl+S)")
        self.hide_btn.connect("clicked", lambda *_: self.on_toggle_sidebar())
        self.nav_header.append(self.hide_btn)

        self.append(self.nav_header)

        # 2. Scrolled container for Favorites + Pinned + Today
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_vexpand(True)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.content_box.set_margin_start(8)
        self.content_box.set_margin_end(8)
        self.content_box.set_margin_top(6)
        self.content_box.set_margin_bottom(6)
        self.scroll.set_child(self.content_box)
        self.append(self.scroll)

        # Favorites Grid
        self.favorites_grid = FavoritesGrid(
            on_select=self.on_tab_selected,
            on_remove=lambda item: self.on_tab_closed(item),
            on_open_split=self.on_open_split,
        )
        self.content_box.append(self.favorites_grid)

        # Pinned Header & List
        self.pinned_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        self.pinned_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.pinned_header_box.set_margin_top(4)

        self.pinned_header = Gtk.Label(label="PINNED")
        self.pinned_header.set_halign(Gtk.Align.START)
        self.pinned_header.set_hexpand(True)
        self.pinned_header.add_css_class("subtext")
        self.pinned_header_box.append(self.pinned_header)

        # New Folder button in Pinned section
        if self.on_new_folder_requested:
            folder_btn = Gtk.Button.new_from_icon_name("folder-new-symbolic")
            folder_btn.add_css_class("flat")
            folder_btn.add_css_class("cra-nav-btn")
            folder_btn.set_tooltip_text("New Folder")
            folder_btn.connect("clicked", lambda *_: self.on_new_folder_requested(None))
            self.pinned_header_box.append(folder_btn)

        self.pinned_box.append(self.pinned_header_box)

        self.pinned_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.pinned_box.append(self.pinned_list)
        self.content_box.append(self.pinned_box)

        # Today Header with "+" New Tab and "Clear" button
        self.today_header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.today_header_box.set_margin_top(6)

        today_lbl = Gtk.Label(label="TODAY")
        today_lbl.set_halign(Gtk.Align.START)
        today_lbl.set_hexpand(True)
        today_lbl.add_css_class("subtext")
        self.today_header_box.append(today_lbl)

        # "+" New Tab button in Today section
        if self.on_new_tab_requested:
            new_tab_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
            new_tab_btn.add_css_class("flat")
            new_tab_btn.add_css_class("cra-nav-btn")
            new_tab_btn.set_tooltip_text("New Tab (Ctrl+T)")
            new_tab_btn.connect("clicked", lambda *_: self.on_new_tab_requested())
            self.today_header_box.append(new_tab_btn)

        clear_btn = Gtk.Button(label="Clear")
        clear_btn.add_css_class("flat")
        clear_btn.add_css_class("cra-nav-btn")
        clear_btn.add_css_class("subtext")
        clear_btn.set_tooltip_text("Clear Today Tabs (Shift+Ctrl+K)")
        clear_btn.connect("clicked", lambda *_: self.on_clear_today())
        self.today_header_box.append(clear_btn)

        self.content_box.append(self.today_header_box)

        # Today Tabs List
        self.today_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.content_box.append(self.today_list)

        # 3. Space Dock at bottom
        self.space_dock = SpaceDock(
            on_switch_space=self.on_space_switched,
            on_new_space=self.on_new_space_requested,
            on_open_settings=self.on_open_settings,
            on_edit_space=self.on_edit_space,
            on_delete_space=self.on_delete_space,
        )
        self.append(self.space_dock)

    def update_nav_buttons(self, can_go_back: bool, can_go_forward: bool):
        """Update sensitivity of navigation buttons."""
        self.back_btn.set_sensitive(can_go_back)
        self.fwd_btn.set_sensitive(can_go_forward)

    def update_sidebar(self, active_space: Space, active_tab_id: Optional[str]):
        """Re-render items for the currently active space."""
        # Update URL label
        active_item = self.doc.get_item(active_tab_id) if active_tab_id else None
        if active_item and active_item.tab_data:
            clean_url = active_item.tab_data.url.replace("https://", "").replace("http://", "")
            self.url_label.set_text(clean_url or "about:blank")
        else:
            self.url_label.set_text("Search or enter URL…")

        # 1. Favorites
        favorites = self.doc.get_children(active_space.favorites_container_id)
        self.favorites_grid.set_favorites(favorites, active_tab_id=active_tab_id)
        self.favorites_grid.set_visible(len(favorites) > 0)

        # 2. Pinned & Folders
        while True:
            child = self.pinned_list.get_first_child()
            if not child:
                break
            self.pinned_list.remove(child)

        pinned_items = self.doc.get_children(active_space.pinned_container_id)
        self.pinned_box.set_visible(len(pinned_items) > 0)

        def _render_pinned_item(item: SidebarItem, indent: int = 0):
            if item.item_type == "folder":
                child_count = len(item.children)
                folder_row = FolderRow(
                    folder_item=item,
                    child_count=child_count,
                    on_toggle=self._on_folder_toggled,
                    on_new_tab=lambda f: self.on_new_tab_requested() if self.on_new_tab_requested else None,
                    on_new_subfolder=lambda f: self.on_new_folder_requested(f.id) if self.on_new_folder_requested else None,
                    on_rename=self.on_rename_item,
                    on_delete=lambda f: self.on_tab_closed(f),
                    indent_level=indent,
                )
                self.pinned_list.append(folder_row)

                if item.is_expanded:
                    for child_id in item.children:
                        c_item = self.doc.get_item(child_id)
                        if c_item:
                            _render_pinned_item(c_item, indent + 1)
            else:
                row = TabRow(
                    item=item,
                    is_active=(item.id == active_tab_id),
                    is_pinned=True,
                    on_select=self.on_tab_selected,
                    on_close=self.on_tab_closed,
                    on_toggle_pin=self.on_toggle_pin,
                    on_reset_home=self.on_reset_home,
                    on_make_home=self.on_make_home,
                    on_rename=self.on_rename_item,
                    on_open_split=self.on_open_split,
                    indent_level=indent,
                )
                self.pinned_list.append(row)

        for item in pinned_items:
            _render_pinned_item(item, indent=0)

        # 3. Today Tabs
        while True:
            child = self.today_list.get_first_child()
            if not child:
                break
            self.today_list.remove(child)

        today_items = self.doc.get_children(active_space.today_container_id)
        for item in today_items:
            row = TabRow(
                item=item,
                is_active=(item.id == active_tab_id),
                is_pinned=False,
                on_select=self.on_tab_selected,
                on_close=self.on_tab_closed,
                on_toggle_pin=self.on_toggle_pin,
                on_rename=self.on_rename_item,
                on_open_split=self.on_open_split,
            )
            self.today_list.append(row)

        # 4. Spaces
        self.space_dock.set_spaces(self.doc.spaces, active_space.id)

    def _on_folder_toggled(self, folder_item: SidebarItem):
        self.doc.toggle_folder(folder_item.id)
        active_space = self.doc.get_space(folder_item.space_id) if folder_item.space_id else None
        if active_space:
            self.update_sidebar(active_space, None)
