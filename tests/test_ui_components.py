"""Tests verifying UI components and wiring using mock GI environment."""

from cra_browser.model.sidebar import SidebarDocument
from cra_browser.model.storage import Storage
from cra_browser.model.theme import THEME_PRESETS
from cra_browser.ui.window import CraWindow
from cra_browser.ui.sidebar import Sidebar
from cra_browser.ui.browser_view import BrowserView
from cra_browser.ui.split_view import SplitView
from cra_browser.ui.command_bar import CommandBar
from cra_browser.ui.little_window import LittleWindow
from cra_browser.ui.preferences_dialog import PreferencesDialog
from cra_browser.ui.space_editor import SpaceEditorDialog
from cra_browser.ui.theme_styler import ThemeStyler
from unittest.mock import MagicMock


def test_theme_styler():
    styler = ThemeStyler()
    theme = THEME_PRESETS[0][1]
    styler.apply_theme(theme)


def test_command_bar_scopes_and_results():
    nav_mock = MagicMock()
    close_mock = MagicMock()
    tabs_mock = MagicMock(return_value=[
        {"id": "tab-1", "title": "GitHub", "url": "https://github.com", "space": "🌱 Personal"},
        {"id": "tab-2", "title": "ArchWiki", "url": "https://wiki.archlinux.org", "space": "🌱 Personal"},
    ])
    action_mock = MagicMock()

    bar = CommandBar(
        on_navigate=nav_mock,
        on_close=close_mock,
        get_open_tabs=tabs_mock,
        on_action=action_mock,
    )

    bar.show_bar("wiki")
    assert len(bar.results_data) > 0

    # Enter Actions scope
    bar.enter_scope("actions")
    assert bar.active_scope == "actions"
    assert len(bar.results_data) > 0
    assert all(r["type"] == "action" for r in bar.results_data)

    # Enter Tabs scope
    bar.enter_scope("tabs")
    assert bar.active_scope == "tabs"
    assert len(bar.results_data) == 2

    # Exit scope
    bar.exit_scope()
    assert bar.active_scope is None


def test_split_view_interactions():
    p_view = BrowserView(url="https://duckduckgo.com")
    s_view = BrowserView(url="https://cachyos.org")

    focused_views = []
    split = SplitView(
        primary_view=p_view,
        on_active_view_changed=lambda v: focused_views.append(v),
    )

    assert not split.is_split
    assert split.focused_view == p_view

    # Attach secondary
    split.attach_secondary(s_view)
    assert split.is_split
    assert split.secondary_view == s_view
    assert split.focused_view == s_view

    # Toggle orientation
    split.toggle_orientation()

    # Swap panes
    split.swap_panes()
    assert split.primary_view == s_view
    assert split.secondary_view == p_view

    # Detach secondary
    split.detach_secondary()
    assert not split.is_split
    assert split.secondary_view is None


def test_little_window_promotion():
    promoted = []
    win = LittleWindow(
        url="https://wiki.archlinux.org",
        on_promote_to_tab=lambda url, sid: promoted.append((url, sid)),
        available_spaces=[{"id": "s-1", "title": "Personal", "emoji": "🌱"}],
    )
    win.browser_view.web_view.get_uri = MagicMock(return_value="https://wiki.archlinux.org")
    win._on_promote_clicked()
    assert len(promoted) == 1
    assert promoted[0][0] == "https://wiki.archlinux.org"


def test_preferences_dialog_callbacks():
    changed = []
    settings = {
        "search_engine": "DuckDuckGo",
        "adblock_enabled": True,
        "auto_archive_threshold_hours": 24,
        "https_only": True,
        "hardware_acceleration": True,
    }
    dialog = PreferencesDialog(settings, on_change=lambda s: changed.append(dict(s)))
    assert dialog is not None


def test_space_editor_dialog():
    saved = []
    dialog = SpaceEditorDialog(
        parent_window=MagicMock(),
        on_save=lambda t, e, th: saved.append((t, e, th)),
    )
    dialog.title_entry.get_text = MagicMock(return_value="Research")
    dialog.emoji_entry.get_text = MagicMock(return_value="🔬")
    dialog.theme_dropdown.get_selected = MagicMock(return_value=3)
    dialog._on_save_clicked()

    assert len(saved) == 1
    assert saved[0][0] == "Research"
    assert saved[0][1] == "🔬"


def test_cra_window_initialization_and_actions():
    doc = SidebarDocument.fresh()
    settings = Storage.load_settings()
    app = MagicMock()

    window = CraWindow(app=app, doc=doc, settings=settings)
    assert window.active_tab_id is not None
    assert window.sidebar.get_visible()

    # Toggle sidebar
    window.on_toggle_sidebar()
    assert not window.sidebar.get_visible()
    assert window.unhide_btn.get_visible()

    window.on_toggle_sidebar()
    assert window.sidebar.get_visible()
    assert not window.unhide_btn.get_visible()

    # Split view toggle
    window._toggle_split_view()
    assert window.split_view.is_split

    window._toggle_split_view()
    assert not window.split_view.is_split
