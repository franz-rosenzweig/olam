"""Notes Olam writes into the Obsidian vault, in the formats of the vault's TTRPG plugins:

- Fantasy Statblocks: a monster note with a ```statblock``` block (World/Bestiary).
- Initiative Tracker: an ```encounter``` block whose lines are "count: name, HP, AC, initiative, XP" (World/Encounters).
- Dice Roller: `dice:` lines, e.g. `dice: 2d20kh+5` for an attack with advantage (lesson notes).
- Leaflet: the world map note, with a marker for every note in World/Places that has `location:` in its frontmatter.
- Calendarium: session notes date themselves with `fc-date` (the Session template).
- Relations: NPC notes name their ties in frontmatter (ally, enemy, family, friend, rival, mentor).

Olam only ever creates notes; it never overwrites one, except the encounter note it keeps adding to.
"""
import json
import re

from . import config, db, library

FOLDERS = ["World/Bestiary", "World/Encounters", "World/People", "World/Places", "World/Sessions", "World/Maps", "Templates"]
XP = {"0": 10, "1/8": 25, "1/4": 50, "1/2": 100, "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800, "6": 2300, "7": 2900,
      "8": 3900, "9": 5000, "10": 5900, "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000, "16": 15000,
      "17": 18000, "18": 20000, "19": 22000, "20": 25000, "21": 33000, "22": 41000, "23": 50000, "24": 62000,
      "25": 75000, "26": 90000, "27": 105000, "28": 120000, "29": 135000, "30": 155000}
ENCOUNTER = "World/Encounters/Next encounter.md"


def ok():
    return bool(config.VAULT and config.VAULT.exists())


def q(s):
    """A YAML string that is always safe: JSON's double-quoted form is valid YAML."""
    return json.dumps(s if s is not None else "", ensure_ascii=False)


def safe_name(s):
    return re.sub(r'[\\/:*?"<>|#^\[\]]', "", s).strip()


def write_new(rel, text):
    p = config.VAULT / rel
    if p.exists():
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    return True


def olam_link(id):
    return f"{config.URL}/#/wiki/{id}"


# ---------- Fantasy Statblocks ----------

def bestiary_name(e):
    """The 2024 rules get the plain name; any other version says which it is, so the bestiary keeps both."""
    if e["doc"] == "srd-2024":
        return e["name"]
    tag = {"srd-2014": "2014"}.get(e["doc"]) or library.docs().get(e["doc"], {}).get("name", e["doc"])
    return f"{e['name']} ({tag})"


def statblock_yaml(e, name):
    d = e.get("data") or {}
    mod = lambda s: (s - 10) // 2
    speed = ", ".join((f"{v} ft." if k == "walk" else f"{k} {v} ft.") for k, v in (d.get("speed") or {}).items())
    out = ["layout: Basic 5e Layout", f"name: {q(name)}", f"size: {q(d.get('size', ''))}", f"type: {q((d.get('type') or '').lower())}",
           f"alignment: {q(d.get('alignment', ''))}", f"ac: {d.get('ac') or 10}", f"hp: {d.get('hp') or 1}"]
    if d.get("hit_dice"):
        out.append(f"hit_dice: {q(d['hit_dice'])}")
    out.append(f"speed: {q(speed + (' (hover)' if d.get('hover') else ''))}")
    ab = d.get("abilities") or []
    out.append("stats: [" + ", ".join(str(a["score"]) for a in ab) + "]")
    saves = [(a["k"], a["save"]) for a in ab if a.get("save") is not None and a["save"] != mod(a["score"])]
    full = {"STR": "strength", "DEX": "dexterity", "CON": "constitution", "INT": "intelligence", "WIS": "wisdom", "CHA": "charisma"}
    if saves:
        out.append("saves:")
        out += [f"  - {full[k]}: {v}" for k, v in saves]
    if d.get("skills"):
        out.append("skillsaves:")
        out += [f"  - {k.lower()}: {v}" for k, v in d["skills"].items()]
    for key, field in (("damage_vulnerabilities", "vulnerable"), ("damage_resistances", "resist"),
                       ("damage_immunities", "immune"), ("condition_immunities", "cond_immune")):
        if d.get(field):
            out.append(f"{key}: {q(d[field])}")
    out += [f"senses: {q(d.get('senses', ''))}", f"languages: {q(d.get('languages', ''))}", f"cr: {q(d.get('cr', ''))}"]

    def block(key, items):
        if items:
            out.append(f"{key}:")
            for it in items:
                out.append(f"  - name: {q(it['name'])}")
                out.append(f"    desc: {q(it['desc'])}")
    block("traits", d.get("traits"))
    acts = d.get("actions") or []
    for key, kind in (("actions", "ACTION"), ("bonus_actions", "BONUS_ACTION"), ("reactions", "REACTION"),
                      ("legendary_actions", "LEGENDARY_ACTION")):
        block(key, [a for a in acts if (a.get("type") or "ACTION") == kind])
    return "\n".join(out)


def monster(id):
    """A bestiary note for one monster. Returns its path in the vault (the existing one if it's already there)."""
    e = library.get(id)
    if not e or e["kind"] != "monster":
        raise KeyError(id)
    d = library.docs().get(e["doc"], {})
    name = bestiary_name(e)
    rel = f"World/Bestiary/{safe_name(name)}.md"
    cr = (e.get("data") or {}).get("cr", "")
    text = (f"---\ntags: [bestiary]\ncr: {q(cr)}\nsource: {q(d.get('name', e['doc']))}\nlicense: {q(d.get('license', ''))}\n"
            f"olam: {q(id)}\n---\n\n```statblock\n{statblock_yaml(e, name)}\n```\n\n## Notes\n\n\n\n## In my world\n\n\n\n"
            f"---\nFrom {d.get('name', e['doc'])} ({d.get('license', '')}) by way of Olam: {olam_link(id)}\n")
    write_new(rel, text)
    return rel


# ---------- Initiative Tracker ----------

LINE = re.compile(r'^\s*-\s*(\d+):\s*(\[\["(.+?)"\]\]|[^,]+?),\s*(\d+),\s*(\d+),\s*(-?\d+),\s*(\d+)\s*$')


def encounter_lines():
    p = config.VAULT / ENCOUNTER
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        m = LINE.match(line)
        if m:
            out.append({"n": int(m.group(1)), "name": m.group(3) or m.group(2).strip(), "hp": int(m.group(4)),
                        "ac": int(m.group(5)), "init": int(m.group(6)), "xp": int(m.group(7))})
    return out


def encounter_text(creatures):
    def fmt(c):
        name = f'[["{c["name"]}"]]' if "," in c["name"] else c["name"]
        return f"  - {c['n']}: {name}, {c['hp']}, {c['ac']}, {c['init']}, {c['xp']}"
    xp = sum(c["n"] * c["xp"] for c in creatures)
    links = "\n".join(f"- [[{safe_name(c['name'])}]] × {c['n']}" for c in creatures)
    return (f"---\ntags: [encounter]\n---\n\n```encounter\nname: Next encounter\ncreatures:\n"
            + "\n".join(fmt(c) for c in creatures)
            + f"\n```\n\n## Monsters\n\n{links}\n\nTotal XP: {xp:,}\n")


def encounter_add(id, n=1):
    """Add a monster to the next encounter (one more if it's already there) and make sure its bestiary note exists."""
    e = library.get(id)
    if not e or e["kind"] != "monster":
        raise KeyError(id)
    monster(id)
    d = e.get("data") or {}
    name = bestiary_name(e)
    cs = encounter_lines()
    for c in cs:
        if c["name"] == name:
            c["n"] += n
            break
    else:
        cs.append({"n": n, "name": name, "hp": d.get("hp") or 1, "ac": d.get("ac") or 10,
                   "init": d.get("initiative") if d.get("initiative") is not None else (d["abilities"][1]["score"] - 10) // 2,
                   "xp": d.get("xp") or XP.get(str(d.get("cr", "")), 0)})
    p = config.VAULT / ENCOUNTER
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(encounter_text(cs))
    return {"path": ENCOUNTER, "creatures": cs}


# ---------- Dice Roller ----------

def dice_for(roll):
    """A lesson's example roll as a Dice Roller formula: 2d20kh for advantage, 2d20kl for disadvantage."""
    b = roll.get("bonus", 0)
    base = {"adv": "2d20kh", "dis": "2d20kl"}.get(roll.get("mode"), "1d20")
    return f"{base}{'+' if b >= 0 else '-'}{abs(b)}" if b else base


# ---------- the world: templates and the Leaflet map ----------

TEMPLATES = {
    "Templates/NPC.md": """---
tags: [npc]
role:
home:
npcimage:
ally: []
enemy: []
family: []
friend: []
rival: []
mentor: []
---

```relations
size: small
```

**Wants:**
**Fears:**
**Secret:**
**Voice:**

## Known to the party


## Secrets

""",
    "Templates/Place.md": """---
tags: [place]
type: Town
location: [50, 80]
visited: false
dm-only: false
---

**What's here:**
**Who's here:**
**A secret:**
""",
    "Templates/Session.md": """---
tags: [session]
fc-calendar:
fc-date:
fc-category: Session
---

## What happened


## Loose threads


## Rolls worth remembering

`dice: 1d20`
""",
    "Templates/Monster.md": """---
tags: [bestiary, homebrew]
---

```statblock
layout: Basic 5e Layout
name: "{{title}}"
size: Medium
type: humanoid
alignment: neutral
ac: 12
hp: 11
hit_dice: "2d8 + 2"
speed: "30 ft."
stats: [10, 12, 12, 10, 10, 10]
senses: "Passive Perception 10"
languages: "Common"
cr: "1/4"
traits:
  - name: ""
    desc: ""
actions:
  - name: ""
    desc: ""
```
""",
}

MAP_NOTE = """```leaflet
id: olam-world
image: [[World map.png]]
height: 640px
bounds:
  - [100, 0]
  - [0, 160]
lat: 50
long: 80
minZoom: 1
maxZoom: 6
defaultZoom: 2
unit: miles
scale: 1
markerFolder: World/Places
```
"""


def blank_map(path):
    """A parchment sheet to draw the world on, until there's a real map to put in its place."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    W, H = 2400, 1500
    img = Image.new("RGB", (W, H), (231, 216, 182))
    noise = Image.effect_noise((W // 4, H // 4), 22).resize((W, H)).filter(ImageFilter.GaussianBlur(3))
    img = Image.blend(img, Image.merge("RGB", [noise.point(lambda v: 150 + v // 3)] * 3), 0.18)
    dr = ImageDraw.Draw(img)
    for x in range(0, W, 150):
        dr.line([(x, 0), (x, H)], fill=(205, 188, 152), width=1)
    for y in range(0, H, 150):
        dr.line([(0, y), (W, y)], fill=(205, 188, 152), width=1)
    dr.rectangle([24, 24, W - 25, H - 25], outline=(58, 46, 34), width=4)
    cx, cy, r = W - 190, H - 190, 90
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(58, 46, 34), width=3)
    dr.polygon([(cx, cy - r - 30), (cx + 16, cy), (cx, cy + r + 30), (cx - 16, cy)], fill=(58, 46, 34))
    dr.polygon([(cx - r - 30, cy), (cx, cy + 16), (cx + r + 30, cy), (cx, cy - 16)], fill=(122, 106, 82))
    dr.polygon([(cx, cy - r - 30), (cx + 16, cy), (cx - 16, cy)], fill=(156, 59, 42))
    img.save(path, "PNG", optimize=True)


def setup():
    """The world's folders, templates and map. Safe to run again: nothing that exists is touched."""
    if not ok():
        raise RuntimeError("No vault set")
    made = []
    for f in FOLDERS:
        (config.VAULT / f).mkdir(parents=True, exist_ok=True)
    for rel, text in TEMPLATES.items():
        if write_new(rel, text):
            made.append(rel)
    goblin = library.get("srd-2024/monster/goblin-warrior")
    if goblin:
        d = goblin["data"]
        enc = (f"```encounter\nname: \"{{{{title}}}}\"\ncreatures:\n  - 2: {goblin['name']}, {d['hp']}, {d['ac']}, "
               f"{d.get('initiative') or 0}, {d.get('xp') or XP.get(str(d['cr']), 0)}\n```\n")
        if write_new("Templates/Encounter.md", enc):
            made.append("Templates/Encounter.md")
    png = config.VAULT / "World/Maps/World map.png"
    if not png.exists():
        blank_map(png)
        made.append("World/Maps/World map.png")
    if write_new("World/Maps/World map.md", MAP_NOTE):
        made.append("World/Maps/World map.md")
    return made
