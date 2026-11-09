"""Main browser window for Cra Browser Linux."""

from __future__ import annotations
from typing import Dict, Optional, List
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import Gtk, Gdk, Adw, WebKit

from ..model.sidebar import SidebarDocument, SidebarItem
from ..model.space import Space
from ..model.storage import Storage
from ..services.adblock import AdblockService
from .theme_styler import ThemeStyler
from .sidebar import Sidebar
from .browser_view import BrowserView
from .split_view import SplitView
from .command_bar import CommandBar
from .little_window import LittleWindow
from .space_editor import SpaceEditorDialog
from .preferences_dialog import PreferencesDialog


class CraWindow(Adw.ApplicationWindow):
    """Primary application window for Cra Browser on Linux."""

    def __init__(self, app: Adw.Application, doc: SidebarDocument, settings: dict):
        super().__init__(application=app)
        self.doc = doc
        self.settings = settings
        self.set_title("Cra Browser")
        self.set_default_size(1280, 840)

        # Content blocker
        self.adblock_service = AdblockService()
        self.user_content_manager = WebKit.UserContentManager()
        if self.settings.get("adblock_enabled", True):
            self.adblock_service.initialize(
                on_ready=lambda: self.adblock_service.attach_to_manager(self.user_content_manager)
            )

        # Dynamic Theme Styler
        self.theme_styler = ThemeStyler()

        # State
        self.active_space_id: str = self.doc.space_order[0] if self.doc.space_order else ""
        self.active_tab_id: Optional[str] = None
        self.views: Dict[str, BrowserView] = {}

        # Main Layout: Overlay so CommandBar floats on top
        self.overlay = Gtk.Overlay()
        self.set_content(self.overlay)

        # Base layout: Sidebar + Web Workspace
        self.base_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.overlay.set_child(self.base_box)

        # 1. Sidebar
        self.sidebar = Sidebar(
            doc=self.doc,
            on_tab_selected=self.on_tab_selected,
            on_tab_closed=self.on_tab_closed,
            on_toggle_pin=self.on_toggle_pin,
            on_space_switched=self.on_space_switched,
            on_new_space_requested=self.on_new_space_requested,
            on_open_command_bar=self.on_open_command_bar,
            on_clear_today=self.on_clear_today,
            on_open_settings=self.on_open_settings,
            on_go_back=self.on_go_back,
            on_go_forward=self.on_go_forward,
            on_reload=self.on_reload,
            on_toggle_sidebar=self.on_toggle_sidebar,
        )
        self.base_box.append(self.sidebar)

        # 2. Web Workspace Container
        self.workspace_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.workspace_box.set_hexpand(True)
        self.workspace_box.set_vexpand(True)
        self.base_box.append(self.workspace_box)

        # Split view placeholder
        self.split_view: Optional[SplitView] = None

        # 3. Floating Command Bar Overlay
        self.command_bar = CommandBar(
            on_navigate=self.on_command_navigate,
            on_close=lambda: None,
            get_open_tabs=self._get_all_tabs_summary,
            on_action=self.on_command_action,
        )
        self.command_bar.set_visible(False)
        self.overlay.add_overlay(self.command_bar)

        # Global Key Event Controller
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_controller)

        # Initialize first tab
        self._initialize_initial_tab()

    def _initialize_initial_tab(self):
        space = self.doc.get_space(self.active_space_id)
        if not space:
            return

        self.theme_styler.apply_theme(space.theme)

        # Pick first available tab in Today, Pinned, or Favorites
        today_tabs = self.doc.get_children(space.today_container_id)
        pinned_tabs = self.doc.get_children(space.pinned_container_id)
        fav_tabs = self.doc.get_children(space.favorites_container_id)

        target = None
        if today_tabs:
            target = today_tabs[0]
        elif pinned_tabs:
            target = pinned_tabs[0]
        elif fav_tabs:
            target = fav_tabs[0]

        if not target:
            target = self.doc.add_tab(space.id, "https://duckduckgo.com", "Search or enter URL…")

        self.on_tab_selected(target)

    def _get_or_create_view(self, item: SidebarItem) -> BrowserView:
        if item.id in self.views:
            return self.views[item.id]

        url = item.tab_data.url if item.tab_data else "about:blank"
        view = BrowserView(
            url=url,
            on_title_changed=lambda title, it=item: self._on_title_updated(it, title),
            on_url_changed=lambda uri, it=item: self._on_url_updated(it, uri),
            on_new_tab_requested=lambda uri: self._open_new_today_tab(uri),
            user_content_manager=self.user_content_manager,
        )
        self.views[item.id] = view
        return view

    def on_tab_selected(self, item: SidebarItem):
        self.active_tab_id = item.id
        view = self._get_or_create_view(item)

        # Update split view
        if not self.split_view:
            self.split_view = SplitView(view)
            self.workspace_box.append(self.split_view)
        else:
            self.split_view.set_start_child(view)

        # Refresh sidebar
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_tab_closed(self, item: SidebarItem):
        self.doc.remove_tab(item.id)
        if item.id in self.views:
            del self.views[item.id]
        Storage.save_sidebar(self.doc)

        if self.active_tab_id == item.id:
            self._initialize_initial_tab()
        else:
            space = self.doc.get_space(self.active_space_id)
            if space:
                self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_toggle_pin(self, item: SidebarItem):
        space = self.doc.get_space(self.active_space_id)
        if not space:
            return
        pinned_container = self.doc.get_item(space.pinned_container_id)
        if pinned_container and item.id in pinned_container.children:
            self.doc.unpin_tab(item.id)
        else:
            self.doc.pin_tab(item.id)

        Storage.save_sidebar(self.doc)
        self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_space_switched(self, space_id: str):
        space = self.doc.get_space(space_id)
        if not space:
            return
        self.active_space_id = space_id
        self.theme_styler.apply_theme(space.theme)
        self._initialize_initial_tab()

    def on_new_space_requested(self):
        def _save_new_space(title, emoji, theme):
            new_space = self.doc.create_space(title, emoji, theme)
            Storage.save_sidebar(self.doc)
            self.on_space_switched(new_space.id)

        dialog = SpaceEditorDialog(self, on_save=_save_new_space)
        dialog.present()

    def on_open_command_bar(self):
        active_item = self.doc.get_item(self.active_tab_id) if self.active_tab_id else None
        initial_text = active_item.tab_data.url if active_item and active_item.tab_data else ""
        self.command_bar.show_bar(initial_text)

    def on_clear_today(self):
        archived = self.doc.clear_today_tabs(self.active_space_id)
        Storage.archive_tabs(archived, reason="clear")
        Storage.save_sidebar(self.doc)
        self._initialize_initial_tab()

    def on_open_settings(self):
        dialog = PreferencesDialog(self.settings, on_change=lambda s: Storage.save_settings(s))
        dialog.present(self)

    def on_go_back(self):
        if self.active_tab_id in self.views:
            self.views[self.active_tab_id].go_back()

    def on_go_forward(self):
        if self.active_tab_id in self.views:
            self.views[self.active_tab_id].go_forward()

    def on_reload(self):
        if self.active_tab_id in self.views:
            self.views[self.active_tab_id].reload()

    def on_toggle_sidebar(self):
        self.sidebar.set_visible(not self.sidebar.get_visible())

    def on_command_navigate(self, url: str):
        if self.active_tab_id and self.active_tab_id in self.views:
            self.views[self.active_tab_id].load_url(url)
        else:
            self._open_new_today_tab(url)

    def on_command_action(self, action: str):
        if action.startswith("switch_tab:"):
            tab_id = action.split(":", 1)[1]
            item = self.doc.get_item(tab_id)
            if item:
                if item.space_id and item.space_id != self.active_space_id:
                    self.on_space_switched(item.space_id)
                self.on_tab_selected(item)
        elif action == "new_little_window":
            win = LittleWindow(on_promote_to_tab=self._open_new_today_tab, user_content_manager=self.user_content_manager)
            win.present()
        elif action == "toggle_split":
            self._toggle_split_view()
        elif action == "clear_today":
            self.on_clear_today()
        elif action == "open_settings":
            self.on_open_settings()

    def _open_new_today_tab(self, url: str):
        item = self.doc.add_tab(self.active_space_id, url)
        Storage.save_sidebar(self.doc)
        self.on_tab_selected(item)

    def _toggle_split_view(self):
        if not self.split_view:
            return
        if self.split_view.is_split:
            self.split_view.detach_secondary()
        else:
            # Create a secondary view with DuckDuckGo
            secondary = BrowserView(url="https://duckduckgo.com", user_content_manager=self.user_content_manager)
            self.split_view.attach_secondary(secondary)

    def _on_title_updated(self, item: SidebarItem, title: str):
        if item.tab_data:
            item.tab_data.note_title(title)
        Storage.save_sidebar(self.doc)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def _on_url_updated(self, item: SidebarItem, uri: str):
        if item.tab_data:
            item.tab_data.url = uri
        Storage.save_sidebar(self.doc)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def _get_all_tabs_summary(self) -> List[dict]:
        res = []
        for space in self.doc.spaces:
            for c_id in (space.today_container_id, space.pinned_container_id, space.favorites_container_id):
                for item in self.doc.get_children(c_id):
                    if item.tab_data:
                        res.append({
                            "id": item.id,
                            "title": item.display_title,
                            "url": item.tab_data.url,
                            "space": f"{space.emoji} {space.title}",
                        })
        return res

    def _on_key_pressed(self, controller, keyval, keycode, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        # Ctrl+T or Ctrl+L: Command Bar
        if ctrl and not alt and keyval in (Gdk.KEY_t, Gdk.KEY_T, Gdk.KEY_l, Gdk.KEY_L):
            self.on_open_command_bar()
            return True

        # Ctrl+W: Close current tab
        if ctrl and not alt and keyval in (Gdk.KEY_w, Gdk.KEY_W):
            if self.active_tab_id:
                item = self.doc.get_item(self.active_tab_id)
                if item:
                    self.on_tab_closed(item)
            return True

        # Ctrl+S: Toggle sidebar
        if ctrl and not alt and keyval in (Gdk.KEY_s, Gdk.KEY_S):
            self.on_toggle_sidebar()
            return True

        # Ctrl+D: Pin/Unpin
        if ctrl and not alt and keyval in (Gdk.KEY_d, Gdk.KEY_D):
            if self.active_tab_id:
                item = self.doc.get_item(self.active_tab_id)
                if item:
                    self.on_toggle_pin(item)
            return True

        # Shift+Ctrl+K: Clear Today
        if ctrl and shift and keyval in (Gdk.KEY_k, Gdk.KEY_K):
            self.on_clear_today()
            return True

        # Ctrl+Alt+N: Little Window
        if ctrl and alt and keyval in (Gdk.KEY_n, Gdk.KEY_N):
            win = LittleWindow(on_promote_to_tab=self._open_new_today_tab, user_content_manager=self.user_content_manager)
            win.present()
            return True

        # Ctrl+Shift+= : Toggle Split View
        if ctrl and shift and keyval in (Gdk.KEY_equal, Gdk.KEY_plus):
            self._toggle_split_view()
            return True

        # Ctrl+1..9: Switch Spaces
        if ctrl and not alt and not shift:
            if Gdk.KEY_1 <= keyval <= Gdk.KEY_9:
                idx = keyval - Gdk.KEY_1
                if idx < len(self.doc.space_order):
                    self.on_space_switched(self.doc.space_order[idx])
                return True

        # Ctrl+Shift+I: DevTools / Inspector
        if ctrl and shift and keyval in (Gdk.KEY_i, Gdk.KEY_I):
            if self.active_tab_id in self.views:
                self.views[self.active_tab_id].toggle_inspector()
            return True

        return False
