"""Application entrypoint for Cra Browser Linux."""

from __future__ import annotations
import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio
from .model.storage import Storage
from .ui.window import CraWindow


class CraApplication(Adw.Application):
    """Adw.Application for Cra Browser."""

    def __init__(self):
        super().__init__(
            application_id="app.crabrowser.Cra",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self.window: CraWindow | None = None

    def do_activate(self):
        if not self.window:
            doc = Storage.load_sidebar()
            settings = Storage.load_settings()
            self.window = CraWindow(self, doc, settings)

        self.window.present()


def main():
    app = CraApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
