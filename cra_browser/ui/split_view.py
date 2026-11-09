"""Split view container allowing two web views side-by-side."""

from __future__ import annotations
from typing import Optional
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from .browser_view import BrowserView


class SplitView(Gtk.Paned):
    """Container hosting one or two BrowserViews side-by-side."""

    def __init__(self, primary_view: BrowserView):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)
        self.primary_view = primary_view
        self.secondary_view: Optional[BrowserView] = None

        self.set_start_child(self.primary_view)
        self.set_resize_start_child(True)
        self.set_shrink_start_child(False)

    def attach_secondary(self, secondary_view: BrowserView):
        """Add a secondary pane for side-by-side browsing."""
        self.secondary_view = secondary_view
        self.set_end_child(self.secondary_view)
        self.set_resize_end_child(True)
        self.set_shrink_end_child(False)
        self.set_position(500)

    def detach_secondary(self):
        """Close the secondary pane and return to single view."""
        if self.secondary_view:
            self.set_end_child(None)
            self.secondary_view = None

    @property
    def is_split(self) -> bool:
        return self.secondary_view is not None
