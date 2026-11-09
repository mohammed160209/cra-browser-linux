"""Tests for cra_browser.model.storage."""

import time
import tempfile
from pathlib import Path
from cra_browser.model.sidebar import SidebarDocument
from cra_browser.model.storage import Storage


def test_storage_save_and_load_sidebar(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        monkeypatch.setattr("cra_browser.model.storage.get_config_dir", lambda: tmp_path)

        doc = SidebarDocument.fresh()
        Storage.save_sidebar(doc)

        assert (tmp_path / "sidebar.json").exists()
        loaded = Storage.load_sidebar()
        assert len(loaded.spaces) == len(doc.spaces)
        assert loaded.space_order == doc.space_order


def test_storage_settings(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        monkeypatch.setattr("cra_browser.model.storage.get_config_dir", lambda: tmp_path)

        settings = Storage.load_settings()
        assert settings["search_engine"] == "DuckDuckGo"
        assert settings["adblock_enabled"] is True

        settings["search_engine"] = "Brave"
        settings["auto_archive_threshold_hours"] = 12
        Storage.save_settings(settings)

        reloaded = Storage.load_settings()
        assert reloaded["search_engine"] == "Brave"
        assert reloaded["auto_archive_threshold_hours"] == 12


def test_storage_archive_and_auto_archive(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        monkeypatch.setattr("cra_browser.model.storage.get_config_dir", lambda: tmp_path)

        doc = SidebarDocument()
        space = doc.create_space("Testing", "🧪")

        # Tab active 30 hours ago
        idle_tab = doc.add_tab(space.id, "https://old-article.org", "Old Article")
        idle_tab.tab_data.time_last_active = time.time() - (30 * 3600)

        # Tab active now
        fresh_tab = doc.add_tab(space.id, "https://fresh.org", "Fresh Page")

        settings = {"auto_archive_threshold_hours": 24}
        archived_count = Storage.run_auto_archive(doc, settings)
        assert archived_count == 1

        archive_items = Storage.load_archive()
        assert len(archive_items) == 1
        assert archive_items[0]["reason"] == "auto"
        assert archive_items[0]["item"]["id"] == idle_tab.id

        # Verify today container only has fresh_tab
        today_cont = doc.get_item(space.today_container_id)
        assert today_cont.children == [fresh_tab.id]

        # Clear archive
        Storage.clear_archive()
        assert len(Storage.load_archive()) == 0
