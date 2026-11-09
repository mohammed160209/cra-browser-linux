"""Persistent JSON storage for Cra Browser Linux."""

from __future__ import annotations
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from .sidebar import SidebarDocument, SidebarItem


def get_config_dir() -> Path:
    """Get the XDG configuration directory for Cra Browser."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        base = Path(xdg_config)
    else:
        base = Path.home() / ".config"
    config_dir = base / "cra-browser"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


class Storage:
    """Manages disk persistence of spaces, tabs, archive, and settings."""

    @classmethod
    def get_sidebar_path(cls) -> Path:
        return get_config_dir() / "sidebar.json"

    @classmethod
    def get_settings_path(cls) -> Path:
        return get_config_dir() / "settings.json"

    @classmethod
    def get_archive_path(cls) -> Path:
        return get_config_dir() / "archive.json"

    @classmethod
    def load_sidebar(cls) -> SidebarDocument:
        path = cls.get_sidebar_path()
        if not path.exists():
            doc = SidebarDocument.fresh()
            cls.save_sidebar(doc)
            return doc
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return SidebarDocument.from_dict(data)
        except Exception as e:
            print(f"[CraStorage] Error reading sidebar.json: {e}, falling back to fresh state.")
            doc = SidebarDocument.fresh()
            return doc

    @classmethod
    def save_sidebar(cls, doc: SidebarDocument):
        path = cls.get_sidebar_path()
        tmp_path = path.with_suffix(".tmp")
        try:
            data = doc.to_dict()
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_path.replace(path)
        except Exception as e:
            print(f"[CraStorage] Error saving sidebar.json: {e}")

    @classmethod
    def load_settings(cls) -> Dict[str, Any]:
        path = cls.get_settings_path()
        defaults = {
            "search_engine": "DuckDuckGo",
            "adblock_enabled": True,
            "auto_archive_threshold_hours": 24,
            "sidebar_width": 260,
            "hardware_acceleration": True,
            "https_only": True,
        }
        if not path.exists():
            cls.save_settings(defaults)
            return defaults
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            defaults.update(loaded)
            return defaults
        except Exception:
            return defaults

    @classmethod
    def save_settings(cls, settings: Dict[str, Any]):
        path = cls.get_settings_path()
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            tmp_path.replace(path)
        except Exception as e:
            print(f"[CraStorage] Error saving settings: {e}")

    @classmethod
    def archive_tabs(cls, items: List[SidebarItem], reason: str = "manual"):
        if not items:
            return
        path = cls.get_archive_path()
        current: List[dict] = []
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    current = json.load(f)
            except Exception:
                current = []

        now = time.time()
        for item in items:
            current.append({
                "archivedAt": now,
                "reason": reason,
                "item": item.to_dict(),
            })

        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(current, f, indent=2, ensure_ascii=False)
            tmp_path.replace(path)
        except Exception as e:
            print(f"[CraStorage] Error updating archive.json: {e}")

    @classmethod
    def load_archive(cls) -> List[dict]:
        path = cls.get_archive_path()
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @classmethod
    def clear_archive(cls):
        path = cls.get_archive_path()
        if path.exists():
            try:
                path.unlink()
            except Exception as e:
                print(f"[CraStorage] Error clearing archive.json: {e}")

    @classmethod
    def run_auto_archive(cls, doc: SidebarDocument, settings: Dict[str, Any]) -> int:
        """Run inactive Today tab auto-archiving based on settings."""
        threshold_hours = settings.get("auto_archive_threshold_hours", 24)
        if threshold_hours <= 0:
            return 0
        archived = doc.auto_archive_today_tabs(threshold_hours)
        if archived:
            cls.archive_tabs(archived, reason="auto")
            cls.save_sidebar(doc)
            print(f"[CraStorage] Auto-archived {len(archived)} inactive tabs (threshold: {threshold_hours}h).")
        return len(archived)
