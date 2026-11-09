"""Split view container allowing two web views side-by-side or stacked vertically."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .browser_view import BrowserView


class SplitView(Gtk.Box):
    """Container hosting one or two BrowserViews with split controls and active pane tracking."""

    def __init__(
        self,
        primary_view: BrowserView,
        on_active_view_changed: Optional[Callable[[BrowserView], None]] = None,
        on_close_split: Optional[Callable[[], None]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.primary_view = primary_view
        self.secondary_view: Optional[BrowserView] = None
        self.on_active_view_changed = on_active_view_changed
        self.on_close_split = on_close_split
        self.focused_view: BrowserView = primary_view

        # Wire up focus detection on primary view
        self.primary_view.on_focus_in = lambda v: self.set_focused_view(v)

        # Paned container
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_hexpand(True)
        self.paned.set_vexpand(True)
        self.paned.set_start_child(self.primary_view)
        self.paned.set_resize_start_child(True)
        self.paned.set_shrink_start_child(False)

        # Top split toolbar (visible only when split is active)
        self.split_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.split_bar.add_css_class("cra-split-bar")
        self.split_bar.set_visible(False)
        self.split_bar.set_margin_start(8)
        self.split_bar.set_margin_end(8)
        self.split_bar.set_margin_top(4)
        self.split_bar.set_margin_bottom(4)

        self.split_info_label = Gtk.Label(label="Split View")
        self.split_info_label.set_halign(Gtk.Align.START)
        self.split_info_label.set_hexpand(True)
        self.split_info_label.add_css_class("subtext")
        self.split_bar.append(self.split_info_label)

        # Flip orientation button
        self.flip_btn = Gtk.Button.new_from_icon_name("view-mirror-symbolic")
        self.flip_btn.add_css_class("flat")
        self.flip_btn.add_css_class("cra-nav-btn")
        self.flip_btn.set_tooltip_text("Flip Split Orientation (Horizontal / Vertical)")
        self.flip_btn.connect("clicked", lambda *_: self.toggle_orientation())
        self.split_bar.append(self.flip_btn)

        # Swap panes button
        self.swap_btn = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
        self.swap_btn.add_css_class("flat")
        self.swap_btn.add_css_class("cra-nav-btn")
        self.swap_btn.set_tooltip_text("Swap Panes")
        self.swap_btn.connect("clicked", lambda *_: self.swap_panes())
        self.split_bar.append(self.swap_btn)

        # Close split button
        self.close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.close_btn.add_css_class("flat")
        self.close_btn.add_css_class("cra-nav-btn")
        self.close_btn.set_tooltip_text("Close Split Pane (Ctrl+Shift+-)")
        self.close_btn.connect("clicked", lambda *_: self.detach_secondary())
        self.split_bar.append(self.close_btn)

        self.append(self.split_bar)
        self.append(self.paned)

    def attach_secondary(self, secondary_view: BrowserView):
        """Add a secondary pane for side-by-side or stacked browsing."""
        self.secondary_view = secondary_view
        self.secondary_view.on_focus_in = lambda v: self.set_focused_view(v)

        self.paned.set_end_child(self.secondary_view)
        self.paned.set_resize_end_child(True)
        self.paned.set_shrink_end_child(False)
        self.paned.set_position(540)

        self.split_bar.set_visible(True)
        self.set_focused_view(self.secondary_view)

    def detach_secondary(self):
        """Close the secondary pane and return to single view."""
        if self.secondary_view:
            self.paned.set_end_child(None)
            self.secondary_view = None
            self.split_bar.set_visible(False)
            self.set_focused_view(self.primary_view)
            if self.on_close_split:
                self.on_close_split()

    def set_start_child(self, view: BrowserView):
        self.primary_view = view
        self.primary_view.on_focus_in = lambda v: self.set_focused_view(v)
        self.paned.set_start_child(view)
        if self.focused_view == self.primary_view:
            self.set_focused_view(view)

    def set_focused_view(self, view: BrowserView):
        self.focused_view = view
        if self.primary_view:
            if self.primary_view == view:
                self.primary_view.add_css_class("active-pane")
            else:
                self.primary_view.remove_css_class("active-pane")
        if self.secondary_view:
            if self.secondary_view == view:
                self.secondary_view.add_css_class("active-pane")
            else:
                self.secondary_view.remove_css_class("active-pane")

        if self.is_split:
            pane_name = "Primary" if view == self.primary_view else "Secondary"
            self.split_info_label.set_text(f"Split View • Focused: {pane_name} ({view.current_title or view.current_url})")

        if self.on_active_view_changed:
            self.on_active_view_changed(view)

    def toggle_orientation(self):
        """Toggle between horizontal and vertical split."""
        current = self.paned.get_orientation()
        new_ori = Gtk.Orientation.VERTICAL if current == Gtk.Orientation.HORIZONTAL else Gtk.Orientation.HORIZONTAL
        self.paned.set_orientation(new_ori)

    def swap_panes(self):
        """Swap primary and secondary panes."""
        if not self.is_split or not self.secondary_view:
            return
        p, s = self.primary_view, self.secondary_view
        self.paned.set_start_child(s)
        self.paned.set_end_child(p)
        self.primary_view, self.secondary_view = s, p

    @property
    def is_split(self) -> bool:
        return self.secondary_view is not None
