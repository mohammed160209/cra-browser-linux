"""Tests for cra_browser.model.theme."""

from cra_browser.model.theme import (
    hex_to_rgb,
    hex_luminance,
    SpaceTheme,
    THEME_PRESETS,
)


def test_hex_to_rgb():
    assert hex_to_rgb("#FFFFFF") == (1.0, 1.0, 1.0)
    assert hex_to_rgb("#000000") == (0.0, 0.0, 0.0)
    rgb = hex_to_rgb("#1C242B")
    assert rgb is not None
    assert 0.0 <= rgb[0] <= 1.0
    assert 0.0 <= rgb[1] <= 1.0
    assert 0.0 <= rgb[2] <= 1.0

    assert hex_to_rgb("invalid") is None


def test_hex_luminance():
    assert hex_luminance("#FFFFFF") > 0.95
    assert hex_luminance("#000000") < 0.05
    assert hex_luminance("#F8D558") > hex_luminance("#1C242B")


def test_space_theme_gradient():
    theme = SpaceTheme(colors=["#1C242B", "#3A3660"], appearance="dark")
    assert theme.is_dark
    grad = theme.to_css_gradient()
    assert "linear-gradient" in grad
    assert "#1C242B" in grad
    assert "#3A3660" in grad

    light_theme = SpaceTheme(colors=["#F4F1EA", "#E6DCC8"], appearance="light")
    assert not light_theme.is_dark


def test_theme_presets():
    preset_names = [p[0] for p in THEME_PRESETS]
    expected = ["Ink", "Phantom", "Wall", "Moss", "Ember", "Gold", "Brand", "Parchment", "Light Sun", "Sunset"]
    for exp in expected:
        assert exp in preset_names
