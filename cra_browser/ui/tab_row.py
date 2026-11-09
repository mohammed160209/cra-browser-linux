"""Tab row widget for Cra Browser Linux sidebar."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.sidebar import SidebarItem


class TabRow(Gtk.Box):
    """Row representing a tab in the sidebar (Pinned or Today)."""

    def __init__(
        self,
        item: SidebarItem,
        is_active: bool,
        is_pinned: bool,
        on_select: Callable[[SidebarItem], None],
        on_close: Callable[[SidebarItem], None],
        on_toggle_pin: Callable[[SidebarItem], None],
        on_reset_home: Optional[Callable[[SidebarItem], None]] = None,
        on_make_home: Optional[Callable[[SidebarItem], None]] = None,
        on_rename: Optional[Callable[[SidebarItem, str], None]] = None,
        on_open_split: Optional[Callable[[SidebarItem], None]] = None,
        on_toggle_mute: Optional[Callable[[SidebarItem], None]] = None,
        indent_level: int = 0,
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.item = item
        self.is_active = is_active
        self.is_pinned = is_pinned
        self.on_select = on_select
        self.on_close = on_close
        self.on_toggle_pin = on_toggle_pin
        self.on_reset_home = on_reset_home
        self.on_make_home = on_make_home
        self.on_rename = on_rename
        self.on_open_split = on_open_split
        self.on_toggle_mute = on_toggle_mute
        self.indent_level = indent_level

        self.add_css_class("cra-tab-row")
        if is_active:
            self.add_css_class("active")
        if item.tab_data and item.tab_data.is_sleeping:
            self.add_css_class("cra-tab-sleeping")

        # Indent if inside a folder
        if indent_level > 0:
            self.set_margin_start(16 * indent_level)

        # Click gesture for selecting the tab
        click = Gtk.GestureClick()
        click.connect("released", self._on_clicked)
        self.add_controller(click)

        # Right-click context menu gesture
        right_click = Gtk.GestureClick()
        right_click.set_button(3)  # Secondary click
        right_click.connect("pressed", self._on_right_click)
        self.add_controller(right_click)

        # Tab favicon / icon
        self.icon = Gtk.Image.new_from_icon_name("text-html-symbolic")
        self.icon.set_pixel_size(16)
        if item.tab_data and item.tab_data.is_sleeping and not is_active:
            self.icon.set_opacity(0.6)
        self.append(self.icon)

        # Title label
        self.label = Gtk.Label(label=item.display_title)
        self.label.set_hexpand(True)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        if item.tab_data and item.tab_data.is_sleeping and not is_active:
            self.label.set_opacity(0.7)
        self.append(self.label)

        # Audio / Mute indicator button (visible when playing audio)
        self.audio_btn: Optional[Gtk.Button] = None
        if item.tab_data and item.tab_data.is_audible:
            audio_icon = "audio-volume-muted-symbolic" if item.tab_data.muted else "audio-volume-high-symbolic"
            self.audio_btn = Gtk.Button.new_from_icon_name(audio_icon)
            self.audio_btn.add_css_class("flat")
            self.audio_btn.add_css_class("cra-nav-btn")
            self.audio_btn.add_css_class("cra-audio-btn")
            self.audio_btn.set_tooltip_text("Unmute Tab" if item.tab_data.muted else "Mute Tab")
            if on_toggle_mute:
                self.audio_btn.connect("clicked", lambda *_: on_toggle_mute(self.item))
            self.append(self.audio_btn)

        # Reset-to-home indicator button (if pinned and navigated away from home)
        self.home_btn: Optional[Gtk.Button] = None
        if self.is_pinned and item.is_away_from_home:
            self.home_btn = Gtk.Button.new_from_icon_name("go-home-symbolic")
            self.home_btn.add_css_class("flat")
            self.home_btn.add_css_class("cra-nav-btn")
            self.home_btn.add_css_class("cra-home-reset-btn")
            saved_url = item.tab_data.saved_url if item.tab_data else ""
            self.home_btn.set_tooltip_text(f"Reset to Home: {saved_url}")
            self.home_btn.connect("clicked", self._on_reset_clicked)
            self.append(self.home_btn)

        # Pin / Unpin button
        pin_icon = "view-pin-symbolic"
        self.pin_btn = Gtk.Button.new_from_icon_name(pin_icon)
        self.pin_btn.add_css_class("flat")
        self.pin_btn.add_css_class("cra-nav-btn")
        self.pin_btn.set_tooltip_text("Unpin Tab (Ctrl+D)" if is_pinned else "Pin Tab (Ctrl+D)")
        self.pin_btn.connect("clicked", lambda *_: self.on_toggle_pin(self.item))
        self.append(self.pin_btn)

        # Close button
        self.close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.close_btn.add_css_class("flat")
        self.close_btn.add_css_class("cra-nav-btn")
        self.close_btn.set_tooltip_text("Close Tab (Ctrl+W)")
        self.close_btn.connect("clicked", lambda *_: self.on_close(self.item))
        self.append(self.close_btn)

    def _on_clicked(self, gesture, n_press, x, y):
        if n_press == 2:
            # Double-click to rename
            self._prompt_rename()
        else:
            self.on_select(self.item)

    def _on_reset_clicked(self, *_):
        if self.on_reset_home:
            self.on_reset_home(self.item)
        else:
            self.item.reset_to_home()
            self.on_select(self.item)

    def _on_right_click(self, gesture, n_press, x, y):
        # Create context popover
        popover = Gtk.Popover()
        popover.set_parent(self)
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)

        # Reset to home (if pinned and away)
        if self.is_pinned and self.item.is_away_from_home and self.on_reset_home:
            btn_reset = Gtk.Button(label="Reset to Home")
            btn_reset.add_css_class("flat")
            btn_reset.connect("clicked", lambda *_: (popover.popdown(), self.on_reset_home(self.item)))
            menu_box.append(btn_reset)

        # Make current URL home (if pinned)
        if self.is_pinned and self.on_make_home:
            btn_make_home = Gtk.Button(label="Make Current URL Home")
            btn_make_home.add_css_class("flat")
            btn_make_home.connect("clicked", lambda *_: (popover.popdown(), self.on_make_home(self.item)))
            menu_box.append(btn_make_home)

        # Rename
        btn_rename = Gtk.Button(label="Rename Tab…")
        btn_rename.add_css_class("flat")
        btn_rename.connect("clicked", lambda *_: (popover.popdown(), self._prompt_rename()))
        menu_box.append(btn_rename)

        # Open in Split View
        if self.on_open_split:
            btn_split = Gtk.Button(label="Open in Split View")
            btn_split.add_css_class("flat")
            btn_split.connect("clicked", lambda *_: (popover.popdown(), self.on_open_split(self.item)))
            menu_box.append(btn_split)

        # Toggle Pin
        pin_label = "Unpin Tab" if self.is_pinned else "Pin Tab"
        btn_pin = Gtk.Button(label=pin_label)
        btn_pin.add_css_class("flat")
        btn_pin.connect("clicked", lambda *_: (popover.popdown(), self.on_toggle_pin(self.item)))
        menu_box.append(btn_pin)

        # Close
        btn_close = Gtk.Button(label="Close Tab")
        btn_close.add_css_class("flat")
        btn_close.add_css_class("destructive-action")
        btn_close.connect("clicked", lambda *_: (popover.popdown(), self.on_close(self.item)))
        menu_box.append(btn_close)

        popover.set_child(menu_box)
        popover.popup()

    def _prompt_rename(self):
        # Open inline or modal rename dialog
        root = self.get_root()
        if not root:
            return

        dialog = Gtk.Window()
        dialog.set_transient_for(root)
        dialog.set_modal(True)
        dialog.set_title("Rename Tab")
        dialog.set_default_size(320, 140)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        entry = Gtk.Entry()
        entry.set_text(self.item.display_title)
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
            new_title = entry.get_text().strip()
            if self.on_rename:
                self.on_rename(self.item, new_title)
            else:
                self.item.rename(new_title)
                self.label.set_text(self.item.display_title)
            dialog.close()

        save_btn.connect("clicked", _do_save)
        entry.connect("activate", _do_save)
        btn_box.append(save_btn)
        box.append(btn_box)

        dialog.set_child(box)
        dialog.present()

    def update_title(self, title: str):
        self.label.set_text(title)
