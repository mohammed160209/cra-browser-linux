"""Dynamic CSS styling for Cra Browser Linux based on Space themes."""

from __future__ import annotations
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
from ..model.theme import SpaceTheme, hex_luminance


class ThemeStyler:
    """Generates and updates GTK CSS styles based on active SpaceTheme."""

    def __init__(self):
        self.provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def apply_theme(self, theme: SpaceTheme):
        """Apply CSS rules for the sidebar and window chrome."""
        gradient = theme.to_css_gradient()
        is_dark = theme.is_dark

        text_color = "#FFFFFF" if is_dark else "#1A1A1A"
        subtext_color = "rgba(255, 255, 255, 0.7)" if is_dark else "rgba(0, 0, 0, 0.65)"
        tile_bg = "rgba(255, 255, 255, 0.12)" if is_dark else "rgba(0, 0, 0, 0.07)"
        tile_hover = "rgba(255, 255, 255, 0.2)" if is_dark else "rgba(0, 0, 0, 0.12)"
        active_tab_bg = "rgba(255, 255, 255, 0.18)" if is_dark else "rgba(0, 0, 0, 0.1)"
        border_color = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(0, 0, 0, 0.08)"

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
        }}

        .cra-nav-btn {{
            background: transparent;
            color: {text_color};
            border-radius: 8px;
            padding: 4px;
            min-height: 28px;
            min-width: 28px;
            border: none;
        }}

        .cra-nav-btn:hover {{
            background: {tile_bg};
        }}

        .cra-url-pill {{
            background: {tile_bg};
            color: {text_color};
            border-radius: 12px;
            padding: 6px 12px;
            border: 1px solid {border_color};
            font-size: 13px;
        }}

        .cra-url-pill:hover {{
            background: {tile_hover};
        }}

        .cra-favorite-tile {{
            background: {tile_bg};
            border-radius: 10px;
            padding: 8px;
            border: 1px solid {border_color};
            transition: all 150ms ease;
        }}

        .cra-favorite-tile:hover {{
            background: {tile_hover};
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
        }}

        .cra-space-dock {{
            background: rgba(0, 0, 0, 0.2);
            border-top: 1px solid {border_color};
            padding: 6px;
        }}

        .cra-space-pill {{
            border-radius: 16px;
            padding: 4px 10px;
            color: {text_color};
            background: transparent;
        }}

        .cra-space-pill:hover {{
            background: {tile_bg};
        }}

        .cra-space-pill.active {{
            background: {tile_hover};
            font-weight: bold;
        }}

        .cra-command-card {{
            background: #25282E;
            color: #FFFFFF;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5);
            padding: 12px;
        }}

        .cra-command-entry {{
            font-size: 16px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            color: #FFFFFF;
            padding: 8px 14px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        """

        try:
            self.provider.load_from_data(css.encode("utf-8"))
        except Exception as e:
            print(f"[ThemeStyler] CSS load error: {e}")
