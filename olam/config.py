"""Where Olam keeps things and how it runs. Every setting is an environment variable, and any of them can also go in
olam.env in the data folder (see olam.env.example)."""
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
LESSONS = ROOT / "lessons"

DATA = Path(os.environ.get("OLAM_DATA", str(ROOT / "data")))

# The settings file, so the service and the command line see the same settings. Never read by the demo.
if os.environ.get("OLAM_DEMO") != "1" and (DATA / "olam.env").exists():
    for _line in (DATA / "olam.env").read_text().splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
DB = Path(os.environ.get("OLAM_DB", str(DATA / "olam.db")))

# The public demo (OLAM_DEMO=1): no login, only open-licensed sources, no Calibre books, no vault, no AI,
# and each visitor's progress kept in their own browser.
DEMO = os.environ.get("OLAM_DEMO") == "1"
ZIM_DIR = DATA / "zim"
SRD_PDF = DATA / "srd" / "SRD_CC_v5.2.1.pdf"
OPEN5E = DATA / "open5e" / "repo" / "data" / "v2"
AUTH_FILE = DATA / "auth.json"

# A Calibre library (the folder with metadata.db): read only, never written. Empty means none.
CALIBRE = Path(os.environ["OLAM_CALIBRE"]) if os.environ.get("OLAM_CALIBRE") else None

# The Obsidian vault for lesson notes and the world. Empty means none yet.
VAULT = Path(os.environ["OLAM_VAULT"]) if os.environ.get("OLAM_VAULT") else None

# kiwix-serve, for reading the ZIM files in full: its address, e.g. http://localhost:8461. Empty means none.
# "Open in Kiwix" shows only when Olam is opened on the same host name.
KIWIX_URL = os.environ.get("OLAM_KIWIX_URL", "").rstrip("/")

# The addresses to listen on (comma-separated; 0.0.0.0 in a container) and the port.
HOSTS = [h for h in os.environ.get("OLAM_HOSTS", "127.0.0.1").split(",") if h]
PORT = int(os.environ.get("OLAM_PORT", "8462"))
# Olam's own address, for the links it writes into vault notes.
URL = os.environ.get("OLAM_URL", "").rstrip("/") or f"http://{'localhost' if HOSTS[-1] in ('0.0.0.0', '127.0.0.1') else HOSTS[-1]}:{PORT}"

# The AI features (Ask, Summary, the Game Master, interviews) use the Claude API when there's a key, and otherwise
# the Claude CLI signed in to a Claude subscription. With neither, they're off.
API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or ""
CLAUDE = os.environ.get("OLAM_CLAUDE") or shutil.which("claude") or str(Path.home() / ".local/bin/claude")
MODEL = os.environ.get("OLAM_MODEL", "claude-sonnet-5-5")
AI = not DEMO and os.environ.get("OLAM_AI", "1") != "0" and bool(API_KEY or Path(CLAUDE).exists())

# What each ZIM is, by file-name prefix: its shelf (how far to trust it) and how to show it.
ZIMS = {
    "rpg.stackexchange.com": {"shelf": "expert", "label": "RPG Stack Exchange", "license": "CC BY-SA", "kind": "qa"},
    "mythology.stackexchange.com": {"shelf": "expert", "label": "Mythology Q&A", "license": "CC BY-SA", "kind": "qa", "group": "myth"},
    "worldbuilding.stackexchange.com": {"shelf": "craft", "label": "Worldbuilding Q&A", "license": "CC BY-SA", "kind": "qa"},
    "dandwiki": {"shelf": "idea", "label": "D&D Wiki", "license": "GFDL", "kind": "wiki", "note": "homebrew, not official"},
}

# Calibre books whose metadata is wrong, or that need a shelf other than "idea": books.json in the data folder,
# {"<calibre book id>": {"title", "author", "shelf", "edition", "note"}}, every key optional.
try:
    BOOKS = {int(k): v for k, v in json.loads((DATA / "books.json").read_text()).items()}
except (FileNotFoundError, ValueError):
    BOOKS = {}
