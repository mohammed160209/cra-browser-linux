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
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.window: CraWindow | None = None
        self._initial_url: str | None = None

    def do_activate(self):
        if not self.window:
            doc = Storage.load_sidebar()
            settings = Storage.load_settings()
            self.window = CraWindow(self, doc, settings)
            if self._initial_url:
                self.window._open_new_today_tab(self._initial_url)
                self._initial_url = None

        self.window.present()

    def do_open(self, files, n_files, hint):
        self.do_activate()
        if self.window and files:
            for f in files:
                uri = f.get_uri()
                if uri:
                    self.window._open_new_today_tab(uri)


def main():
    app = CraApplication()
    # Check if a URL was passed via command line
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        app._initial_url = sys.argv[1]
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
