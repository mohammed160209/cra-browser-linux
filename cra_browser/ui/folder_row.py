"""Folder row widget for collapsible folders in the Cra Browser Linux sidebar."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.sidebar import SidebarItem


class FolderRow(Gtk.Box):
    """Row representing a collapsible folder in the pinned section."""

    def __init__(
        self,
        folder_item: SidebarItem,
        child_count: int,
        on_toggle: Callable[[SidebarItem], None],
        on_new_tab: Optional[Callable[[SidebarItem], None]] = None,
        on_new_subfolder: Optional[Callable[[SidebarItem], None]] = None,
        on_rename: Optional[Callable[[SidebarItem, str], None]] = None,
        on_delete: Optional[Callable[[SidebarItem], None]] = None,
        indent_level: int = 0,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.folder_item = folder_item
        self.child_count = child_count
        self.on_toggle = on_toggle
        self.on_new_tab = on_new_tab
        self.on_new_subfolder = on_new_subfolder
        self.on_rename = on_rename
        self.on_delete = on_delete
        self.indent_level = indent_level

        self.add_css_class("cra-folder-row")

        if indent_level > 0:
            self.set_margin_start(16 * indent_level)

        # Click gesture to toggle expansion
        click = Gtk.GestureClick()
        click.connect("released", self._on_clicked)
        self.add_controller(click)

        # Right-click context menu gesture
        right_click = Gtk.GestureClick()
        right_click.set_button(3)
        right_click.connect("pressed", self._on_right_click)
        self.add_controller(right_click)

        # Chevron icon (pan-down vs pan-end)
        chevron_icon = "pan-down-symbolic" if folder_item.is_expanded else "pan-end-symbolic"
        self.chevron = Gtk.Image.new_from_icon_name(chevron_icon)
        self.chevron.set_pixel_size(12)
        self.chevron.add_css_class("cra-folder-chevron")
        self.append(self.chevron)

        # Folder icon
        folder_icon = "folder-open-symbolic" if folder_item.is_expanded else "folder-symbolic"
        self.folder_icon = Gtk.Image.new_from_icon_name(folder_icon)
        self.folder_icon.set_pixel_size(16)
        self.append(self.folder_icon)

        # Title label
        title_text = folder_item.title or "Folder"
        self.label = Gtk.Label(label=title_text)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_ellipsize(3)
        self.append(self.label)

        # Count badge
        if child_count > 0:
            count_lbl = Gtk.Label(label=str(child_count))
            count_lbl.add_css_class("cra-folder-count")
            count_lbl.add_css_class("subtext")
            self.append(count_lbl)

        # Add tab inside folder button
        if self.on_new_tab:
            add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic")
            add_btn.add_css_class("flat")
            add_btn.add_css_class("cra-nav-btn")
            add_btn.set_tooltip_text("New Tab in Folder")
            add_btn.connect("clicked", lambda *_: self.on_new_tab(self.folder_item))
            self.append(add_btn)

    def _on_clicked(self, gesture, n_press, x, y):
        if n_press == 2:
            self._prompt_rename()
        else:
            self.on_toggle(self.folder_item)

    def _on_right_click(self, gesture, n_press, x, y):
        popover = Gtk.Popover()
        popover.set_parent(self)
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)

        if self.on_new_tab:
            btn_new_tab = Gtk.Button(label="New Tab in Folder")
            btn_new_tab.add_css_class("flat")
            btn_new_tab.connect("clicked", lambda *_: (popover.popdown(), self.on_new_tab(self.folder_item)))
            menu_box.append(btn_new_tab)

        if self.on_new_subfolder:
            btn_sub = Gtk.Button(label="New Nested Folder")
            btn_sub.add_css_class("flat")
            btn_sub.connect("clicked", lambda *_: (popover.popdown(), self.on_new_subfolder(self.folder_item)))
            menu_box.append(btn_sub)

        btn_rename = Gtk.Button(label="Rename Folder…")
        btn_rename.add_css_class("flat")
        btn_rename.connect("clicked", lambda *_: (popover.popdown(), self._prompt_rename()))
        menu_box.append(btn_rename)

        if self.on_delete:
            btn_del = Gtk.Button(label="Delete Folder")
            btn_del.add_css_class("flat")
            btn_del.add_css_class("destructive-action")
            btn_del.connect("clicked", lambda *_: (popover.popdown(), self.on_delete(self.folder_item)))
            menu_box.append(btn_del)

        popover.set_child(menu_box)
        popover.popup()

    def _prompt_rename(self):
        root = self.get_root()
        if not root:
            return

        dialog = Gtk.Window()
        dialog.set_transient_for(root)
        dialog.set_modal(True)
        dialog.set_title("Rename Folder")
        dialog.set_default_size(300, 130)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        entry = Gtk.Entry()
        entry.set_text(self.folder_item.title or "Folder")
        entry.set_hexpand(True)
        box.append(entry)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda *_: dialog.close())
        btn_box.append(cancel_btn)

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")

        def _do_save(*_):
            new_title = entry.get_text().strip() or "Folder"
            if self.on_rename:
                self.on_rename(self.folder_item, new_title)
            else:
                self.folder_item.rename(new_title)
                self.label.set_text(new_title)
            dialog.close()

        save_btn.connect("clicked", _do_save)
        entry.connect("activate", _do_save)
        btn_box.append(save_btn)
        box.append(btn_box)

        dialog.set_child(box)
        dialog.present()
