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
from ..model.storage import Storage, get_data_dir, get_cache_dir
from ..services.adblock import AdblockService
from ..services.tab_sleep import TabSleepService
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

        # Run auto-archiving for idle Today tabs based on user threshold
        Storage.run_auto_archive(self.doc, self.settings)

        # Persistent WebKit NetworkSession with persistent SQLite cookie storage
        data_dir = get_data_dir()
        cache_dir = get_cache_dir()
        try:
            self.network_session = WebKit.NetworkSession.new(str(data_dir / "profile"), str(cache_dir / "webkit"))
            cookie_mgr = self.network_session.get_cookie_manager()
            if hasattr(WebKit, "CookiePersistentStorage"):
                cookie_mgr.set_persistent_storage(str(data_dir / "cookies.sqlite"), WebKit.CookiePersistentStorage.SQLITE)
        except Exception as e:
            print(f"[CraWindow] NetworkSession initialization fallback: {e}")
            self.network_session = None

        # Content blocker
        self.adblock_service = AdblockService()
        self.user_content_manager = WebKit.UserContentManager()
        if self.settings.get("adblock_enabled", True):
            self.adblock_service.initialize(
                on_ready=lambda: self.adblock_service.attach_to_manager(self.user_content_manager)
            )

        # Tab Sleep / Memory Saver Service
        self.tab_sleep_service = TabSleepService(
            doc=self.doc,
            settings=self.settings,
            get_active_tab_ids=self._get_active_tab_ids,
            get_view=lambda tid: self.views.get(tid),
            discard_view=self._discard_view_for_sleep,
            on_tab_slept=self._on_tab_slept,
        )
        self.tab_sleep_service.start()

        # Dynamic Theme Styler
        self.theme_styler = ThemeStyler()

        # State
        self.active_space_id: str = self.doc.space_order[0] if self.doc.space_order else ""
        self.active_tab_id: Optional[str] = None
        self.views: Dict[str, BrowserView] = {}
        self.current_focused_view: Optional[BrowserView] = None

        # Main Layout: Overlay so CommandBar & Unhide button float on top
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
            on_reset_home=self.on_reset_home,
            on_make_home=self.on_make_home,
            on_rename_item=self.on_rename_item,
            on_new_tab_requested=self.on_new_tab_requested,
            on_new_folder_requested=self.on_new_folder_requested,
            on_open_split=self.on_open_tab_in_split,
            on_toggle_mute=self.on_toggle_mute,
            on_edit_space=self.on_edit_space,
            on_delete_space=self.on_delete_space,
        )
        self.base_box.append(self.sidebar)

        # 2. Web Workspace Container
        self.workspace_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.workspace_box.set_hexpand(True)
        self.workspace_box.set_vexpand(True)
        self.base_box.append(self.workspace_box)

        # Split view placeholder
        self.split_view: Optional[SplitView] = None

        # Floating Unhide Sidebar button (visible when sidebar is hidden)
        self.unhide_btn = Gtk.Button.new_from_icon_name("sidebar-show-symbolic")
        self.unhide_btn.add_css_class("cra-unhide-btn")
        self.unhide_btn.set_tooltip_text("Show Sidebar (Ctrl+S)")
        self.unhide_btn.set_halign(Gtk.Align.START)
        self.unhide_btn.set_valign(Gtk.Align.START)
        self.unhide_btn.set_visible(False)
        self.unhide_btn.connect("clicked", lambda *_: self.on_toggle_sidebar())
        self.overlay.add_overlay(self.unhide_btn)

        # 3. Floating Command Bar Overlay
        self.command_bar = CommandBar(
            on_navigate=self.on_command_navigate,
            on_close=lambda: None,
            get_open_tabs=self._get_all_tabs_summary,
            on_action=self.on_command_action,
            get_search_engine=lambda: self.settings.get("search_engine", "DuckDuckGo"),
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
            # If it's a folder, check folder children
            if pinned_tabs[0].item_type == "folder" and pinned_tabs[0].children:
                target = self.doc.get_item(pinned_tabs[0].children[0])
            else:
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
        saved_state = item.tab_data.session_state if item.tab_data else None

        view = BrowserView(
            url=url,
            on_title_changed=lambda title, it=item: self._on_title_updated(it, title),
            on_url_changed=lambda uri, it=item: self._on_url_updated(it, uri),
            on_new_tab_requested=lambda uri: self._open_new_today_tab(uri),
            on_nav_state_changed=self._on_nav_state_updated,
            user_content_manager=self.user_content_manager,
            network_session=self.network_session,
            on_audio_changed=lambda is_audible, it=item: self._on_audio_changed(it, is_audible),
            saved_session_state=saved_state,
        )
        self.views[item.id] = view
        return view

    def _get_active_tab_ids(self) -> set[str]:
        active = set()
        if self.active_tab_id:
            active.add(self.active_tab_id)
        if self.split_view and self.split_view.is_split and self.split_view.secondary_view:
            for tid, v in self.views.items():
                if v == self.split_view.secondary_view:
                    active.add(tid)
        return active

    def _discard_view_for_sleep(self, tab_id: str):
        if tab_id in self.views:
            view = self.views[tab_id]
            if self.split_view:
                if view in (self.split_view.primary_view, self.split_view.secondary_view):
                    return
            try:
                if hasattr(view.web_view, "terminate_web_process"):
                    view.web_view.terminate_web_process()
            except Exception:
                pass
            del self.views[tab_id]

    def _on_tab_slept(self, item: SidebarItem):
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def _on_audio_changed(self, item: SidebarItem, is_audible: bool):
        if item.tab_data:
            item.tab_data.is_audible = is_audible
            space = self.doc.get_space(self.active_space_id)
            if space:
                self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_toggle_mute(self, item: SidebarItem):
        if item.id in self.views:
            view = self.views[item.id]
            view.set_muted(not view.is_muted)
            if item.tab_data:
                item.tab_data.muted = view.is_muted
            space = self.doc.get_space(self.active_space_id)
            if space:
                self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_tab_selected(self, item: SidebarItem):
        if item.item_type == "folder":
            return

        self.active_tab_id = item.id
        if item.tab_data:
            item.tab_data.touch_active()

        view = self._get_or_create_view(item)
        self.current_focused_view = view

        # Update split view
        if not self.split_view:
            self.split_view = SplitView(
                primary_view=view,
                on_active_view_changed=self._on_split_view_focused,
                on_close_split=self._on_split_closed,
            )
            self.workspace_box.append(self.split_view)
        else:
            self.split_view.set_start_child(view)

        # Refresh sidebar
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

        self._on_nav_state_updated(view.can_go_back, view.can_go_forward)

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

    def on_reset_home(self, item: SidebarItem):
        """Reset a pinned tab to its initial home URL."""
        item.reset_to_home()
        Storage.save_sidebar(self.doc)
        if item.id in self.views and item.tab_data:
            self.views[item.id].load_url(item.tab_data.saved_url)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_make_home(self, item: SidebarItem):
        """Update a pinned tab's home URL to its current URL."""
        item.make_current_page_home()
        Storage.save_sidebar(self.doc)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_rename_item(self, item: SidebarItem, new_title: str):
        """Rename a tab or folder."""
        item.rename(new_title)
        Storage.save_sidebar(self.doc)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_new_tab_requested(self):
        """Open a new empty today tab."""
        self._open_new_today_tab("https://duckduckgo.com")
        self.on_open_command_bar()

    def on_new_folder_requested(self, parent_id: Optional[str] = None):
        """Create a new folder in pinned tabs."""
        self.doc.add_folder(self.active_space_id, title="New Folder", parent_id=parent_id)
        Storage.save_sidebar(self.doc)
        space = self.doc.get_space(self.active_space_id)
        if space:
            self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_open_tab_in_split(self, item: SidebarItem):
        """Open a tab directly in split view."""
        if not self.split_view:
            return
        view = self._get_or_create_view(item)
        self.split_view.attach_secondary(view)

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

    def on_edit_space(self, space_id: str):
        space = self.doc.get_space(space_id)
        if not space:
            return

        def _save_edited(title, emoji, theme):
            space.title = title
            space.emoji = emoji
            space.theme = theme
            Storage.save_sidebar(self.doc)
            if self.active_space_id == space.id:
                self.theme_styler.apply_theme(theme)
            self.sidebar.update_sidebar(space, self.active_tab_id)

        dialog = SpaceEditorDialog(self, on_save=_save_edited, space_to_edit=space)
        dialog.present()

    def on_delete_space(self, space_id: str):
        if self.doc.delete_space(space_id):
            Storage.save_sidebar(self.doc)
            next_space = self.doc.space_order[0]
            self.on_space_switched(next_space)

    def on_open_command_bar(self):
        active_item = self.doc.get_item(self.active_tab_id) if self.active_tab_id else None
        initial_text = active_item.tab_data.url if active_item and active_item.tab_data else ""
        self.command_bar.show_bar(initial_text)

    def on_clear_today(self):
        archived = self.doc.clear_today_tabs(self.active_space_id)
        Storage.archive_tabs(archived, reason="clear")
        Storage.save_sidebar(self.doc)

        # Only reset tab if the active tab was among cleared tabs
        cleared_ids = {item.id for item in archived}
        for it_id in cleared_ids:
            if it_id in self.views:
                del self.views[it_id]

        if self.active_tab_id in cleared_ids:
            self._initialize_initial_tab()
        else:
            space = self.doc.get_space(self.active_space_id)
            if space:
                self.sidebar.update_sidebar(space, self.active_tab_id)

    def on_open_settings(self):
        dialog = PreferencesDialog(self.settings, on_change=lambda s: Storage.save_settings(s))
        dialog.present(self)

    def _get_active_view(self) -> Optional[BrowserView]:
        if self.split_view and self.split_view.is_split:
            return self.split_view.focused_view
        if self.active_tab_id in self.views:
            return self.views[self.active_tab_id]
        return None

    def on_go_back(self):
        view = self._get_active_view()
        if view:
            view.go_back()

    def on_go_forward(self):
        view = self._get_active_view()
        if view:
            view.go_forward()

    def on_reload(self):
        view = self._get_active_view()
        if view:
            view.reload()

    def on_toggle_sidebar(self):
        is_visible = self.sidebar.get_visible()
        self.sidebar.set_visible(not is_visible)
        self.unhide_btn.set_visible(is_visible)

    def on_command_navigate(self, url: str):
        view = self._get_active_view()
        if view:
            view.load_url(url)
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
            spaces_meta = [{"id": s.id, "title": s.title, "emoji": s.emoji} for s in self.doc.spaces]
            win = LittleWindow(
                on_promote_to_tab=self._promote_little_window_tab,
                user_content_manager=self.user_content_manager,
                available_spaces=spaces_meta,
                network_session=self.network_session,
            )
            win.present()
        elif action == "toggle_split":
            self._toggle_split_view()
        elif action == "flip_split":
            if self.split_view:
                self.split_view.toggle_orientation()
        elif action == "clear_today":
            self.on_clear_today()
        elif action == "open_settings":
            self.on_open_settings()
        elif action == "new_space":
            self.on_new_space_requested()
        elif action == "new_folder":
            self.on_new_folder_requested()
        elif action == "pin_tab":
            if self.active_tab_id:
                item = self.doc.get_item(self.active_tab_id)
                if item:
                    self.on_toggle_pin(item)
        elif action == "reset_home":
            if self.active_tab_id:
                item = self.doc.get_item(self.active_tab_id)
                if item:
                    self.on_reset_home(item)
        elif action == "toggle_devtools":
            view = self._get_active_view()
            if view:
                view.toggle_inspector()

    def _open_new_today_tab(self, url: str, space_id: Optional[str] = None):
        target_space = space_id if space_id else self.active_space_id
        item = self.doc.add_tab(target_space, url)
        Storage.save_sidebar(self.doc)
        if target_space != self.active_space_id:
            self.on_space_switched(target_space)
        self.on_tab_selected(item)

    def _promote_little_window_tab(self, url: str, space_id: Optional[str] = None):
        self._open_new_today_tab(url, space_id)
        self.present()

    def _toggle_split_view(self):
        if not self.split_view:
            return
        if self.split_view.is_split:
            self.split_view.detach_secondary()
        else:
            # Create a secondary view with DuckDuckGo
            secondary = BrowserView(
                url="https://duckduckgo.com",
                user_content_manager=self.user_content_manager,
                network_session=self.network_session,
                on_nav_state_changed=self._on_nav_state_updated,
            )
            self.split_view.attach_secondary(secondary)

    def _on_split_view_focused(self, view: BrowserView):
        self.current_focused_view = view
        self._on_nav_state_updated(view.can_go_back, view.can_go_forward)

    def _on_split_closed(self):
        if self.active_tab_id in self.views:
            self.current_focused_view = self.views[self.active_tab_id]
            self._on_nav_state_updated(self.current_focused_view.can_go_back, self.current_focused_view.can_go_forward)

    def _on_nav_state_updated(self, can_back: bool, can_fwd: bool):
        self.sidebar.update_nav_buttons(can_back, can_fwd)

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
            item.tab_data.touch_active()
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
                    elif item.item_type == "folder":
                        for child_id in item.children:
                            c_item = self.doc.get_item(child_id)
                            if c_item and c_item.tab_data:
                                res.append({
                                    "id": c_item.id,
                                    "title": c_item.display_title,
                                    "url": c_item.tab_data.url,
                                    "space": f"{space.emoji} {space.title} / {item.title or 'Folder'}",
                                })
        return res

    def _on_key_pressed(self, controller, keyval, keycode, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)

        # Alt+Left: Go Back
        if alt and not ctrl and keyval == Gdk.KEY_Left:
            self.on_go_back()
            return True

        # Alt+Right: Go Forward
        if alt and not ctrl and keyval == Gdk.KEY_Right:
            self.on_go_forward()
            return True

        # Ctrl+R or F5: Reload
        if (ctrl and not alt and keyval in (Gdk.KEY_r, Gdk.KEY_R)) or keyval == Gdk.KEY_F5:
            self.on_reload()
            return True

        # Ctrl+T or Ctrl+L: Command Bar
        if ctrl and not alt and keyval in (Gdk.KEY_t, Gdk.KEY_T, Gdk.KEY_l, Gdk.KEY_L):
            self.on_open_command_bar()
            return True

        # Ctrl+W: Close current tab or secondary split pane
        if ctrl and not alt and keyval in (Gdk.KEY_w, Gdk.KEY_W):
            if self.split_view and self.split_view.is_split and self.split_view.focused_view == self.split_view.secondary_view:
                self.split_view.detach_secondary()
                return True
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
            spaces_meta = [{"id": s.id, "title": s.title, "emoji": s.emoji} for s in self.doc.spaces]
            win = LittleWindow(
                on_promote_to_tab=self._promote_little_window_tab,
                user_content_manager=self.user_content_manager,
                available_spaces=spaces_meta,
                network_session=self.network_session,
            )
            win.present()
            return True

        # Ctrl+Shift+= / Ctrl+Shift++ : Toggle Split View
        if ctrl and shift and keyval in (Gdk.KEY_equal, Gdk.KEY_plus):
            self._toggle_split_view()
            return True

        # Ctrl+Shift+- : Close Split View pane
        if ctrl and shift and keyval in (Gdk.KEY_minus, Gdk.KEY_underscore):
            if self.split_view and self.split_view.is_split:
                self.split_view.detach_secondary()
            return True

        # Ctrl+, : Open Preferences
        if ctrl and not alt and keyval == Gdk.KEY_comma:
            self.on_open_settings()
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
            view = self._get_active_view()
            if view:
                view.toggle_inspector()
            return True

        return False
