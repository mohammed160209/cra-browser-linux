"""Pytest configuration and mocks for GObject/GTK4/Libadwaita/WebKit when running headlessly."""

import sys
from unittest.mock import MagicMock

# If gi is not installed in the environment, install lightweight mock
try:
    import gi
except ImportError:
    gi_mock = MagicMock()
    gi_mock.require_version = MagicMock()

    repository_mock = MagicMock()

    class MockWidget(MagicMock):
        def __init__(self, *args, **kwargs):
            # Do not pass args/kwargs into MagicMock to avoid spec strings
            super().__init__()
            self._visible = True
            self._classes = set()
            self._children = []
            self._selected_row = None
            self.load_url = MagicMock()
            self.go_back = MagicMock()
            self.go_forward = MagicMock()
            self.reload = MagicMock()
            self.toggle_inspector = MagicMock()
            self.get_uri = MagicMock(return_value="https://duckduckgo.com")
            self.get_title = MagicMock(return_value="DuckDuckGo")
            self.get_zoom_level = MagicMock(return_value=1.0)
            self.set_zoom_level = MagicMock()
            self.get_orientation = MagicMock(return_value=0)
            self.set_orientation = MagicMock()
            self.get_text = MagicMock(return_value="")
            self.set_text = MagicMock()
            self.get_selected = MagicMock(return_value=0)
            self.has_focus = MagicMock(return_value=False)
            self.connect = MagicMock()
            self.set_pixel_size = MagicMock()
            self.set_tooltip_text = MagicMock()
            self.set_hexpand = MagicMock()
            self.set_vexpand = MagicMock()
            self.set_halign = MagicMock()
            self.set_valign = MagicMock()
            self.set_ellipsize = MagicMock()
            self.set_size_request = MagicMock()
            self.set_margin_start = MagicMock()
            self.set_margin_end = MagicMock()
            self.set_margin_top = MagicMock()
            self.set_margin_bottom = MagicMock()
            self.set_child = MagicMock()
            self.set_title = MagicMock()
            self.set_default_size = MagicMock()
            self.set_transient_for = MagicMock()
            self.set_modal = MagicMock()
            self.set_content = MagicMock()
            self.set_sensitive = MagicMock()
            self.present = MagicMock()
            self.close = MagicMock()
            self.add_controller = MagicMock()
            self.load_from_data = MagicMock()

        def _get_child_mock(self, /, **kw):
            return MagicMock(**kw)

        def set_visible(self, val):
            self._visible = bool(val)

        def get_visible(self):
            return self._visible

        def add_css_class(self, cls):
            self._classes.add(cls)

        def remove_css_class(self, cls):
            self._classes.discard(cls)

        def append(self, child):
            self._children.append(child)

        def pack_start(self, child):
            self._children.append(child)

        def pack_end(self, child):
            self._children.append(child)

        def remove(self, child):
            if child in self._children:
                self._children.remove(child)

        def get_first_child(self):
            return self._children[0] if self._children else None

        def get_row_at_index(self, idx):
            if 0 <= idx < len(self._children):
                return self._children[idx]
            return None

        def select_row(self, row):
            self._selected_row = row

        def get_selected_row(self):
            return self._selected_row

        def get_index(self):
            return 0

        def get_root(self):
            return MagicMock()

        @classmethod
        def new_from_icon_name(cls, *args, **kwargs):
            return cls()

        @classmethod
        def new_from_strings(cls, *args, **kwargs):
            return cls()

        @classmethod
        def new(cls, *args, **kwargs):
            return cls()

        @classmethod
        def new_with_settings(cls, *args, **kwargs):
            return cls()

        @classmethod
        def new_with_user_content_manager(cls, *args, **kwargs):
            return cls()

    # Gtk mocks
    gtk_mock = MagicMock()
    gtk_mock.STYLE_PROVIDER_PRIORITY_APPLICATION = 600
    gtk_mock.Orientation.HORIZONTAL = 0
    gtk_mock.Orientation.VERTICAL = 1
    gtk_mock.PolicyType.NEVER = 0
    gtk_mock.PolicyType.AUTOMATIC = 1
    gtk_mock.SelectionMode.NONE = 0
    gtk_mock.SelectionMode.SINGLE = 1
    gtk_mock.Align.START = 0
    gtk_mock.Align.CENTER = 1
    gtk_mock.Align.END = 2

    gtk_mock.Box = MockWidget
    gtk_mock.Button = MockWidget
    gtk_mock.Image = MockWidget
    gtk_mock.Label = MockWidget
    gtk_mock.Entry = MockWidget
    gtk_mock.Paned = MockWidget
    gtk_mock.Overlay = MockWidget
    gtk_mock.FlowBox = MockWidget
    gtk_mock.ListBox = MockWidget
    gtk_mock.ListBoxRow = MockWidget
    gtk_mock.ScrolledWindow = MockWidget
    gtk_mock.ProgressBar = MockWidget
    gtk_mock.DropDown = MockWidget
    gtk_mock.Popover = MockWidget
    gtk_mock.Window = MockWidget
    gtk_mock.StringList = MockWidget
    gtk_mock.GestureClick = MagicMock
    gtk_mock.EventControllerKey = MagicMock
    gtk_mock.CssProvider = MockWidget

    style_context_mock = MagicMock()
    style_context_mock.add_provider_for_display = MagicMock()
    gtk_mock.StyleContext = style_context_mock

    # Gdk keysyms & Display
    gdk_mock = MagicMock()
    display_mock = MagicMock()
    gdk_mock.Display.get_default = MagicMock(return_value=display_mock)

    gdk_mock.KEY_t = ord('t')
    gdk_mock.KEY_T = ord('T')
    gdk_mock.KEY_l = ord('l')
    gdk_mock.KEY_L = ord('L')
    gdk_mock.KEY_w = ord('w')
    gdk_mock.KEY_W = ord('W')
    gdk_mock.KEY_s = ord('s')
    gdk_mock.KEY_S = ord('S')
    gdk_mock.KEY_d = ord('d')
    gdk_mock.KEY_D = ord('D')
    gdk_mock.KEY_k = ord('k')
    gdk_mock.KEY_K = ord('K')
    gdk_mock.KEY_n = ord('n')
    gdk_mock.KEY_N = ord('N')
    gdk_mock.KEY_r = ord('r')
    gdk_mock.KEY_R = ord('R')
    gdk_mock.KEY_F5 = 0xffc2
    gdk_mock.KEY_Escape = 0xff1b
    gdk_mock.KEY_Tab = 0xff09
    gdk_mock.KEY_BackSpace = 0xff08
    gdk_mock.KEY_Left = 0xff51
    gdk_mock.KEY_Right = 0xff53
    gdk_mock.KEY_Up = 0xff52
    gdk_mock.KEY_Down = 0xff54
    gdk_mock.KEY_equal = ord('=')
    gdk_mock.KEY_plus = ord('+')
    gdk_mock.KEY_minus = ord('-')
    gdk_mock.KEY_underscore = ord('_')
    gdk_mock.KEY_comma = ord(',')
    gdk_mock.KEY_1 = ord('1')
    gdk_mock.KEY_9 = ord('9')
    gdk_mock.KEY_i = ord('i')
    gdk_mock.KEY_I = ord('I')

    gdk_mock.ModifierType.CONTROL_MASK = 1 << 2
    gdk_mock.ModifierType.SHIFT_MASK = 1 << 0
    gdk_mock.ModifierType.ALT_MASK = 1 << 3

    # Adw mocks
    adw_mock = MagicMock()
    adw_mock.Application = MagicMock
    adw_mock.ApplicationWindow = MockWidget
    adw_mock.Window = MockWidget
    adw_mock.HeaderBar = MockWidget
    adw_mock.PreferencesWindow = MockWidget
    adw_mock.PreferencesPage = MockWidget
    adw_mock.PreferencesGroup = MockWidget
    adw_mock.ActionRow = MockWidget
    adw_mock.ComboRow = MockWidget
    adw_mock.SwitchRow = MockWidget

    # WebKit mocks
    webkit_mock = MagicMock()
    webkit_mock.WebView = MockWidget
    webkit_mock.Settings = MagicMock
    webkit_mock.UserContentManager = MockWidget
    webkit_mock.UserContentFilterStore = MockWidget
    webkit_mock.HardwareAccelerationPolicy.ALWAYS = 1

    # Gio / GLib mocks
    gio_mock = MagicMock()
    gio_mock.ApplicationFlags.DEFAULT_FLAGS = 0
    gio_mock.ApplicationFlags.HANDLES_OPEN = 1

    glib_mock = MagicMock()
    glib_mock.Bytes = MagicMock
    glib_mock.Error = Exception

    repository_mock.Gtk = gtk_mock
    repository_mock.Gdk = gdk_mock
    repository_mock.Adw = adw_mock
    repository_mock.WebKit = webkit_mock
    repository_mock.Gio = gio_mock
    repository_mock.GLib = glib_mock

    gi_mock.repository = repository_mock

    sys.modules["gi"] = gi_mock
    sys.modules["gi.repository"] = repository_mock
