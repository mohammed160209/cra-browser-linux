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

    def note_title(self, title: str, pinned: bool = False):
        if title:
            self.saved_title = title

    def make_current_page_home(self):
        self.saved_url = self.url

    def return_home(self):
        self.url = self.saved_url

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "savedURL": self.saved_url,
            "savedTitle": self.saved_title,
            "faviconKey": self.favicon_url,
            "timeLastActiveAt": self.time_last_active,
            "muted": self.muted,
            "tileColor": self.tile_color,
        }

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
        )


@dataclass
class SidebarItem:
    """An item in the Cra sidebar (tab, folder, container, split)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    title: Optional[str] = None
    children: List[str] = field(default_factory=list)
    is_unread: bool = False
    created_at: float = field(default_factory=time.time)
    item_type: str = "tab"  # "tab" | "folder" | "container" | "split"
    tab_data: Optional[TabData] = None
    container_kind: Optional[str] = None  # "favorites" | "pinned" | "today"
    space_id: Optional[str] = None

    @property
    def display_title(self) -> str:
        if self.title:
            return self.title
        if self.tab_data:
            if self.tab_data.saved_title:
                return self.tab_data.saved_title
            parsed = urlparse(self.tab_data.url)
            if parsed.netloc:
                return parsed.netloc
            return self.tab_data.url
        if self.item_type == "folder":
            return "Folder"
        if self.item_type == "split":
            return "Split View"
        return "Untitled"

    @property
    def host(self) -> str:
        if self.tab_data and self.tab_data.url:
            parsed = urlparse(self.tab_data.url)
            return parsed.netloc.replace("www.", "")
        return ""

    def to_dict(self) -> dict:
        d = {
            "id": self.id,
            "parentID": self.parent_id,
            "title": self.title,
            "children": self.children,
            "isUnread": self.is_unread,
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
    ) -> SidebarItem:
        """Add a tab to a space's Today, Pinned, or Favorites container."""
        space = self.get_space(space_id)
        if not space:
            space = self.spaces[0]
            space_id = space.id

        if is_favorite:
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

    def remove_tab(self, item_id: str):
        """Remove a tab from the sidebar."""
        item = self.items.pop(item_id, None)
        if item and item.parent_id:
            parent = self.get_item(item.parent_id)
            if parent and item_id in parent.children:
                parent.children.remove(item_id)

    def pin_tab(self, item_id: str):
        """Move a tab from Today to Pinned in its space."""
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

        # Add to pinned container
        pinned_container = self.get_item(space.pinned_container_id)
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
        # Add popular starter favorites
        doc.add_tab(p_space.id, "https://duckduckgo.com", "DuckDuckGo", is_favorite=True)
        doc.add_tab(p_space.id, "https://github.com", "GitHub", is_favorite=True)
        doc.add_tab(p_space.id, "https://wikipedia.org", "Wikipedia", is_favorite=True)
        doc.add_tab(p_space.id, "https://cachyos.org", "CachyOS", is_favorite=True)

        # Starter pinned tab
        doc.add_tab(p_space.id, "https://wiki.archlinux.org", "ArchWiki", is_pinned=True)

        # Initial today tab
        doc.add_tab(p_space.id, "https://duckduckgo.com", "Search or enter URL...")

        # Work Space
        w_space = doc.create_space("Work", "💼", THEME_PRESETS[6][1])  # Brand violet
        doc.add_tab(w_space.id, "https://github.com", "GitHub", is_favorite=True)
        doc.add_tab(w_space.id, "https://duckduckgo.com", "Search or enter URL...")

        return doc
