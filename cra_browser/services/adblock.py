"""Content blocking and anti-tracking service using WebKit UserContentFilter."""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Optional, Callable, List

try:
    import gi
    gi.require_version("WebKit", "6.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import WebKit, GLib
    HAS_WEBKIT = True
except (ImportError, ValueError):
    HAS_WEBKIT = False
    WebKit = None
    GLib = None


def compile_blocklist_rules(domains: List[str], batch_size: int = 4000) -> List[dict]:
    """Compile a list of domain strings into WebKit UserContentFilter JSON rule dictionaries."""
    rules = []
    for i in range(0, len(domains), batch_size):
        chunk = domains[i : i + batch_size]
        rules.append({
            "trigger": {
                "url-filter": ".*",
                "if-domain": [f"*{d}" if not d.startswith("*") else d for d in chunk],
            },
            "action": {"type": "block"},
        })
    return rules


class AdblockService:
    """Manages compilation and attachment of domain blocklists in WebKitGTK."""

    def __init__(self, blocklist_path: Optional[Path] = None):
        if blocklist_path and blocklist_path.exists():
            self.blocklist_path = blocklist_path
        else:
            pkg_data = Path(__file__).parent.parent.parent / "data" / "blocklist" / "domains.txt"
            if pkg_data.exists():
                self.blocklist_path = pkg_data
            else:
                self.blocklist_path = Path("/usr/share/cra-browser/blocklist/domains.txt")

        cache_base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        self.store_dir = cache_base / "cra-browser" / "filters"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.filter_identifier = "cra_tracker_blocker_v1"
        self.compiled_filter = None

        if HAS_WEBKIT and WebKit:
            self.store = WebKit.UserContentFilterStore.new(str(self.store_dir))
        else:
            self.store = None

    def initialize(self, on_ready: Optional[Callable[[], None]] = None):
        """Load or compile the blocklist asynchronously."""
        if not HAS_WEBKIT or not self.store:
            if on_ready:
                on_ready()
            return

        def on_loaded(source, res):
            try:
                self.compiled_filter = source.load_finish(res)
                if on_ready:
                    on_ready()
            except GLib.Error:
                # Need to compile from domains.txt
                self._compile_rules(on_ready)

        self.store.load(self.filter_identifier, None, on_loaded)

    def _compile_rules(self, on_ready: Optional[Callable[[], None]] = None):
        if not self.blocklist_path.exists() or not self.store:
            if on_ready:
                on_ready()
            return

        try:
            with open(self.blocklist_path, "r", encoding="utf-8") as f:
                domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        except Exception as e:
            print(f"[Adblock] Failed to read blocklist: {e}")
            if on_ready:
                on_ready()
            return

        rules = compile_blocklist_rules(domains)
        rules_json = json.dumps(rules)
        bytes_data = GLib.Bytes.new(rules_json.encode("utf-8"))

        def on_saved(source, res):
            try:
                self.compiled_filter = source.save_finish(res)
                print(f"[Adblock] Compiled {len(domains)} tracker domains successfully.")
            except Exception as e:
                print(f"[Adblock] Failed to compile rules: {e}")
            if on_ready:
                on_ready()

        self.store.save(self.filter_identifier, bytes_data, None, on_saved)

    def attach_to_manager(self, manager):
        """Attach the active filter to a WebKit UserContentManager."""
        if self.compiled_filter and manager:
            manager.add_filter(self.compiled_filter)
