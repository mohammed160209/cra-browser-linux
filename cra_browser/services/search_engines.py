"""Search engines and smart URL resolution for Cra Browser Linux."""

from __future__ import annotations
import re
from urllib.parse import quote_plus


SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Brave": "https://search.brave.com/search?q={}",
    "Kagi": "https://kagi.com/search?q={}",
    "Bing": "https://www.bing.com/search?q={}",
    "Ecosia": "https://www.ecosia.org/search?q={}",
}

TLD_REGEX = re.compile(
    r"^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d+)?(\/.*)?$"
)
IP_REGEX = re.compile(r"^(https?:\/\/)?(\d{1,3}\.){3}\d{1,3}(:\d+)?(\/.*)?$")
LOCALHOST_REGEX = re.compile(r"^(https?:\/\/)?localhost(:\d+)?(\/.*)?$")


def is_url(text: str) -> bool:
    """Determine whether the input string is a URL rather than a search query."""
    text = text.strip()
    if not text:
        return False
    if " " in text:
        return False
    if text.startswith("http://") or text.startswith("https://") or text.startswith("file://") or text.startswith("about:"):
        return True
    if LOCALHOST_REGEX.match(text) or IP_REGEX.match(text):
        return True
    if TLD_REGEX.match(text):
        return True
    return False


def resolve_input(text: str, engine_name: str = "DuckDuckGo") -> str:
    """Resolve user input from the Command Bar or address bar to a navigable URL."""
    text = text.strip()
    if not text:
        return "about:blank"
    if is_url(text):
        if not (text.startswith("http://") or text.startswith("https://") or text.startswith("file://") or text.startswith("about:")):
            return f"https://{text}"
        return text
    template = SEARCH_ENGINES.get(engine_name, SEARCH_ENGINES["DuckDuckGo"])
    return template.format(quote_plus(text))
