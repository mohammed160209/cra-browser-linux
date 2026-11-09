"""Web content view wrapping WebKitGTK 6.0."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, WebKit


class BrowserView(Gtk.Box):
    """Container holding a single WebKit.WebView with navigation and state handling."""

    def __init__(
        self,
        url: str = "about:blank",
        on_title_changed: Optional[Callable[[str], None]] = None,
        on_url_changed: Optional[Callable[[str], None]] = None,
        on_new_tab_requested: Optional[Callable[[str], None]] = None,
        on_nav_state_changed: Optional[Callable[[bool, bool], None]] = None,
        on_focus_in: Optional[Callable[[BrowserView], None]] = None,
        user_content_manager: Optional[WebKit.UserContentManager] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_title_changed = on_title_changed
        self.on_url_changed = on_url_changed
        self.on_new_tab_requested = on_new_tab_requested
        self.on_nav_state_changed = on_nav_state_changed
        self.on_focus_in = on_focus_in

        # Progress bar at the top of the web view
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.add_css_class("cra-load-progress")
        self.append(self.progress_bar)

        # Settings
        settings = WebKit.Settings()
        settings.set_enable_developer_extras(True)
        settings.set_enable_webrtc(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_javascript_can_open_windows_automatically(True)
        settings.set_hardware_acceleration_policy(WebKit.HardwareAccelerationPolicy.ALWAYS)

        if user_content_manager:
            self.web_view = WebKit.WebView.new_with_user_content_manager(user_content_manager)
            self.web_view.set_settings(settings)
        else:
            self.web_view = WebKit.WebView.new_with_settings(settings)

        self.web_view.set_vexpand(True)
        self.web_view.set_hexpand(True)
        self.append(self.web_view)

        # Click gesture to detect focus in split view
        focus_click = Gtk.GestureClick()
        focus_click.connect("pressed", lambda *_: self._handle_focus())
        self.add_controller(focus_click)

        # Signal connections
        self.web_view.connect("notify::title", self._on_title_notify)
        self.web_view.connect("notify::uri", self._on_uri_notify)
        self.web_view.connect("notify::estimated-load-progress", self._on_progress_notify)
        self.web_view.connect("notify::is-loading", self._on_loading_notify)
        self.web_view.connect("load-changed", self._on_load_changed)
        self.web_view.connect("create", self._on_create_window)

        if url and url != "about:blank":
            self.load_url(url)

    def _handle_focus(self):
        if self.on_focus_in:
            self.on_focus_in(self)

    def load_url(self, url: str):
        if url.startswith("about:"):
            self.web_view.load_uri(url)
        elif not url.startswith("http://") and not url.startswith("https://") and not url.startswith("file://"):
            self.web_view.load_uri(f"https://{url}")
        else:
            self.web_view.load_uri(url)

    def go_back(self):
        if self.web_view.can_go_back():
            self.web_view.go_back()

    def go_forward(self):
        if self.web_view.can_go_forward():
            self.web_view.go_forward()

    def reload(self):
        self.web_view.reload()

    def stop_loading(self):
        self.web_view.stop_loading()

    def toggle_inspector(self):
        inspector = self.web_view.get_inspector()
        if inspector.is_attached():
            inspector.close()
        else:
            inspector.show()

    def zoom_in(self):
        level = self.web_view.get_zoom_level()
        self.web_view.set_zoom_level(min(level + 0.1, 3.0))

    def zoom_out(self):
        level = self.web_view.get_zoom_level()
        self.web_view.set_zoom_level(max(level - 0.1, 0.5))

    def zoom_reset(self):
        self.web_view.set_zoom_level(1.0)

    @property
    def current_url(self) -> str:
        return self.web_view.get_uri() or "about:blank"

    @property
    def current_title(self) -> str:
        return self.web_view.get_title() or ""

    @property
    def can_go_back(self) -> bool:
        return self.web_view.can_go_back()

    @property
    def can_go_forward(self) -> bool:
        return self.web_view.can_go_forward()

    def _on_title_notify(self, *_):
        title = self.current_title
        if self.on_title_changed:
            self.on_title_changed(title)

    def _on_uri_notify(self, *_):
        uri = self.current_url
        if self.on_url_changed:
            self.on_url_changed(uri)
        self._notify_nav_state()

    def _on_progress_notify(self, *_):
        progress = self.web_view.get_estimated_load_progress()
        self.progress_bar.set_fraction(progress)

    def _on_loading_notify(self, *_):
        is_loading = self.web_view.is_loading()
        self.progress_bar.set_visible(is_loading)
        self._notify_nav_state()

    def _on_load_changed(self, web_view, load_event):
        self._notify_nav_state()

    def _notify_nav_state(self):
        if self.on_nav_state_changed:
            self.on_nav_state_changed(self.web_view.can_go_back(), self.web_view.can_go_forward())

    def _on_create_window(self, web_view, navigation_action):
        uri = navigation_action.get_request().get_uri()
        if self.on_new_tab_requested and uri:
            self.on_new_tab_requested(uri)
        return None
