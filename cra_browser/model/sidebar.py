"""Sidebar and tab data structures for Cra Browser Linux."""

from __future__ import annotations
import uuid
import time
from urllib.parse import urlparse
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .space import Space
from .theme import THEME_PRESETS


@dataclass
class TabData:
    """State for a single browser tab."""
    url: str
    saved_url: str
    saved_title: str = ""
    favicon_url: Optional[str] = None
    time_last_active: float = field(default_factory=time.time)
    muted: bool = False
    custom_icon: Optional[str] = None
    tile_color: Optional[str] = None
    session_state: Optional[str] = None  # Base64 serialized WebKit.WebViewSessionState
    is_sleeping: bool = False
    is_audible: bool = False

    def note_title(self, title: str, pinned: bool = False):
        if title:
            self.saved_title = title

    def make_current_page_home(self):
        self.saved_url = self.url

    def return_home(self):
        self.url = self.saved_url

    def touch_active(self):
        self.time_last_active = time.time()
        self.is_sleeping = False

    def to_dict(self) -> dict:
        d = {
            "url": self.url,
            "savedURL": self.saved_url,
            "savedTitle": self.saved_title,
            "faviconKey": self.favicon_url,
            "timeLastActiveAt": self.time_last_active,
            "muted": self.muted,
            "tileColor": self.tile_color,
        }
        if self.session_state:
            d["sessionState"] = self.session_state
        return d

    @classmethod
    def from_dict(cls, data: dict) -> TabData:
        url = data.get("url", "about:blank")
        return cls(
            url=url,
            saved_url=data.get("savedURL", url),
            saved_title=data.get("savedTitle", ""),
            favicon_url=data.get("faviconKey"),
            time_last_active=data.get("timeLastActiveAt", time.time()),
            muted=data.get("muted", False),
            tile_color=data.get("tileColor"),
            session_state=data.get("sessionState"),
            is_sleeping=data.get("isSleeping", False),
        )


@dataclass
class SidebarItem:
    """An item in the Cra sidebar (tab, folder, container, split)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    title: Optional[str] = None
    children: List[str] = field(default_factory=list)
    is_unread: bool = False
    is_expanded: bool = True  # For folders
    created_at: float = field(default_factory=time.time)
    item_type: str = "tab"  # "tab" | "folder" | "container" | "split"
    tab_data: Optional[TabData] = None
    container_kind: Optional[str] = None  # "favorites" | "pinned" | "today"
    space_id: Optional[str] = None

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title
        if self.item_type == "folder":
            return "Folder"
        if self.item_type == "split":
            return "Split View"
        if self.tab_data:
            if self.tab_data.saved_title:
                return self.tab_data.saved_title
            parsed = urlparse(self.tab_data.url)
            if parsed.netloc:
                return parsed.netloc
            return self.tab_data.url
        return "Untitled"

    @property
    def host(self) -> str:
        if self.tab_data and self.tab_data.url:
            parsed = urlparse(self.tab_data.url)
            return parsed.netloc.replace("www.", "")
        return ""

    @property
    def is_away_from_home(self) -> bool:
        """True if this is a pinned tab whose current URL differs from its saved home URL."""
        if not self.tab_data or not self.tab_data.saved_url:
            return False
        u1 = self.tab_data.url.rstrip("/")
        u2 = self.tab_data.saved_url.rstrip("/")
        return bool(u1 and u2 and u1 != u2)

    def reset_to_home(self):
        """Restore the tab to its initial home URL."""
        if self.tab_data and self.tab_data.saved_url:
            self.tab_data.url = self.tab_data.saved_url

    def make_current_page_home(self):
        """Update saved home URL to the current URL."""
        if self.tab_data:
            self.tab_data.saved_url = self.tab_data.url

    def rename(self, new_title: Optional[str]):
        """Rename the tab or folder (custom user title)."""
        clean = new_title.strip() if new_title else None
        self.title = clean if clean else None

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "parentID": self.parent_id,
            "title": self.title,
            "children": self.children,
            "isUnread": self.is_unread,
            "isExpanded": self.is_expanded,
            "createdAt": self.created_at,
            "itemType": self.item_type,
        }
        if self.tab_data:
            d["tabData"] = self.tab_data.to_dict()
        if self.container_kind:
            d["containerKind"] = self.container_kind
        if self.space_id:
            d["spaceID"] = self.space_id
        return d

    @classmethod
    def from_dict(cls, data: dict) -> SidebarItem:
        tab_data = TabData.from_dict(data["tabData"]) if "tabData" in data else None
        return cls(
            id=str(data.get("id", uuid.uuid4())),
            parent_id=data.get("parentID"),
            title=data.get("title"),
            children=[str(c) for c in data.get("children", [])],
            is_unread=data.get("isUnread", False),
            is_expanded=data.get("isExpanded", True),
            created_at=data.get("createdAt", time.time()),
            item_type=data.get("itemType", "tab"),
            tab_data=tab_data,
            container_kind=data.get("containerKind"),
            space_id=data.get("spaceID"),
        )


class SidebarDocument:
    """Root model holding all spaces, containers, and items."""
    def __init__(self):
        self.version: int = 1
        self.spaces: List[Space] = []
        self.space_order: List[str] = []
        self.items: Dict[str, SidebarItem] = {}

    def get_space(self, space_id: str) -> Optional[Space]:
        for s in self.spaces:
            if s.id == space_id:
                return s
        return None

    def get_item(self, item_id: str) -> Optional[SidebarItem]:
        return self.items.get(item_id)

    def get_children(self, parent_id: str) -> List[SidebarItem]:
        parent = self.get_item(parent_id)
        if not parent:
            return []
        result = []
        for child_id in parent.children:
            item = self.get_item(child_id)
            if item:
                result.append(item)
        return result

    def add_tab(
        self,
        space_id: str,
        url: str,
        title: str = "",
        is_pinned: bool = False,
        is_favorite: bool = False,
        parent_folder_id: Optional[str] = None,
    ) -> SidebarItem:
        """Add a tab to a space's Today, Pinned, Favorites, or a nested folder."""
        space = self.get_space(space_id)
        if not space:
            if self.spaces:
                space = self.spaces[0]
                space_id = space.id
            else:
                space = self.create_space("Personal", "🌱")
                space_id = space.id

        if parent_folder_id and parent_folder_id in self.items:
            target_container_id = parent_folder_id
        elif is_favorite:
            target_container_id = space.favorites_container_id
        elif is_pinned:
            target_container_id = space.pinned_container_id
        else:
            target_container_id = space.today_container_id

        container = self.get_item(target_container_id)
        if not container:
            container = SidebarItem(
                id=target_container_id,
                item_type="container",
                container_kind="favorites" if is_favorite else ("pinned" if is_pinned else "today"),
                space_id=space_id,
            )
            self.items[target_container_id] = container

        tab_item = SidebarItem(
            id=str(uuid.uuid4()),
            parent_id=target_container_id,
            title=title if title else None,
            item_type="tab",
            tab_data=TabData(url=url, saved_url=url, saved_title=title),
            space_id=space_id,
        )
        self.items[tab_item.id] = tab_item
        container.children.append(tab_item.id)
        return tab_item

    def add_folder(
        self,
        space_id: str,
        title: str = "New Folder",
        parent_id: Optional[str] = None,
    ) -> SidebarItem:
        """Add a foldable folder to Pinned tabs (or nested inside another folder)."""
        space = self.get_space(space_id)
        if not space:
            space = self.spaces[0]
            space_id = space.id

        target_parent = parent_id if parent_id else space.pinned_container_id
        parent_item = self.get_item(target_parent)
        if not parent_item:
            parent_item = SidebarItem(
                id=target_parent,
                item_type="container",
                container_kind="pinned",
                space_id=space_id,
            )
            self.items[target_parent] = parent_item

        folder_item = SidebarItem(
            id=str(uuid.uuid4()),
            parent_id=target_parent,
            title=title,
            item_type="folder",
            is_expanded=True,
            space_id=space_id,
        )
        self.items[folder_item.id] = folder_item
        parent_item.children.append(folder_item.id)
        return folder_item

    def toggle_folder(self, folder_id: str) -> bool:
        """Toggle expand/collapse state of a folder."""
        folder = self.get_item(folder_id)
        if folder and folder.item_type == "folder":
            folder.is_expanded = not folder.is_expanded
            return folder.is_expanded
        return False

    def remove_tab(self, item_id: str):
        """Remove a tab or folder from the sidebar."""
        item = self.items.pop(item_id, None)
        if item and item.parent_id:
            parent = self.get_item(item.parent_id)
            if parent and item_id in parent.children:
                parent.children.remove(item_id)
        # If it was a folder, remove all descendants
        if item and item.item_type == "folder":
            for child_id in list(item.children):
                self.remove_tab(child_id)

    def pin_tab(self, item_id: str, target_folder_id: Optional[str] = None):
        """Move a tab from Today to Pinned (or into a specific folder)."""
        item = self.get_item(item_id)
        if not item or not item.space_id:
            return
        space = self.get_space(item.space_id)
        if not space:
            return

        # Remove from old parent
        if item.parent_id:
            parent = self.get_item(item.parent_id)
            if parent and item_id in parent.children:
                parent.children.remove(item_id)

        # Target container
        target_container_id = target_folder_id if target_folder_id else space.pinned_container_id
        pinned_container = self.get_item(target_container_id)
        if pinned_container:
            item.parent_id = pinned_container.id
            if item_id not in pinned_container.children:
                pinned_container.children.append(item_id)
            if item.tab_data:
                item.tab_data.make_current_page_home()

    def unpin_tab(self, item_id: str):
        """Move a tab from Pinned/Favorites to Today in its space."""
        item = self.get_item(item_id)
        if not item or not item.space_id:
            return
        space = self.get_space(item.space_id)
        if not space:
            return

        if item.parent_id:
            parent = self.get_item(item.parent_id)
            if parent and item_id in parent.children:
                parent.children.remove(item_id)

        today_container = self.get_item(space.today_container_id)
        if today_container:
            item.parent_id = today_container.id
            if item_id not in today_container.children:
                today_container.children.insert(0, item_id)

    def make_favorite(self, item_id: str):
        """Move or promote a tab to Favorites in its space."""
        item = self.get_item(item_id)
        if not item or not item.space_id:
            return
        space = self.get_space(item.space_id)
        if not space:
            return

        if item.parent_id:
            parent = self.get_item(item.parent_id)
            if parent and item_id in parent.children:
                parent.children.remove(item_id)

        fav_container = self.get_item(space.favorites_container_id)
        if fav_container:
            item.parent_id = fav_container.id
            if item_id not in fav_container.children:
                fav_container.children.append(item_id)

    def clear_today_tabs(self, space_id: str) -> List[SidebarItem]:
        """Clear and return all Today tabs for a space (archiving them)."""
        space = self.get_space(space_id)
        if not space:
            return []
        today_container = self.get_item(space.today_container_id)
        if not today_container:
            return []

        archived: List[SidebarItem] = []
        for child_id in list(today_container.children):
            item = self.items.pop(child_id, None)
            if item:
                archived.append(item)
        today_container.children.clear()
        return archived

    def auto_archive_today_tabs(self, threshold_hours: int) -> List[SidebarItem]:
        """Archive inactive today tabs older than threshold_hours across all spaces."""
        if threshold_hours <= 0:
            return []
        threshold_seconds = threshold_hours * 3600
        now = time.time()
        archived: List[SidebarItem] = []

        for space in self.spaces:
            today_container = self.get_item(space.today_container_id)
            if not today_container:
                continue
            retained: List[str] = []
            for child_id in today_container.children:
                item = self.get_item(child_id)
                if not item:
                    continue
                last_active = item.tab_data.time_last_active if item.tab_data else item.created_at
                if (now - last_active) > threshold_seconds:
                    archived.append(item)
                    self.items.pop(child_id, None)
                else:
                    retained.append(child_id)
            today_container.children = retained

        return archived

    def create_space(self, title: str, emoji: str, theme: Optional[THEME_PRESETS] = None) -> Space:
        """Create a new space with its 3 containers."""
        space_id = str(uuid.uuid4())
        fav_id = str(uuid.uuid4())
        pin_id = str(uuid.uuid4())
        today_id = str(uuid.uuid4())

        chosen_theme = theme if theme else THEME_PRESETS[len(self.spaces) % len(THEME_PRESETS)][1]
        space = Space(
            id=space_id,
            title=title,
            emoji=emoji,
            theme=chosen_theme,
            favorites_container_id=fav_id,
            pinned_container_id=pin_id,
            today_container_id=today_id,
        )

        self.items[fav_id] = SidebarItem(id=fav_id, item_type="container", container_kind="favorites", space_id=space_id)
        self.items[pin_id] = SidebarItem(id=pin_id, item_type="container", container_kind="pinned", space_id=space_id)
        self.items[today_id] = SidebarItem(id=today_id, item_type="container", container_kind="today", space_id=space_id)

        self.spaces.append(space)
        self.space_order.append(space_id)
        return space

    def delete_space(self, space_id: str) -> bool:
        """Delete a space and all its tabs (prevent deleting the only space)."""
        if len(self.spaces) <= 1:
            return False
        space = self.get_space(space_id)
        if not space:
            return False

        # Remove items in its containers
        for cid in (space.today_container_id, space.pinned_container_id, space.favorites_container_id):
            container = self.items.pop(cid, None)
            if container:
                for child_id in container.children:
                    self.remove_tab(child_id)

        self.spaces.remove(space)
        if space_id in self.space_order:
            self.space_order.remove(space_id)
        return True

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "spaceOrder": self.space_order,
            "spaces": [s.to_dict() for s in self.spaces],
            "items": [item.to_dict() for item in self.items.values()],
        }

    @classmethod
    def from_dict(cls, data: dict) -> SidebarDocument:
        doc = cls()
        doc.version = data.get("version", 1)
        doc.space_order = [str(x) for x in data.get("spaceOrder", [])]
        doc.spaces = [Space.from_dict(s) for s in data.get("spaces", [])]
        for item_data in data.get("items", []):
            item = SidebarItem.from_dict(item_data)
            doc.items[item.id] = item
        return doc

    @classmethod
    def fresh(cls) -> SidebarDocument:
        """Create a brand new starter document with two spaces and defaults."""
        doc = cls()
        # Personal Space
        p_space = doc.create_space("Personal", "🌱", THEME_PRESETS[0][1])
        # Add starter favorites
        doc.add_tab(p_space.id, "https://duckduckgo.com", "DuckDuckGo", is_favorite=True)
        doc.add_tab(p_space.id, "https://github.com", "GitHub", is_favorite=True)
        doc.add_tab(p_space.id, "https://wikipedia.org", "Wikipedia", is_favorite=True)
        doc.add_tab(p_space.id, "https://cachyos.org", "CachyOS", is_favorite=True)

        # Starter pinned tab
        doc.add_tab(p_space.id, "https://wiki.archlinux.org", "ArchWiki", is_pinned=True)

        # Initial today tab
        doc.add_tab(p_space.id, "https://duckduckgo.com", "Search or enter URL…")

        # Work Space
        w_space = doc.create_space("Work", "💼", THEME_PRESETS[6][1])  # Brand violet
        doc.add_tab(w_space.id, "https://github.com", "GitHub", is_favorite=True)
        doc.add_tab(w_space.id, "https://duckduckgo.com", "Search or enter URL…")

        return doc
