"""Space model for Cra Browser Linux."""

from __future__ import annotations
import uuid
import time
from dataclasses import dataclass, field
from typing import Optional
from .theme import SpaceTheme, THEME_PRESETS


@dataclass
class Space:
    """A Space in Cra/Arc, containing its own favorites, pinned tabs, and today tabs."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Personal"
    emoji: str = "🌱"
    theme: SpaceTheme = field(default_factory=lambda: THEME_PRESETS[0][1])
    favorites_container_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pinned_container_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    today_container_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    profile_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "emoji": self.emoji,
            "theme": self.theme.to_dict(),
            "favoritesContainerID": self.favorites_container_id,
            "pinnedContainerID": self.pinned_container_id,
            "todayContainerID": self.today_container_id,
            "createdAt": self.created_at,
            "profileID": self.profile_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Space:
        theme_data = data.get("theme", {})
        theme = SpaceTheme.from_dict(theme_data) if isinstance(theme_data, dict) else THEME_PRESETS[0][1]
        return cls(
            id=str(data.get("id", uuid.uuid4())),
            title=data.get("title", "Personal"),
            emoji=data.get("emoji", "🌱"),
            theme=theme,
            favorites_container_id=str(data.get("favoritesContainerID", uuid.uuid4())),
            pinned_container_id=str(data.get("pinnedContainerID", uuid.uuid4())),
            today_container_id=str(data.get("todayContainerID", uuid.uuid4())),
            created_at=data.get("createdAt", time.time()),
            profile_id=data.get("profileID"),
        )
