"""Web content view wrapping WebKitGTK 6.0."""

from __future__ import annotations
import base64
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("WebKit", "6.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gtk, WebKit, GLib


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
        network_session: Optional[WebKit.NetworkSession] = None,
        on_audio_changed: Optional[Callable[[bool], None]] = None,
        saved_session_state: Optional[str] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_title_changed = on_title_changed
        self.on_url_changed = on_url_changed
        self.on_new_tab_requested = on_new_tab_requested
        self.on_nav_state_changed = on_nav_state_changed
        self.on_focus_in = on_focus_in
        self.on_audio_changed = on_audio_changed

        # Progress bar at the top of the web view
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.add_css_class("cra-load-progress")
        self.append(self.progress_bar)

        # Performance & Engine Settings
        settings = WebKit.Settings()
        settings.set_enable_developer_extras(True)
        settings.set_enable_webrtc(True)
        settings.set_enable_smooth_scrolling(True)
        settings.set_javascript_can_open_windows_automatically(True)
        if hasattr(settings, "set_enable_back_forward_navigation_gestures"):
            try:
                settings.set_enable_back_forward_navigation_gestures(True)
            except Exception:
                pass
        settings.set_hardware_acceleration_policy(WebKit.HardwareAccelerationPolicy.ALWAYS)

        # Construct properties via GObject keyword arguments
        webview_kwargs = {}
        if user_content_manager is not None:
            webview_kwargs["user_content_manager"] = user_content_manager
        if network_session is not None:
            webview_kwargs["network_session"] = network_session
        if settings is not None:
            webview_kwargs["settings"] = settings

        try:
            self.web_view = WebKit.WebView(**webview_kwargs)
        except (TypeError, AttributeError):
            if hasattr(WebKit.WebView, "new_with_user_content_manager") and user_content_manager is not None:
                self.web_view = WebKit.WebView.new_with_user_content_manager(user_content_manager)
            elif hasattr(WebKit.WebView, "new_with_settings") and settings is not None:
                self.web_view = WebKit.WebView.new_with_settings(settings)
            elif hasattr(WebKit.WebView, "new"):
                self.web_view = WebKit.WebView.new()
            else:
                self.web_view = WebKit.WebView()

        if settings is not None:
            try:
                self.web_view.set_settings(settings)
            except Exception:
                pass

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

        # Audio playing signal for tab sleep protection & mute indicator
        try:
            self.web_view.connect("notify::is-playing-audio", self._on_audio_notify)
        except Exception:
            pass

        if saved_session_state:
            restored = self.restore_session_state_b64(saved_session_state)
            if not restored and url and url != "about:blank":
                self.load_url(url)
        elif url and url != "about:blank":
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
        try:
            inspector = self.web_view.get_inspector()
            if hasattr(inspector, "is_attached") and inspector.is_attached():
                inspector.close()
            elif hasattr(inspector, "is_open") and inspector.is_open():
                inspector.close()
            else:
                inspector.show()
        except Exception:
            pass

    def zoom_in(self):
        try:
            level = float(self.web_view.get_zoom_level())
            self.web_view.set_zoom_level(min(level + 0.1, 3.0))
        except Exception:
            pass

    def zoom_out(self):
        try:
            level = float(self.web_view.get_zoom_level())
            self.web_view.set_zoom_level(max(level - 0.1, 0.5))
        except Exception:
            pass

    def zoom_reset(self):
        try:
            self.web_view.set_zoom_level(1.0)
        except Exception:
            pass

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

    @property
    def is_playing_audio(self) -> bool:
        if hasattr(self.web_view, "is_playing_audio"):
            try:
                return bool(self.web_view.is_playing_audio())
            except Exception:
                return False
        return False

    @property
    def is_muted(self) -> bool:
        if hasattr(self.web_view, "get_is_muted"):
            try:
                return bool(self.web_view.get_is_muted())
            except Exception:
                return False
        return False

    def set_muted(self, muted: bool):
        if hasattr(self.web_view, "set_is_muted"):
            try:
                self.web_view.set_is_muted(muted)
            except Exception:
                pass

    def get_session_state_b64(self) -> Optional[str]:
        """Serialize WebKit session state into base64 string for persistence and tab sleep."""
        try:
            if hasattr(self.web_view, "get_session_state"):
                state = self.web_view.get_session_state()
                if state and hasattr(state, "serialize"):
                    serialized = state.serialize()
                    if serialized:
                        data = serialized.get_data()
                        return base64.b64encode(data).decode("ascii")
        except Exception as e:
            print(f"[BrowserView] Failed to capture session state: {e}")
        return None

    def restore_session_state_b64(self, b64_str: str) -> bool:
        """Restore WebKit session state from base64 string."""
        if not b64_str:
            return False
        try:
            if hasattr(WebKit, "WebViewSessionState") and hasattr(self.web_view, "restore_session_state"):
                raw = base64.b64decode(b64_str)
                bytes_obj = GLib.Bytes.new(raw)
                state = WebKit.WebViewSessionState.new(bytes_obj)
                self.web_view.restore_session_state(state)
                return True
        except Exception as e:
            print(f"[BrowserView] Failed to restore session state: {e}")
        return False

    def _on_audio_notify(self, *_):
        if self.on_audio_changed:
            self.on_audio_changed(self.is_playing_audio)
