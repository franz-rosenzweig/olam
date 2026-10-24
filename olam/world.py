"""The world as the vault holds it, for the Map, People and Table screens.

Places are notes in the map's marker folder (World/Places) with `location: [lat, long]`, which the Leaflet plugin also reads.
People are notes in World/People: frontmatter for role, home and Relations ties, and a body with **Wants:**-style lines,
"## Known to the party" and "## Secrets". Encounters are notes in World/Encounters with an Initiative Tracker
```encounter``` block, and the party is World/Party.md. Edits change only the lines they need, so a note stays as it was written.
"""
import re
from datetime import date
from pathlib import Path

import yaml

from . import config, db, library

MAP_NOTE = "World/Maps/World map.md"
PLACES = "World/Places"
PEOPLE = "World/People"
ENCOUNTERS = "World/Encounters"
PARTY = "World/Party.md"
TIES = ["ally", "enemy", "family", "friend", "rival", "spouse", "lover", "mentor", "parent"]
FACTS = ["Wants", "Fears", "Secret", "Voice"]
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
FM = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


# ---------- reading and writing notes ----------

def root():
    if not (config.VAULT and config.VAULT.exists()):
        raise RuntimeError("No vault set")
    return config.VAULT


def path_of(rel):
    """A path inside the vault, or an error: nothing outside it is ever read or written."""
    p = (root() / rel).resolve()
    if root().resolve() not in p.parents:
        raise ValueError("Outside the vault")
    return p


def rel_of(p):
    return str(Path(p).relative_to(root()))


def read(rel):
    text = path_of(rel).read_text()
    m = FM.match(text)
    fm = {}
    if m:
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
    return (fm if isinstance(fm, dict) else {}), (text[m.end():] if m else text), text


def set_key(rel, key, value):
    """Set one frontmatter key, touching only its line(s). value is written as YAML flow (one line)."""
    p = path_of(rel)
    text = p.read_text()
    line = f"{key}: " + yq(value)
    m = FM.match(text)
    if not m:
        p.write_text(f"---\n{line}\n---\n{text}")
        return
    fm = m.group(1).split("\n")
    out, i, done = [], 0, False
    while i < len(fm):
        if re.match(rf"^{re.escape(key)}\s*:", fm[i]):
            i += 1
            while i < len(fm) and (fm[i].startswith((" ", "\t", "-")) and not re.match(r"^[\w-]+\s*:", fm[i])):
                i += 1                                      # the old value's continuation lines
            out.append(line)
            done = True
            continue
        out.append(fm[i])
        i += 1
    if not done:
        out.append(line)
    p.write_text("---\n" + "\n".join(out) + "\n---\n" + text[m.end():])


def first(v):
    """YAML reads `image: [[World map.png]]` as a list inside a list: the first string inside."""
    while isinstance(v, list) and v:
        v = v[0]
    return link_name(v) if isinstance(v, str) else ""


def link_name(v):
    """'[[Brinehold|the port]]' -> 'Brinehold'; plain strings pass through."""
    if not isinstance(v, str):
        return ""
    m = re.match(r"^\s*\[\[([^\]|#]+)", v)
    return (m.group(1) if m else v).strip()


def index():
    """Every note and image in the vault by name, for resolving [[links]]."""
    out = {}
    for p in root().rglob("*"):
        if ".obsidian" in p.parts or ".trash" in p.parts or not p.is_file():
            continue
        if p.suffix == ".md":
            out.setdefault(p.stem.lower(), rel_of(p))
        elif p.suffix.lower() in IMAGES:
            out.setdefault(p.name.lower(), rel_of(p))
    return out


def resolve(name, idx=None):
    idx = idx if idx is not None else index()
    n = link_name(name).lower()
    return idx.get(n) or idx.get(n + ".md") or ""


def excerpt(body, n=220):
    for para in re.split(r"\n\s*\n", body):
        t = para.strip()
        if t and not t.startswith(("#", "```", ">", "-", "|", "**")):
            t = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda m: m.group(2) or m.group(1), t)
            return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"
    return ""


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", s or "").strip()[:80]


def new_note(folder, name, text):
    name = safe_name(name)
    if not name:
        raise ValueError("A name is needed")
    p = path_of(f"{folder}/{name}.md")
    if p.exists():
        raise FileExistsError(f"{folder}/{name}.md already exists")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return rel_of(p)


def yq(s):
    return yaml.safe_dump(s, default_flow_style=True, allow_unicode=True, width=10000, sort_keys=False).strip().removesuffix("\n...")


# ---------- the map ----------

def map_info():
    """The world map: its image, its bounds (written into the note if missing) and the places on it."""
    rel = MAP_NOTE
    p = path_of(rel)
    if not p.exists():
        raise FileNotFoundError("No world map yet")
    text = p.read_text()
    block = re.search(r"```leaflet\n(.*?)```", text, re.S)
    opts = yaml.safe_load(block.group(1)) if block else {}
    img = resolve(first(opts.get("image")))
    w = h = 0
    if img:
        from PIL import Image
        with Image.open(path_of(img)) as im:
            w, h = im.size
    bounds = opts.get("bounds")
    if not (isinstance(bounds, list) and len(bounds) == 2) and w and h:
        bounds = [[100, 0], [0, round(100 * w / h, 2)]]
        text = text.replace("```leaflet\n", f"```leaflet\nbounds:\n  - {yq(bounds[0])}\n  - {yq(bounds[1])}\n", 1)
        p.write_text(text)
    (top, left), (bottom, right) = bounds if bounds else ([100, 0], [0, 160])
    folder = first(opts.get("markerFolder")) or PLACES
    return {"note": rel, "image": img, "width": w, "height": h, "bounds": {"top": top, "left": left, "bottom": bottom, "right": right},
            "folder": str(folder).strip("/"), "places": places(str(folder).strip("/"))}


def places(folder=PLACES):
    base = path_of(folder)
    if not base.exists():
        return []
    idx = index()
    homes = {}
    for pr in people(idx):
        if pr["home"]:
            homes.setdefault(pr["home"].lower(), []).append({"name": pr["name"], "rel": pr["rel"]})
    out = []
    for p in sorted(base.rglob("*.md")):
        fm, body, _ = read(rel_of(p))
        loc = fm.get("location")
        if not (isinstance(loc, list) and len(loc) == 2):
            loc = None
        out.append({"name": p.stem, "rel": rel_of(p), "location": loc, "type": str(fm.get("type") or ""),
                    "visited": bool(fm.get("visited")), "dm_only": bool(fm.get("dm-only")),
                    "excerpt": excerpt(body), "people": homes.get(p.stem.lower(), [])})
    return out


def place_create(name, kind, location):
    loc = [round(float(location[0]), 2), round(float(location[1]), 2)]
    text = (f"---\ntags: [place]\ntype: {yq(kind or 'Place')}\nlocation: {yq(loc)}\nvisited: false\ndm-only: false\n---\n\n"
            "**What's here:**\n**Who's here:**\n**A secret:**\n")
    return new_note(PLACES, name, text)


def place_set(rel, key, value):
    if not rel.startswith(PLACES + "/") or key not in ("location", "visited", "dm-only", "type"):
        raise ValueError("Not a place setting")
    if key == "location":
        value = [round(float(value[0]), 2), round(float(value[1]), 2)]
    set_key(rel, key, value)


# ---------- people ----------

def people(idx=None):
    base = path_of(PEOPLE)
    if not base.exists():
        return []
    idx = idx if idx is not None else index()
    out = []
    for p in sorted(base.rglob("*.md")):
        fm, body, _ = read(rel_of(p))
        ties = sum(len(v) if isinstance(v, list) else (1 if v else 0) for k, v in fm.items() if k in TIES)
        img = resolve(str(fm.get("npcimage") or ""), idx) if fm.get("npcimage") else ""
        out.append({"name": p.stem, "rel": rel_of(p), "role": str(fm.get("role") or ""), "home": link_name(fm.get("home") or ""),
                    "image": img, "ties": ties, "excerpt": excerpt(body)})
    return out


def sections(body):
    """The note body split at its ## headings: {heading: text}, with the text before any heading under ''."""
    out, cur, buf = {}, "", []
    for line in body.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    out[cur] = "\n".join(buf).strip()
    return out


def bullets(text):
    return [re.sub(r"^\s*[-*]\s+", "", l).strip() for l in (text or "").split("\n") if re.match(r"^\s*[-*]\s+\S", l)]


def person(rel):
    if not rel.startswith(PEOPLE + "/"):
        raise ValueError("Not a person")
    fm, body, _ = read(rel)
    idx = index()
    sec = sections(body)
    facts = []
    rest = []
    for line in sec.get("", "").split("\n"):
        m = re.match(r"^\*\*(\w[\w ]*?):\*\*\s*(.*)$", line.strip())
        if m:
            facts.append({"k": m.group(1), "v": m.group(2)})
        elif not line.strip().startswith("```") and "relations" not in line and line.strip() not in ("size: small",):
            rest.append(line)
    ties = []
    for k in TIES:
        v = fm.get(k)
        for n in (v if isinstance(v, list) else ([v] if v else [])):
            name = link_name(n)
            if name:
                ties.append({"type": k, "name": name, "rel": resolve(name, idx)})
    name = Path(rel).stem
    appears = []
    for p in sorted(path_of("World").rglob("*.md")):
        r = rel_of(p)
        if r != rel and not r.startswith(PEOPLE + "/") and f"[[{name}" in p.read_text():
            appears.append({"name": p.stem, "rel": r})
    home = link_name(fm.get("home") or "")
    return {"name": name, "rel": rel, "role": str(fm.get("role") or ""), "home": home, "home_rel": resolve(home, idx) if home else "",
            "image": resolve(str(fm.get("npcimage") or ""), idx) if fm.get("npcimage") else "",
            "facts": facts, "known": bullets(sec.get("Known to the party")), "secrets": bullets(sec.get("Secrets")),
            "notes": "\n".join(rest).strip(), "ties": ties, "appears": appears[:20],
            "details": bullets(sec.get("Details")),
            "extra": {k: v for k, v in sec.items() if k not in ("", "Known to the party", "Secrets", "Details")}}


def person_create(name, role="", home=""):
    text = (f"---\ntags: [npc]\nrole: {yq(role or '')}\nhome: {yq(f'[[{home}]]' if home else '')}\nnpcimage:\n"
            + "".join(f"{k}: []\n" for k in ("ally", "enemy", "family", "friend", "rival", "mentor"))
            + "---\n\n```relations\nsize: small\n```\n\n**Wants:**\n**Fears:**\n**Secret:**\n**Voice:**\n\n"
            "## Known to the party\n\n\n## Secrets\n\n")
    return new_note(PEOPLE, name, text)


def person_reveal(rel, i):
    """Move one bullet from ## Secrets to ## Known to the party, marked with today's date."""
    if not rel.startswith(PEOPLE + "/"):
        raise ValueError("Not a person")
    p = path_of(rel)
    lines = p.read_text().split("\n")
    head = lambda t: next((k for k, l in enumerate(lines) if re.match(rf"^##\s+{t}\s*$", l)), None)
    s = head("Secrets")
    if s is None:
        raise ValueError("No secrets")
    found, n = None, -1
    for k in range(s + 1, len(lines)):
        if lines[k].startswith("## "):
            break
        if re.match(r"^\s*[-*]\s+\S", lines[k]):
            n += 1
            if n == i:
                found = k
                break
    if found is None:
        raise IndexError("No such secret")
    item = re.sub(r"^\s*[-*]\s+", "", lines.pop(found)).strip()
    entry = f"- {item} (revealed {date.today().isoformat()})"
    kn = head("Known to the party")
    if kn is None:
        lines += ["", "## Known to the party", "", entry]
    else:
        k = kn + 1
        while k < len(lines) and not lines[k].startswith("## ") and (re.match(r"^\s*[-*]\s+", lines[k]) or not lines[k].strip()):
            if not lines[k].strip() and k + 1 < len(lines) and not re.match(r"^\s*[-*]\s+", lines[k + 1]):
                break
            k += 1
        while k > kn + 1 and not lines[k - 1].strip():
            k -= 1
        lines.insert(k, entry)
    p.write_text("\n".join(lines))
    return person(rel)


def person_add(rel, where, text):
    """Add a bullet under ## Secrets or ## Known to the party (made if missing)."""
    if not rel.startswith(PEOPLE + "/") or where not in ("Secrets", "Known to the party", "Details"):
        raise ValueError("No such section")
    p = path_of(rel)
    lines = p.read_text().rstrip("\n").split("\n")
    h = next((k for k, l in enumerate(lines) if re.match(rf"^##\s+{where}\s*$", l)), None)
    entry = "- " + " ".join(text.split())[:500]
    if h is None:
        lines += ["", f"## {where}", "", entry]
    else:
        k = h + 1
        while k < len(lines) and not lines[k].startswith("## "):
            k += 1
        while k > h + 1 and not lines[k - 1].strip():
            k -= 1
        lines.insert(k, entry)
    p.write_text("\n".join(lines) + "\n")
    return person(rel)


# ---------- encounters, the party, the table ----------

def encounter_notes():
    base = path_of(ENCOUNTERS)
    out = []
    if base.exists():
        for p in sorted(base.rglob("*.md")):
            t = p.read_text()
            if "```encounter" in t:
                out.append({"name": p.stem, "rel": rel_of(p), "creatures": parse_encounter(t)})
    return out


def creature_stats(name):
    """HP, AC, initiative and XP for a creature named in an encounter: its bestiary note, then the 2024 rules."""
    from . import vault
    idx = index()
    r = idx.get(name.lower())
    e = None
    if r:
        fm, body, _ = read(r)
        if fm.get("olam"):
            e = library.get(fm["olam"])
        else:
            m = re.search(r"```statblock\n(.*?)```", body, re.S)
            if m:
                try:
                    sb = yaml.safe_load(m.group(1)) or {}
                except yaml.YAMLError:
                    sb = {}
                stats = sb.get("stats") or [10, 10, 10, 10, 10, 10]
                return {"hp": int(sb.get("hp") or 1), "ac": int(str(sb.get("ac") or 10).split()[0]),
                        "init": (int(stats[1]) - 10) // 2, "xp": vault.XP.get(str(sb.get("cr", "")), 0), "note": r, "id": ""}
    if not e:
        row = db.connect().execute("SELECT id FROM entries WHERE kind='monster' AND doc='srd-2024' AND name=? COLLATE NOCASE",
                                   (re.sub(r"\s*\(.*\)$", "", name),)).fetchone()
        e = library.get(row[0]) if row else None
    if not e:
        return {"hp": 0, "ac": 0, "init": 0, "xp": 0, "note": r or "", "id": ""}
    d = e.get("data") or {}
    return {"hp": d.get("hp") or 1, "ac": d.get("ac") or 10,
            "init": d.get("initiative") if d.get("initiative") is not None else (d["abilities"][1]["score"] - 10) // 2,
            "xp": d.get("xp") or vault.XP.get(str(d.get("cr", "")), 0), "note": r or "", "id": e["id"]}


def parse_encounter(text):
    """The creatures of the first ```encounter``` block: [{n, name, hp, ac, init, xp, id, note}]."""
    m = re.search(r"```encounter\n(.*?)```", text, re.S)
    if not m:
        return []
    try:
        block = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return []
    out = []
    for c in block.get("creatures") or []:
        n, spec = 1, c
        if isinstance(c, dict) and len(c) == 1:
            (k, spec), = c.items()
            n = int(k) if str(k).isdigit() else 1
        if isinstance(spec, list):
            spec = ", ".join(str(x) for x in spec)
        if not isinstance(spec, str):
            continue
        name_m = re.match(r'^\s*\[\["?([^"\]]+)"?\]\]\s*,?\s*(.*)$', spec)
        if name_m:
            name, rest = name_m.group(1), name_m.group(2)
        else:
            name, _, rest = spec.partition(",")
        nums = [int(x) for x in re.findall(r"-?\d+", rest)]
        st = creature_stats(name.strip())
        hp, ac, ini, xp = (nums + [None] * 4)[:4]
        out.append({"n": n, "name": name.strip(), "hp": hp if hp is not None else st["hp"], "ac": ac if ac is not None else st["ac"],
                    "init": ini if ini is not None else st["init"], "xp": xp if xp is not None else st["xp"],
                    "id": st["id"], "note": st["note"]})
    return out


def party():
    p = path_of(PARTY)
    if not p.exists():
        return []
    fm, _, _ = read(PARTY)
    out = []
    for m in fm.get("party") or []:
        if isinstance(m, dict) and m.get("name"):
            out.append({"name": str(m["name"]), "hp": int(m.get("hp") or 10), "ac": int(m.get("ac") or 10), "init": int(m.get("init") or 0)})
    return out


def party_save(members):
    clean = [{"name": safe_name(str(m.get("name", ""))), "hp": int(m.get("hp") or 10), "ac": int(m.get("ac") or 10),
              "init": int(m.get("init") or 0)} for m in members if safe_name(str(m.get("name", "")))][:12]
    p = path_of(PARTY)
    if not p.exists():
        p.write_text("---\ntags: [party]\nparty: []\n---\n\nThe adventurers. Olam's Table reads this list.\n")
    set_key(PARTY, "party", clean)
    return party()


def table_get():
    return db.cache_get("table") or {}


def table_put(state):
    state = state if isinstance(state, dict) else {}
    state["v"] = int(table_get().get("v") or 0) + 1
    db.cache_put("table", state)
    return state


def table_end(state):
    """Write how the fight went under ## Results in its encounter note, then clear the table."""
    rel = state.get("encounter")
    lines = []
    if rel and rel.startswith(ENCOUNTERS + "/") and path_of(rel).exists():
        fallen = [c["name"] for c in state.get("combatants", []) if c.get("kind") == "foe" and int(c.get("hp", 1)) <= 0]
        standing = [f"{c['name']} {c.get('hp')}/{c.get('max')}" for c in state.get("combatants", []) if c.get("kind") == "pc"]
        lines = [f"- {date.today().isoformat()}: {state.get('round', 1)} rounds."
                 + (f" Defeated: {', '.join(fallen)}." if fallen else "")
                 + (f" The party: {', '.join(standing)}." if standing else "")]
        p = path_of(rel)
        t = p.read_text().rstrip("\n")
        t += ("\n\n## Results\n\n" if "## Results" not in t else "\n") + "\n".join(lines) + "\n"
        p.write_text(t)
    db.cache_put("table", {"v": int(table_get().get("v") or 0) + 1})
    return {"written": lines, "note": rel}
