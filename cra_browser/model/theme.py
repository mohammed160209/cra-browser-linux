"""Space theme and color models for Cra Browser Linux."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


def hex_to_rgb(hex_str: str) -> Optional[Tuple[float, float, float]]:
    """Convert hex string (e.g. '#1C242B') to (r, g, b) in 0..1."""
    s = hex_str.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        return None
    try:
        val = int(s, 16)
        return (
            ((val >> 16) & 0xFF) / 255.0,
            ((val >> 8) & 0xFF) / 255.0,
            (val & 0xFF) / 255.0,
        )
    except ValueError:
        return None


def hex_luminance(hex_str: str) -> float:
    """Calculate relative luminance of a hex color."""
    rgb = hex_to_rgb(hex_str)
    if not rgb:
        return 0.5
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


@dataclass
class SpaceTheme:
    """Theme configuration for a Space."""
    colors: List[str] = field(default_factory=lambda: ["#1C242B", "#3A3660"])
    intensity: float = 0.85
    noise: float = 0.18
    appearance: str = "dark"  # "dark" | "light" | "auto"
    vibrant: bool = False
    accent: Optional[str] = None
    solid: bool = False

    @property
    def is_dark(self) -> bool:
        if self.appearance == "dark":
            return True
        if self.appearance == "light":
            return False
        if self.colors:
            return hex_luminance(self.colors[0]) < 0.45
        return True

    def to_dict(self) -> dict:
        return {
            "colors": self.colors,
            "intensity": self.intensity,
            "noise": self.noise,
            "appearance": self.appearance,
            "vibrant": self.vibrant,
            "accent": self.accent,
            "solid": self.solid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SpaceTheme:
        return cls(
            colors=data.get("colors", ["#1C242B", "#3A3660"]),
            intensity=data.get("intensity", 0.85),
            noise=data.get("noise", 0.18),
            appearance=data.get("appearance", "dark"),
            vibrant=data.get("vibrant", False),
            accent=data.get("accent"),
            solid=data.get("solid", False),
        )

    def to_css_gradient(self) -> str:
        """Generate a CSS linear gradient representing the theme."""
        if not self.colors:
            return "linear-gradient(180deg, #1C242B 0%, #3A3660 100%)"
        if len(self.colors) == 1 or self.solid:
            return self.colors[0]
        return f"linear-gradient(160deg, {self.colors[0]} 0%, {self.colors[1]} 100%)"


# Built-in Space Theme Presets matching Cra / Arc
THEME_PRESETS: List[Tuple[str, SpaceTheme]] = [
    ("Ink", SpaceTheme(colors=["#1C242B", "#3A3660"], intensity=0.85, appearance="dark")),
    ("Phantom", SpaceTheme(colors=["#181818", "#262626"], intensity=0.9, appearance="dark")),
    ("Wall", SpaceTheme(colors=["#1C1712", "#2E2620"], intensity=0.9, appearance="dark")),
    ("Moss", SpaceTheme(colors=["#0F2420", "#2F6F5E"], intensity=0.75, appearance="dark")),
    ("Ember", SpaceTheme(colors=["#2A1A14", "#A2481D"], intensity=0.7, appearance="dark")),
    ("Gold", SpaceTheme(colors=["#2A2310", "#7A5C0F"], intensity=0.75, appearance="dark")),
    ("Brand", SpaceTheme(colors=["#241C3A", "#6944AE"], intensity=0.75, appearance="dark")),
    ("Parchment", SpaceTheme(colors=["#F4F1EA", "#E6DCC8"], intensity=0.6, appearance="light")),
    ("Light Sun", SpaceTheme(colors=["#F8D558", "#A4F554"], intensity=0.45, appearance="light")),
    ("Sunset", SpaceTheme(colors=["#C7CAFF", "#FFE5E5"], intensity=0.5, appearance="light")),
]
