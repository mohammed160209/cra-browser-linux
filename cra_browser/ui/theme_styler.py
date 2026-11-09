"""Dynamic CSS styling for Cra Browser Linux based on Space themes."""

from __future__ import annotations
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.theme import SpaceTheme, hex_luminance


class ThemeStyler:
    """Generates and updates GTK CSS styles based on active SpaceTheme."""

    def __init__(self):
        self.provider = Gtk.CssProvider()
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                self.provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def apply_theme(self, theme: SpaceTheme):
        """Apply CSS rules for the sidebar, window chrome, and command bar."""
        gradient = theme.to_css_gradient()
        is_dark = theme.is_dark

        text_color = "#FFFFFF" if is_dark else "#1A1A1A"
        subtext_color = "rgba(255, 255, 255, 0.7)" if is_dark else "rgba(0, 0, 0, 0.65)"
        tile_bg = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.07)"
        tile_hover = "rgba(255, 255, 255, 0.22)" if is_dark else "rgba(0, 0, 0, 0.13)"
        active_tab_bg = "rgba(255, 255, 255, 0.20)" if is_dark else "rgba(0, 0, 0, 0.12)"
        active_border = "rgba(255, 255, 255, 0.35)" if is_dark else "rgba(0, 0, 0, 0.25)"
        border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.08)"
        split_border = "rgba(53, 132, 228, 0.8)"  # Libadwaita accent blue for active split

        css = f"""
        .cra-sidebar {{
            background: {gradient};
            color: {text_color};
            border-right: 1px solid {border_color};
        }}

        .cra-sidebar label {{
            color: {text_color};
        }}

        .cra-sidebar .subtext {{
            color: {subtext_color};
            font-size: 11px;
            font-weight: 500;
        }}

        .cra-nav-btn {{
            background: transparent;
            color: {text_color};
            border-radius: 8px;
            padding: 4px;
            min-height: 28px;
            min-width: 28px;
            border: none;
            transition: background 120ms ease;
        }}

        .cra-nav-btn:hover {{
            background: {tile_bg};
        }}

        .cra-nav-btn:disabled {{
            opacity: 0.35;
        }}

        .cra-url-pill {{
            background: {tile_bg};
            color: {text_color};
            border-radius: 12px;
            padding: 6px 12px;
            border: 1px solid {border_color};
            font-size: 13px;
            transition: all 140ms ease;
        }}

        .cra-url-pill:hover {{
            background: {tile_hover};
            border-color: {active_border};
        }}

        .cra-favorite-tile {{
            background: {tile_bg};
            border-radius: 10px;
            padding: 8px 6px;
            border: 1px solid {border_color};
            min-height: 48px;
            transition: all 150ms ease;
        }}

        .cra-favorite-tile:hover {{
            background: {tile_hover};
            transform: translateY(-1px);
        }}

        .cra-favorite-tile.active-favorite {{
            background: {active_tab_bg};
            border: 1.5px solid {active_border};
        }}

        .cra-favorite-monogram {{
            font-weight: bold;
            font-size: 13px;
            letter-spacing: 0.5px;
        }}

        .cra-tab-row {{
            border-radius: 8px;
            padding: 6px 10px;
            margin: 1px 4px;
            transition: background 120ms ease;
        }}

        .cra-tab-row:hover {{
            background: {tile_bg};
        }}

        .cra-tab-row.active {{
            background: {active_tab_bg};
            font-weight: 600;
            border: 1px solid {border_color};
        }}

        .cra-tab-row.cra-tab-sleeping {{
            opacity: 0.72;
        }}

        .cra-audio-btn {{
            color: #3584E4;
            padding: 2px 4px;
            min-height: 22px;
            min-width: 22px;
        }}

        .cra-audio-btn:hover {{
            background: rgba(53, 132, 228, 0.2);
        }}

        .cra-home-reset-btn {{
            color: #3584E4;
            padding: 2px 4px;
            min-height: 22px;
            min-width: 22px;
        }}

        .cra-home-reset-btn:hover {{
            background: rgba(53, 132, 228, 0.2);
        }}

        .cra-folder-row {{
            border-radius: 8px;
            padding: 6px 8px;
            margin: 1px 4px;
            font-weight: 600;
            transition: background 120ms ease;
        }}

        .cra-folder-row:hover {{
            background: {tile_bg};
        }}

        .cra-folder-count {{
            font-size: 11px;
            padding: 1px 6px;
            border-radius: 10px;
            background: {tile_bg};
        }}

        .cra-space-dock {{
            background: rgba(0, 0, 0, 0.22);
            border-top: 1px solid {border_color};
            padding: 6px 8px;
        }}

        .cra-space-pill {{
            border-radius: 16px;
            padding: 4px 12px;
            color: {text_color};
            background: transparent;
            font-size: 13px;
            transition: all 120ms ease;
        }}

        .cra-space-pill:hover {{
            background: {tile_bg};
        }}

        .cra-space-pill.active {{
            background: {tile_hover};
            font-weight: bold;
            border: 1px solid {border_color};
        }}

        .cra-command-card {{
            background: #25282E;
            color: #FFFFFF;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 20px 48px rgba(0, 0, 0, 0.65);
            padding: 14px;
        }}

        .cra-command-input-container {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.14);
            padding: 4px 8px;
        }}

        .cra-command-entry {{
            font-size: 16px;
            background: transparent;
            color: #FFFFFF;
            border: none;
            box-shadow: none;
            padding: 6px 8px;
        }}

        .cra-scope-pill {{
            background: #3584E4;
            color: #FFFFFF;
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 12px;
            font-weight: 600;
            border: none;
        }}

        .cra-command-results {{
            background: transparent;
            margin-top: 6px;
        }}

        .cra-badge {{
            font-size: 11px;
            background: rgba(255, 255, 255, 0.12);
            color: rgba(255, 255, 255, 0.8);
            border-radius: 6px;
            padding: 2px 6px;
            font-family: monospace;
        }}

        .cra-split-bar {{
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 4px 8px;
        }}

        .active-pane {{
            outline: 2px solid {split_border};
            outline-offset: -2px;
        }}

        .cra-unhide-btn {{
            background: rgba(30, 30, 30, 0.85);
            color: #FFFFFF;
            border-radius: 8px;
            padding: 6px 10px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            margin: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }}

        .cra-unhide-btn:hover {{
            background: rgba(50, 50, 50, 0.95);
        }}

        paned > separator {{
            background: rgba(0, 0, 0, 0.15);
            min-width: 2px;
            transition: background 150ms ease;
        }}

        paned > separator:hover {{
            background: #3584E4;
        }}
        """

        try:
            self.provider.load_from_data(css.encode("utf-8"))
        except Exception as e:
            print(f"[ThemeStyler] CSS load error: {e}")
