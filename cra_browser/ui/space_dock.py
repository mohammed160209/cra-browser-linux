"""Space switcher dock widget for Cra Browser Linux sidebar."""

from __future__ import annotations
from typing import Callable, List, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.space import Space


class SpaceDock(Gtk.Box):
    """Bottom dock in the sidebar for switching, managing, and creating Spaces."""

    def __init__(
        self,
        on_switch_space: Callable[[str], None],
        on_new_space: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_edit_space: Optional[Callable[[str], None]] = None,
        on_delete_space: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.on_switch_space = on_switch_space
        self.on_new_space = on_new_space
        self.on_open_settings = on_open_settings
        self.on_edit_space = on_edit_space
        self.on_delete_space = on_delete_space

        self.add_css_class("cra-space-dock")

        # Scrollable / horizontal box for space pills
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
        self.settings_btn.set_tooltip_text("Preferences (Ctrl+,)")
        self.settings_btn.connect("clicked", lambda *_: self.on_open_settings())
        self.append(self.settings_btn)

    def set_spaces(self, spaces: List[Space], active_space_id: str):
        while True:
            child = self.spaces_box.get_first_child()
            if not child:
                break
            self.spaces_box.remove(child)

        for idx, space in enumerate(spaces):
            btn = Gtk.Button()
            btn.add_css_class("flat")
            btn.add_css_class("cra-space-pill")
            if space.id == active_space_id:
                btn.add_css_class("active")

            lbl = Gtk.Label(label=f"{space.emoji} {space.title}")
            lbl.set_ellipsize(3)
            btn.set_child(lbl)
            shortcut_hint = f" (Ctrl+{idx+1})" if idx < 9 else ""
            btn.set_tooltip_text(f"Switch to {space.title}{shortcut_hint}")
            btn.connect("clicked", lambda _, sid=space.id: self.on_switch_space(sid))

            # Right click context menu on space pill
            right_click = Gtk.GestureClick()
            right_click.set_button(3)
            right_click.connect(
                "pressed",
                lambda g, n, x, y, sid=space.id, b=btn, can_del=(len(spaces) > 1): self._on_space_context(b, sid, can_del)
            )
            btn.add_controller(right_click)

            self.spaces_box.append(btn)

    def _on_space_context(self, btn: Gtk.Button, space_id: str, can_delete: bool):
        popover = Gtk.Popover()
        popover.set_parent(btn)
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)

        if self.on_edit_space:
            btn_edit = Gtk.Button(label="Edit Space…")
            btn_edit.add_css_class("flat")
            btn_edit.connect("clicked", lambda *_: (popover.popdown(), self.on_edit_space(space_id)))
            menu_box.append(btn_edit)

        if can_delete and self.on_delete_space:
            btn_del = Gtk.Button(label="Delete Space")
            btn_del.add_css_class("flat")
            btn_del.add_css_class("destructive-action")
            btn_del.connect("clicked", lambda *_: (popover.popdown(), self.on_delete_space(space_id)))
            menu_box.append(btn_del)

        popover.set_child(menu_box)
        popover.popup()
