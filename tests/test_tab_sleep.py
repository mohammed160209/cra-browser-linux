"""Unit tests for TabSleepService and memory saver policies."""

import time
from unittest.mock import MagicMock
from cra_browser.model.sidebar import SidebarDocument, TabData
from cra_browser.services.tab_sleep import TabSleepService


def test_tab_sleep_protects_active_and_audible_tabs():
    doc = SidebarDocument.fresh()
    space = doc.spaces[0]

    # Create 3 tabs
    t1 = doc.add_tab(space.id, "https://active.com", "Active")
    t2 = doc.add_tab(space.id, "https://audio.com", "Playing Music")
    t3 = doc.add_tab(space.id, "https://idle.com", "Idle Tab")

    # Set idle tab active time in past (2 hours ago)
    t1.tab_data.time_last_active = time.time()
    t2.tab_data.time_last_active = time.time() - 7200
    t3.tab_data.time_last_active = time.time() - 7200

    discarded = []

    # Mock views
    view1 = MagicMock()
    view1.is_playing_audio = False

    view2 = MagicMock()
    view2.is_playing_audio = True  # Audible: must NOT sleep

    view3 = MagicMock()
    view3.is_playing_audio = False
    view3.get_session_state_b64.return_value = "b64state_idle=="

    views = {t1.id: view1, t2.id: view2, t3.id: view3}

    # Set protected recent tabs to 1 so t3 can be discarded
    TabSleepService.PROTECTED_RECENT_TABS = 1

    svc = TabSleepService(
        doc=doc,
        settings={"tab_sleep_enabled": True, "tab_sleep_threshold_minutes": 60},
        get_active_tab_ids=lambda: {t1.id},
        get_view=lambda tid: views.get(tid),
        discard_view=lambda tid: discarded.append(tid),
    )

    slept = svc.sweep()
    assert slept == 1
    assert t3.id in discarded
    assert t1.id not in discarded  # active
    assert t2.id not in discarded  # audible
    assert t3.tab_data.is_sleeping
    assert t3.tab_data.session_state == "b64state_idle=="


def test_tab_sleep_disabled_setting():
    doc = SidebarDocument.fresh()
    space = doc.spaces[0]
    t = doc.add_tab(space.id, "https://idle.com")
    t.tab_data.time_last_active = time.time() - 99999

    discarded = []
    svc = TabSleepService(
        doc=doc,
        settings={"tab_sleep_enabled": False, "tab_sleep_threshold_minutes": 60},
        get_active_tab_ids=lambda: set(),
        get_view=lambda tid: MagicMock(),
        discard_view=lambda tid: discarded.append(tid),
    )

    assert svc.sweep() == 0
    assert len(discarded) == 0
