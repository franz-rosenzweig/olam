"""Pictures for the library from Wikipedia and Wikimedia Commons: old paintings of goblins and griffons, museum photos
of swords and armour, photos of real animals. `olam fetch pictures` finds and downloads them into data/pictures,
with data/pictures/index.json saying where each came from, who made it and its license, so every picture is credited
where it's shown.

A picture matches an entry by name. Wikipedia only hands back freely licensed images, and Olam keeps only the ones
hosted on Commons. Monsters only take articles about a creature, an animal or a being, so "Assassin" doesn't bring back
a photo of a real assassination. Classes and species use articles chosen by hand, and SKIP lists pictures that came
up wrong when we looked at them.
"""
import hashlib
import json
import re
import threading
import time
import urllib.parse
import urllib.request
from html import unescape
from io import BytesIO

from . import __version__, config, db

DIR = config.DATA / "pictures"
INDEX = DIR / "index.json"
UA = f"Olam/{__version__} (self-hosted D&D app; https://github.com/franz-rosenzweig/olam)"
WIKI = "https://en.wikipedia.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
WIDTH = 640

# Classes and species: the article to use, or None for none (the icon stands in).
CURATED = {
    "class:barbarian": "Barbarian", "class:bard": "Bard", "class:cleric": "Chaplain", "class:druid": "Druid",
    "class:fighter": "Knight", "class:monk": "Shaolin kung fu", "class:paladin": "Paladin", "class:ranger": "Robin Hood",
    "class:rogue": "Theft", "class:sorcerer": "Witchcraft", "class:warlock": "Warlock", "class:wizard": "Merlin",
    "species:dwarf": "Dwarf (folklore)", "species:elf": "Elf", "species:gnome": "Gnome", "species:goliath": "Goliath",
    "species:halfling": "Halfling", "species:human": "Vitruvian Man", "species:dragonborn": None, "species:orc": None,
    "species:tiefling": None,
    "monster:griffon": "Griffin", "monster:hydra": "Lernaean Hydra", "monster:chimera": "Chimera (mythology)",
    "monster:gargoyle": "Gargoyle",
}
# Commons files that matched by name but show the wrong thing, or something too modern for the table (each one was
# looked at, 25 Oct 2026).
SKIP = {
    "15th_century_Gothic_breastplate.jpg",
    "AGFA_glas.jpg",
    "A_Thai_student_pouring_Holy_water.jpg",
    "A_close_up_of_0.50_Caliber_(12.7_mm)_Browning_Ball_M33_Ammunition_loaded_onto_a_Browning_M2_HB_0.50_caliber_heavy_machine.JPEG",
    "Angler_at_devizes_england_arp.jpg",
    "Aplodontia_rufa_distribution_map.png",
    "BL_Harleian_585_f_167v_Against_a_dwarf.png",
    "BallBearing.gif",
    "Bloody_Bones.png",
    "COVID-19_Vaccine_vial_and_syringe_-_US_Census.jpg",
    "California_Yacht_Race_in_2013_Photo_Don_Ramey_Logan.jpg",
    "Carandache_Ecridor.jpg",
    "Chest.jpg",
    "Choctaw_group.png",
    "Cork_cambium_1.jpg",
    "Cunninghamella_echinulata01.jpg",
    "D&D_Game_1.jpg",
    "DnD_Gnoll.png",
    "Dressage_Arabian_(2938612678).jpg",
    "ESEE-5-Knife-Review-Tactical-Survival-Knife-1536x1024.jpg",
    "Fothergilla_gardenii.jpg",
    "Füller-tinte_hg.jpg",
    "Giant_Eagle_logo.svg",
    "Henkersknoten8Wklg.JPG",
    "INF3-270_Anti-rumour_and_careless_talk_Keep_mum_-_she's_not_so_dumb.jpg",
    "Imperial_Encyclopaedia_-_Animal_Kingdom_-_pic152_-_騶虞圖.png",
    "India.Mumbai.04.jpg",
    "Jiangshi_custome.jpg",
    "KZ-2013-50tenge-Shurale-b.png",
    "Ladder.webp",
    "Lightning-rod-diagram.svg",
    "Mag_glass_request.jpg",
    "Mesenchytraeus_solifugus_anterior.png",
    "Parts_of_a_Bell.svg",
    "Pentothal_vintage_package_-_truth_serum.jpg",
    "Person_handcuffed_behind_back.jpg",
    "Pistol_used_by_\"Squeaky\"_Fromme.JPG",
    "Portland_Pudgy_safety_dinghy,_rowing.JPG",
    "Profilhaken.jpg",
    "Ramses_I_Mummy.jpg",
    "Riding_crop.jpeg",
    "Romanian_ration-card_for_bread,_1989.jpg",
    "Rucksack1.jpg",
    "Russian-Matroshka.jpg",
    "SaintsenecaTreefort2014.jpg",
    "Samurai_actors.jpg",
    "Saxo_Grammaticus_-_Frederik_Winkel_Horn_-_Louis_Moe_(1898)_bsb00073337_00172.jpg",
    "Scotland_Independence_March,_28_March_2026_(32).jpg",
    "Seven_Sisters_3.jpg",
    "Skovl.jpg",
    "Skulls_of_Desmodus_draculae_and_D._rotundus.jpg",
    "Stamp_of_Ukraine_s1817.jpg",
    "Strasbourg,_Rat_King_retusche.jpg",
    "Synthyris_reniformis_4979.JPG",
    "US_Army_mess_kits_-_IMG_1506.JPG",
    "Ursa_Major_constellation_detail_map.PNG",
    "Vampire_watermelon.jpg",
    "Various_products_made_from_paper.JPG",
    "Volunteer_Mushing_on_Wonder_Lake_(7065286379).jpg",
    "Wagon_Ride_P9190071.jpg",
    "Wampus_cat_20160530_123904_(cropped).jpg",
    "Warring_States_Bronze_Pi,_5th-3rd_C._BC.jpg",
    "Waspstinger1658-2.jpg",
    "Weiselzellen_68a.jpg",
    "Worry_stones.jpg",
    "Zeppellin_NT_amk.JPG",
}

# A monster's article must describe a creature of some kind.
CREATURE = re.compile(r"myth|legend|folklore|creature|monster|spirit|being|undead|demon|devil|deity|species|genus|"
                      r"family of|order of|subfamily|animal|mammal|bird|reptile|snake|lizard|serpent|fish|insect|spider|"
                      r"arachnid|shark|whale|dragon|giant|fairy|fae|nymph|cryptid|horse|dog|cat\b|bear|wolf|\bape\b|"
                      r"elephant|beetle|crab|octopus|squid|frog|toad|bat\b|rat\b|boar|lion|tiger|crocodile|eagle|owl|"
                      r"hawk|vulture|raven|scorpion|worm|plant|tree|fungus|mould|mold|slime|elemental|ghost|vampire", re.I)
# No item takes an article that's about one of these.
NOT_ITEM = re.compile(r"album|song|film|band\b|video game|company|television|tv series|novel|comic|surname|given name|"
                      r"village|town in|city in|municipality|commune|river|football|software|magazine|newspaper|"
                      r"programming|musician|singer|actor|politician|character|airline|brand|sports|team|rapper|"
                      r"chemical compound|element with|unit of|fictional|dungeons & dragons|person|people", re.I)
PREFIX = re.compile(r"^(giant|young|adult|ancient|elder|swarm of|dire|greater|lesser|awakened)\s+", re.I)
ROLE = re.compile(r"\s+(warrior|boss|minion|captain|chieftain|shaman|mage|priest|archer|scout|lord|king|queen|leader|"
                  r"champion|soldier|guard|berserker|hunter|tyrant|matriarch|patriarch|elite)$", re.I)

_lock = threading.Lock()
_index = {"mtime": None, "data": {}}


def norm(name):
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def key(kind, name):
    return ("item" if kind in ("item", "magic-item") else kind) + ":" + norm(name)


def index():
    """The index, reloaded when `olam fetch pictures` rewrites it."""
    with _lock:
        try:
            m = INDEX.stat().st_mtime
        except FileNotFoundError:
            return {}
        if m != _index["mtime"]:
            _index["data"] = json.loads(INDEX.read_text()).get("pictures", {})
            _index["mtime"] = m
        return _index["data"]


def lookup(kind, name):
    p = index().get(key(kind, name))
    if not p:
        return None
    return {"src": "pictures/" + p["file"], "author": p["author"], "license": p["license"], "license_url": p["license_url"],
            "source": p["source"], "article": p["article"], "w": p["w"], "h": p["h"]}


def decorate(e):
    """An entry gets its picture (if it has one) and its icon, for the page to show."""
    from . import icons
    if isinstance(e, dict) and e.get("kind"):
        e["pic"] = lookup(e["kind"], e.get("name"))
        e["icon"] = icons.for_entry(e)
    return e


# ---------- fetching ----------

def _get(url, params, tries=4):
    u = url + "?" + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i < tries - 1:
                time.sleep(5 * (i + 1))
                continue
            raise


def targets():
    """Everything that could have a picture: monsters, gear, magic items, classes and species, with the names to try."""
    c = db.connect()
    out = {}
    for r in c.execute("SELECT kind, name, doc, data FROM entries WHERE kind IN ('monster','item','magic-item','class','species')"):
        k = key(r["kind"], r["name"])
        d = json.loads(r["data"] or "{}") if r["data"] else {}
        if r["kind"] == "class" and d.get("subclass_of"):
            continue
        t = out.setdefault(k, {"kind": r["kind"], "name": r["name"], "srd": False})
        t["srd"] |= r["doc"].startswith("srd-")
    for k, t in out.items():
        name = re.sub(r"\s*\(.*?\)\s*", " ", t["name"]).strip()
        if k in CURATED:
            t["titles"] = [CURATED[k]] if CURATED[k] else []
            t["curated"] = True
            continue
        titles = [name, name[:1] + name[1:].lower()]
        if t["kind"] == "monster" and t["srd"]:
            base = PREFIX.sub("", name)
            base = PREFIX.sub("", base)
            if base != name:
                titles += [base, base[:1].upper() + base[1:].lower()]
            role = ROLE.sub("", base)
            if role != base:
                titles += [role, role[:1].upper() + role[1:].lower()]
            if re.search(r"dragon\b|wyrmling", name, re.I):
                titles.append("Dragon")
        t["titles"] = list(dict.fromkeys(titles))
    return out


def resolve(titles):
    """Wikipedia's page for each title: {title: {page, image, description}}, following redirects."""
    out = {}
    titles = list(dict.fromkeys(titles))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = json.loads(_get(WIKI, {"action": "query", "format": "json", "redirects": 1, "prop": "pageimages|pageprops|description",
                                   "piprop": "name", "ppprop": "disambiguation", "titles": "|".join(chunk)}))["query"]
        hop = {n["from"]: n["to"] for n in q.get("normalized", [])}
        red = {n["from"]: n["to"] for n in q.get("redirects", [])}
        pages = {p.get("title"): p for p in q.get("pages", {}).values()}
        for t in chunk:
            s = hop.get(t, t)
            s = red.get(s, s)
            p = pages.get(s)
            if not p or "missing" in p or "disambiguation" in p.get("pageprops", {}) or s.startswith("List of"):
                continue
            if p.get("pageimage"):
                out[t] = {"page": s, "image": p["pageimage"], "description": p.get("description", "")}
        time.sleep(0.3)
    return out


def commons(files):
    """Commons' details for each file: a thumbnail, the author and the license. Files not on Commons are left out."""
    out = {}
    files = list(dict.fromkeys(files))
    for i in range(0, len(files), 50):
        chunk = files[i:i + 50]
        q = json.loads(_get(COMMONS, {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|extmetadata|mime",
                                      "iiurlwidth": WIDTH, "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|UsageTerms",
                                      "titles": "|".join("File:" + f for f in chunk)}))["query"]
        hop = {n["to"]: n["from"] for n in q.get("normalized", [])}
        for p in q.get("pages", {}).values():
            if "missing" in p or not p.get("imageinfo"):
                continue
            ii = p["imageinfo"][0]
            meta = {k: v.get("value", "") for k, v in (ii.get("extmetadata") or {}).items()}
            author = re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", meta.get("Artist", "")))).strip()
            author = re.sub(r"\s*\((Life ?time|born|died)[^)]*\)|\s*\(talk\)", "", author, flags=re.I).strip(" ,;") or "Unknown author"
            name = hop.get(p["title"], p["title"]).removeprefix("File:")
            out[name.replace(" ", "_")] = {"thumb": ii.get("thumburl") or ii.get("url"), "source": ii.get("descriptionurl"),
                                           "author": author if len(author) <= 90 else author[:88].rsplit(" ", 1)[0] + "…", "license": meta.get("LicenseShortName") or meta.get("UsageTerms") or "See source",
                                           "license_url": meta.get("LicenseUrl", "")}
        time.sleep(0.3)
    return out


def fetch(log=print):
    from PIL import Image
    DIR.mkdir(parents=True, exist_ok=True)
    T = targets()
    log(f"Pictures: looking up {len(T)} names on Wikipedia")
    pages = resolve([t for v in T.values() for t in v["titles"]])
    chosen = {}
    for k, t in T.items():
        for title in t["titles"]:
            p = pages.get(title)
            if not p or p["image"].replace(" ", "_") in SKIP:
                continue
            if not t.get("curated"):
                if t["kind"] == "monster" and not CREATURE.search(p["description"] + " " + p["page"]):
                    continue
                if t["kind"] in ("item", "magic-item") and NOT_ITEM.search(p["description"]):
                    continue
            chosen[k] = p
            break
    log(f"  {len(chosen)} have a picture on Wikipedia; checking Commons")
    info = commons([p["image"] for p in chosen.values()])
    pics, done = {}, {}
    for k, p in sorted(chosen.items()):
        f = p["image"].replace(" ", "_")
        ci = info.get(f)
        if not ci or not ci["thumb"]:
            continue
        if f not in done:
            out = re.sub(r"[^a-z0-9]+", "-", f.lower().rsplit(".", 1)[0])[:40].strip("-") + "-" + hashlib.sha1(f.encode()).hexdigest()[:8] + ".webp"
            path = DIR / out
            if not path.exists():
                try:
                    raw = urllib.request.urlopen(urllib.request.Request(ci["thumb"], headers={"User-Agent": UA}), timeout=60).read()
                    im = Image.open(BytesIO(raw))
                    im = im.convert("RGBA") if im.mode in ("P", "LA") else im
                    if im.mode == "RGBA":
                        bg = Image.new("RGB", im.size, (239, 228, 203))
                        bg.paste(im, mask=im.split()[-1])
                        im = bg
                    im = im.convert("RGB")
                    im.thumbnail((WIDTH, WIDTH))
                    im.save(path, "WEBP", quality=80)
                    time.sleep(0.2)
                except Exception as e:  # one bad picture shouldn't stop the rest
                    log(f"  skipped {f}: {e}")
                    continue
            with Image.open(path) as im:
                w, h = im.size
            done[f] = {"file": out, "w": w, "h": h}
        pics[k] = dict(done[f], commons=f, source=ci["source"], author=ci["author"], license=ci["license"],
                       license_url=ci["license_url"], article="https://en.wikipedia.org/wiki/" + urllib.parse.quote(p["page"].replace(" ", "_")),
                       title=p["page"])
    used = {p["file"] for p in pics.values()}
    for old in DIR.glob("*.webp"):
        if old.name not in used:
            old.unlink()
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps({"fetched": time.strftime("%Y-%m-%d"), "pictures": pics}, ensure_ascii=False, indent=1))
    tmp.replace(INDEX)
    log(f"  {len(pics)} entries now have a picture ({len(used)} files)")
    return len(pics)
