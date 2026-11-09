#!/usr/bin/env bash
set -euo pipefail

browser=$1
output=$2
mkdir -p "$output"
export XDG_DATA_HOME
XDG_DATA_HOME=$(mktemp -d)
trap 'if [[ -n ${browser_pid:-} ]]; then kill "$browser_pid" 2>/dev/null || true; wait "$browser_pid" 2>/dev/null || true; fi; rm -rf "$XDG_DATA_HOME"' EXIT

python3 - <<'PY'
import json
import os
import time
from html import escape
from pathlib import Path

directory = Path(os.environ["XDG_DATA_HOME"])
profile = directory / "cra-browser-cef"
profile.mkdir()
entries = [
    (1, "A calmer way to browse", "", False, True),
    (2, "Design reference", "", True, True),
    (3, "Research notes", "Launch", False, True),
    (4, "Ideas", "Launch", False, True),
    (5, "Reading list", "", False, False),
    (6, "Release notes", "", False, False),
    (7, "Documentation", "", True, True),
    (8, "Bookmarks", "", True, True),
    (9, "Project", "", True, True),
]
tabs = []
for id, title, folder, favorite, pinned in entries:
    page = directory / f"page-{id}.html"
    page.write_text(f"""<!doctype html><html><head><meta charset="utf-8">
<title>{escape(title)}</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(ellipse at 70% 26%,#414bc6,#171a72 75%);color:#fff;font:17px system-ui;min-height:100vh;display:grid;place-items:center;text-align:center}}
main{{max-width:620px;padding:50px}}span{{display:inline-block;padding:10px 19px;border-radius:24px;background:#f5f4ff;color:#24265c;font-weight:650}}h1{{font-size:54px;letter-spacing:-.055em;line-height:1.03;margin:26px 0 18px}}p{{color:#dddeff}}
</style></head><body><main><span>Cra</span><h1>{escape(title)}</h1><p>Spaces, favorites, and a sidebar built for browsing.</p></main></body></html>""")
    url = page.as_uri()
    tabs.append(dict(id=id, space="Studio", title=title, url=url,
                     home=url if pinned else "", folder=folder,
                     favorite=favorite, visited=time.time()))
(profile / "session.json").write_text(json.dumps(
    dict(version=1, space="Studio", spaces=["Studio", "Personal"],
         selected=1, tabs=tabs, archive=[])))
PY

"$browser" --no-sandbox --disable-gpu --disable-background-networking   --disable-component-update >"$output/chrome-ui.log" 2>&1 &
browser_pid=$!
windows=$(timeout 25 xdotool search --sync --onlyvisible --name '^Cra$')
window=${windows%%$'\n'*}
xdotool windowfocus --sync "$window"
sleep 1
import -window root "$output/sidebar.png"
xdotool key --clearmodifiers ctrl+t
sleep 0.4
xdotool type --clearmodifiers 'Release notes'
sleep 0.4
import -window root "$output/command-bar.png"
xdotool key Down Return

for attempt in {1..30}; do
  if python3 - "$XDG_DATA_HOME/cra-browser-cef/session.json" <<'PY'
import json
import sys
from pathlib import Path
session = json.loads(Path(sys.argv[1]).read_text())
sys.exit(session["selected"] != 6 or len(session["tabs"]) != 9)
PY
  then
    echo "The command bar switched to an existing tab without creating a duplicate."
    exit 0
  fi
  sleep 0.25
done
cat "$output/chrome-ui.log" >&2
echo "The command bar did not switch to the existing tab." >&2
exit 1
