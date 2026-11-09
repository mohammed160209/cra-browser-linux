"""Tests for cra_browser.services.adblock."""

from cra_browser.services.adblock import compile_blocklist_rules


def test_compile_blocklist_rules():
    sample_domains = [
        "ads.example.com",
        "telemetry.tracker.net",
        "analytics.google.com",
        "*doubleclick.net",
    ]
    rules = compile_blocklist_rules(sample_domains, batch_size=2)
    assert len(rules) == 2  # 4 domains split into batches of 2

    r0 = rules[0]
    assert r0["trigger"]["url-filter"] == ".*"
    assert "*ads.example.com" in r0["trigger"]["if-domain"]
    assert "*telemetry.tracker.net" in r0["trigger"]["if-domain"]
    assert r0["action"]["type"] == "block"

    r1 = rules[1]
    assert "*doubleclick.net" in r1["trigger"]["if-domain"]
