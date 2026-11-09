"""Tests for cra_browser.model.sidebar."""

import time
from cra_browser.model.sidebar import TabData, SidebarItem, SidebarDocument


def test_tab_data_basic():
    tab = TabData(url="https://cachyos.org", saved_url="https://cachyos.org", saved_title="CachyOS")
    assert tab.url == "https://cachyos.org"
    assert tab.saved_url == "https://cachyos.org"
    assert tab.saved_title == "CachyOS"

    tab.url = "https://cachyos.org/download"
    assert tab.url != tab.saved_url

    tab.return_home()
    assert tab.url == "https://cachyos.org"

    tab.url = "https://wiki.cachyos.org"
    tab.make_current_page_home()
    assert tab.saved_url == "https://wiki.cachyos.org"


def test_tab_data_serialization():
    tab = TabData(url="https://archlinux.org", saved_url="https://archlinux.org", saved_title="Arch Linux")
    d = tab.to_dict()
    assert d["url"] == "https://archlinux.org"
    assert d["savedURL"] == "https://archlinux.org"
    assert d["savedTitle"] == "Arch Linux"

    restored = TabData.from_dict(d)
    assert restored.url == tab.url
    assert restored.saved_url == tab.saved_url
    assert restored.saved_title == tab.saved_title


def test_sidebar_item_away_from_home():
    tab_data = TabData(url="https://github.com", saved_url="https://github.com")
    item = SidebarItem(item_type="tab", tab_data=tab_data)
    assert not item.is_away_from_home

    tab_data.url = "https://github.com/mohammed160209"
    assert item.is_away_from_home

    item.reset_to_home()
    assert not item.is_away_from_home
    assert tab_data.url == "https://github.com"


def test_sidebar_item_renaming():
    tab_data = TabData(url="https://github.com", saved_url="https://github.com", saved_title="GitHub Page")
    item = SidebarItem(item_type="tab", tab_data=tab_data)
    assert item.display_title == "GitHub Page"

    item.rename("My Repos")
    assert item.display_title == "My Repos"
    assert item.title == "My Repos"

    item.rename(None)
    assert item.display_title == "GitHub Page"


def test_sidebar_document_containers_and_tabs():
    doc = SidebarDocument.fresh()
    assert len(doc.spaces) >= 2
    personal = doc.spaces[0]

    # Verify containers exist
    assert doc.get_item(personal.favorites_container_id) is not None
    assert doc.get_item(personal.pinned_container_id) is not None
    assert doc.get_item(personal.today_container_id) is not None

    # Add tab to Today
    new_tab = doc.add_tab(personal.id, "https://news.ycombinator.com", "Hacker News")
    assert new_tab.id in doc.get_item(personal.today_container_id).children

    # Pin tab
    doc.pin_tab(new_tab.id)
    assert new_tab.id not in doc.get_item(personal.today_container_id).children
    assert new_tab.id in doc.get_item(personal.pinned_container_id).children
    assert new_tab.tab_data.saved_url == "https://news.ycombinator.com"

    # Unpin tab
    doc.unpin_tab(new_tab.id)
    assert new_tab.id in doc.get_item(personal.today_container_id).children
    assert new_tab.id not in doc.get_item(personal.pinned_container_id).children


def test_nested_folders():
    doc = SidebarDocument()
    space = doc.create_space("Work", "💼")

    folder1 = doc.add_folder(space.id, title="Docs")
    assert folder1.item_type == "folder"
    assert folder1.is_expanded
    assert folder1.id in doc.get_item(space.pinned_container_id).children

    # Add nested subfolder
    subfolder = doc.add_folder(space.id, title="API Specs", parent_id=folder1.id)
    assert subfolder.id in folder1.children

    # Add tab in nested subfolder
    tab = doc.add_tab(space.id, "https://docs.rs", "Docs.rs", parent_folder_id=subfolder.id)
    assert tab.id in subfolder.children

    # Toggle expansion
    doc.toggle_folder(folder1.id)
    assert not folder1.is_expanded
    doc.toggle_folder(folder1.id)
    assert folder1.is_expanded

    # Serialization roundtrip
    d = doc.to_dict()
    restored = SidebarDocument.from_dict(d)
    r_folder1 = restored.get_item(folder1.id)
    assert r_folder1 is not None
    assert r_folder1.item_type == "folder"
    assert subfolder.id in r_folder1.children


def test_clear_today_tabs():
    doc = SidebarDocument()
    space = doc.create_space("Personal", "🌱")

    tab1 = doc.add_tab(space.id, "https://a.com")
    tab2 = doc.add_tab(space.id, "https://b.com")
    doc.add_tab(space.id, "https://pinned.com", is_pinned=True)

    archived = doc.clear_today_tabs(space.id)
    assert len(archived) == 2
    assert {a.id for a in archived} == {tab1.id, tab2.id}

    today_cont = doc.get_item(space.today_container_id)
    assert len(today_cont.children) == 0

    # Pinned remains untouched
    pinned_cont = doc.get_item(space.pinned_container_id)
    assert len(pinned_cont.children) == 1


def test_auto_archive_today_tabs():
    doc = SidebarDocument()
    space = doc.create_space("Personal", "🌱")

    # Recent tab (last active now)
    recent = doc.add_tab(space.id, "https://recent.com")

    # Inactive tab (last active 48 hours ago)
    old = doc.add_tab(space.id, "https://old.com")
    old.tab_data.time_last_active = time.time() - (48 * 3600)

    # Auto archive with 24h threshold
    archived = doc.auto_archive_today_tabs(threshold_hours=24)
    assert len(archived) == 1
    assert archived[0].id == old.id

    today_cont = doc.get_item(space.today_container_id)
    assert today_cont.children == [recent.id]


def test_delete_space():
    doc = SidebarDocument.fresh()
    initial_count = len(doc.spaces)
    space_to_delete = doc.spaces[-1].id

    success = doc.delete_space(space_to_delete)
    assert success
    assert len(doc.spaces) == initial_count - 1
    assert space_to_delete not in doc.space_order

    # Cannot delete the only remaining space
    while len(doc.spaces) > 1:
        doc.delete_space(doc.spaces[-1].id)
    last_id = doc.spaces[0].id
    assert not doc.delete_space(last_id)
    assert len(doc.spaces) == 1
