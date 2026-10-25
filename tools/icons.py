#!/usr/bin/env python3
"""Build web/icons.svg, the sprite of every icon Olam uses (olam/icons.py), from a checkout of game-icons.net's SVGs.

    git clone --depth 1 https://github.com/game-icons/icons.git /tmp/game-icons
    tools/icons.py /tmp/game-icons

Each icon loses its black square and takes the text colour. The author of each one goes in a comment and in
web/icons.json, for the credits. The icons are CC BY 3.0 (a few CC0), by the artists named in game-icons' license.txt.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from olam import icons  # noqa: E402


def main(src):
    src = Path(src)
    files = {p.stem: p for p in sorted(src.glob("*/**/*.svg"))}
    out, authors, missing = [], {}, []
    for name in icons.every():
        p = files.get(name)
        if not p:
            missing.append(name)
            continue
        svg = p.read_text()
        paths = re.findall(r"<path[^>]*/>", svg)
        paths = [x for x in paths if not re.search(r'd="M0 0h512v512H0z"', x)]
        paths = [re.sub(r'\s*fill="[^"]*"', "", x) for x in paths]
        author = p.relative_to(src).parts[0]
        authors[name] = author
        out.append(f'<symbol id="gi-{name}" viewBox="0 0 512 512"><!-- {author} -->{"".join(paths)}</symbol>')
    if missing:
        sys.exit("Not in the icon set: " + ", ".join(missing))
    (ROOT / "web" / "icons.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">\n<!-- From game-icons.net, CC BY 3.0: '
        + ", ".join(sorted(set(authors.values()))) + " -->\n" + "\n".join(out) + "\n</svg>\n")
    (ROOT / "web" / "icons.json").write_text(json.dumps(authors, indent=1, sort_keys=True) + "\n")
    print(f"{len(out)} icons by {len(set(authors.values()))} artists")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/game-icons")
