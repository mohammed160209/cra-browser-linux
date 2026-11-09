"""Tests for CommandBar fuzzy matching and ranking."""

from cra_browser.ui.command_bar import fuzzy_score


def test_fuzzy_score():
    assert fuzzy_score("github", "github") == 100
    assert fuzzy_score("git", "github.com") == 80
    assert fuzzy_score("hub", "github.com") > 0
    assert fuzzy_score("cbl", "cra browser linux") == 20
    assert fuzzy_score("xyz", "github.com") == 0
