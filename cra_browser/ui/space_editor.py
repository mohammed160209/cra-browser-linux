"""Space creation and theme editor dialog."""

from __future__ import annotations
from typing import Callable, Optional
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from ..model.theme import THEME_PRESETS, SpaceTheme
from ..model.space import Space


class SpaceEditorDialog(Adw.Window):
    """Dialog to create or edit a Space's title, emoji, and theme gradient."""

    def __init__(
        self,
        parent_window: Gtk.Window,
        on_save: Callable[[str, str, SpaceTheme], None],
        space_to_edit: Optional[Space] = None,
    ):
        super().__init__()
        self.set_transient_for(parent_window)
        self.set_modal(True)
        self.set_title("Edit Space" if space_to_edit else "New Space")
        self.set_default_size(380, 440)
        self.on_save = on_save
        self.space_to_edit = space_to_edit

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        content.set_margin_start(16)
        content.set_margin_end(16)

        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        self.set_content(content)

        # Title entry
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_lbl = Gtk.Label(label="Space Name")
        title_lbl.set_halign(Gtk.Align.START)
        title_box.append(title_lbl)

        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text("e.g. Research, Projects, Personal")
        if space_to_edit:
            self.title_entry.set_text(space_to_edit.title)
        title_box.append(self.title_entry)
        content.append(title_box)

        # Emoji selector
        emoji_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        emoji_lbl = Gtk.Label(label="Emoji / Icon")
        emoji_lbl.set_halign(Gtk.Align.START)
        emoji_box.append(emoji_lbl)

        self.emoji_entry = Gtk.Entry()
        self.emoji_entry.set_text(space_to_edit.emoji if space_to_edit else "🪐")
        emoji_box.append(self.emoji_entry)
        content.append(emoji_box)

        # Theme preset picker
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        theme_lbl = Gtk.Label(label="Theme Palette")
        theme_lbl.set_halign(Gtk.Align.START)
        theme_box.append(theme_lbl)

        preset_names = [p[0] for p in THEME_PRESETS]
        self.theme_dropdown = Gtk.DropDown.new_from_strings(preset_names)
        if space_to_edit:
            for idx, (name, th) in enumerate(THEME_PRESETS):
                if th.colors == space_to_edit.theme.colors:
                    self.theme_dropdown.set_selected(idx)
                    break
        theme_box.append(self.theme_dropdown)
        content.append(theme_box)

        # Save button
        save_btn = Gtk.Button(label="Save Space" if space_to_edit else "Create Space")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        content.append(save_btn)

    def _on_save_clicked(self, *_):
        title = self.title_entry.get_text().strip() or "Untitled"
        emoji = self.emoji_entry.get_text().strip() or "🪐"
        idx = self.theme_dropdown.get_selected()
        theme = THEME_PRESETS[idx][1]
        self.on_save(title, emoji, theme)
        self.close()
