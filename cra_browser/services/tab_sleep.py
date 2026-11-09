"""Arc/Cra-style Tab Sleep and Memory Saver service for Linux port."""

from __future__ import annotations
import time
from typing import Callable, Dict, List, Optional, Set
import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

from ..model.sidebar import SidebarItem, SidebarDocument
from ..model.storage import Storage


class TabSleepService:
    """Manages memory saver and tab sleep policy (1:1 parity with CraCore.TabSleepPolicy)."""

    PROTECTED_RECENT_TABS = 10  # Arc WebContentLifecycleOptimization protectedLRUTabCount

    def __init__(
        self,
        doc: SidebarDocument,
        settings: dict,
        get_active_tab_ids: Callable[[], Set[str]],
        get_view: Callable[[str], Optional[any]],
        discard_view: Callable[[str], None],
        on_tab_slept: Optional[Callable[[SidebarItem], None]] = None,
    ):
        self.doc = doc
        self.settings = settings
        self.get_active_tab_ids = get_active_tab_ids
        self.get_view = get_view
        self.discard_view = discard_view
        self.on_tab_slept = on_tab_slept
        self._timer_id: Optional[int] = None

    def start(self):
        """Start the periodic sleep sweep timer (runs every 60 seconds)."""
        if self._timer_id is None:
            self._timer_id = GLib.timeout_add_seconds(60, self._on_timer_tick)

    def stop(self):
        """Stop the periodic sweep timer."""
        if self._timer_id is not None:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

    def _on_timer_tick(self) -> bool:
        self.sweep()
        return True  # Keep GLib timer running

    @property
    def is_enabled(self) -> bool:
        return bool(self.settings.get("tab_sleep_enabled", True))

    @property
    def threshold_seconds(self) -> float:
        mins = self.settings.get("tab_sleep_threshold_minutes", 60)
        return float(mins * 60) if mins > 0 else 0.0

    def sweep(self) -> int:
        """Evaluate open tabs and hibernate those exceeding the inactivity threshold."""
        if not self.is_enabled:
            return 0

        thresh = self.threshold_seconds
        if thresh <= 0:
            return 0

        now = time.time()
        active_ids = self.get_active_tab_ids()

        # Collect all items with active views
        all_tabs: List[SidebarItem] = []
        for item in self.doc.items.values():
            if item.item_type == "tab" and item.tab_data:
                all_tabs.append(item)

        # Sort tabs by time_last_active descending (most recently used first)
        all_tabs.sort(key=lambda it: it.tab_data.time_last_active if it.tab_data else 0, reverse=True)

        # Protect the top N most recently active tabs
        protected_by_lru = {it.id for it in all_tabs[: self.PROTECTED_RECENT_TABS]}

        slept_count = 0
        for item in all_tabs:
            if item.id in active_ids:
                continue
            if item.id in protected_by_lru:
                continue
            if not item.tab_data:
                continue

            # Check if tab is currently playing audio
            view = self.get_view(item.id)
            if view:
                if getattr(view, "is_playing_audio", False) or item.tab_data.is_audible:
                    continue

                inactive_duration = now - item.tab_data.time_last_active
                if inactive_duration >= thresh:
                    self.sleep_tab(item, view)
                    slept_count += 1

        if slept_count > 0:
            Storage.save_sidebar(self.doc)
            print(f"[TabSleep] Discarded {slept_count} idle tab(s) to free system memory.")

        return slept_count

    def sleep_tab(self, item: SidebarItem, view: any):
        """Hibernate a specific tab, saving its session state and freeing its WebKit process."""
        if not item.tab_data:
            return

        # Capture session state
        if hasattr(view, "get_session_state_b64"):
            b64_state = view.get_session_state_b64()
            if b64_state:
                item.tab_data.session_state = b64_state

        item.tab_data.is_sleeping = True

        # Discard the view from memory
        self.discard_view(item.id)

        if self.on_tab_slept:
            self.on_tab_slept(item)
