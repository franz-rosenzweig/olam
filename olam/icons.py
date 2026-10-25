"""Which icon each thing gets, from the game-icons.net set (CC BY 3.0, built into web/icons.svg by tools/icons.py).

An entry with a picture of its own (olam/pictures.py) shows that; everything else shows its icon, so every row, card
and token in Olam has something to look at.
"""
import re

KIND = {"rule": "open-book", "glossary": "spell-book", "condition": "knocked-out-stars", "spell": "magic-swirl",
        "monster": "monster-grasp", "item": "knapsack", "magic-item": "crystal-ball", "class": "crossed-swords",
        "species": "person", "background": "scroll-unfurled", "feat": "laurels-trophy", "book": "book-cover"}

MONSTER = {"aberration": "tentacle-strike", "beast": "wolf-head", "celestial": "angel-wings", "construct": "golem-head",
           "dragon": "dragon-head", "elemental": "fire-silhouette", "fey": "fairy", "fiend": "devil-mask", "giant": "giant",
           "humanoid": "hood", "monstrosity": "griffin-symbol", "ooze": "transparent-slime", "plant": "carnivorous-plant",
           "undead": "raise-zombie", "swarm": "bee"}

CLASS = {"barbarian": "barbarian", "bard": "lyre", "cleric": "holy-symbol", "druid": "oak-leaf", "fighter": "checked-shield",
         "monk": "meditation", "paladin": "templar-shield", "ranger": "high-shot", "rogue": "cloak-dagger",
         "sorcerer": "fire-spell-cast", "warlock": "warlock-eye", "wizard": "wizard-staff"}

SPECIES = {"dragonborn": "dragon-head", "dwarf": "dwarf-face", "elf": "elf-ear", "gnome": "bad-gnome", "goliath": "giant",
           "halfling": "hobbit-dwelling", "human": "person", "orc": "orc-head", "tiefling": "devil-mask", "aasimar": "angel-wings"}

CONDITION = {"blinded": "blindfold", "charmed": "charm", "deafened": "hearing-disabled", "exhaustion": "tired-eye",
             "frightened": "terror", "grappled": "grab", "incapacitated": "knockout", "invisible": "invisible",
             "paralyzed": "frozen-body", "petrified": "stone-bust", "poisoned": "poison-bottle", "prone": "falling",
             "restrained": "manacles", "stunned": "knocked-out-stars", "unconscious": "night-sleep"}

DAMAGE = {"acid": "acid-blob", "bludgeoning": "hammer-drop", "cold": "snowflake-1", "fire": "fire", "force": "magic-swirl",
          "lightning": "lightning-arc", "necrotic": "death-juice", "piercing": "arrowhead", "poison": "poison-gas",
          "psychic": "brain", "radiant": "sun-radiations", "slashing": "sword-wound", "thunder": "sound-waves"}

SCHOOL = {"abjuration": "magic-shield", "conjuration": "magic-portal", "divination": "crystal-ball", "enchantment": "charm",
          "evocation": "fire-spell-cast", "illusion": "magick-trick", "necromancy": "death-skull", "transmutation": "transform"}

ABILITY = {"str": "biceps", "dex": "acrobatic", "con": "heart-beats", "int": "brain", "wis": "owl", "cha": "drama-masks"}

DICE = {"d4": "d4", "d6": "perspective-dice-six", "d8": "dice-eight-faces-eight", "d10": "d10", "d12": "d12",
        "d20": "dice-twenty-faces-twenty", "dice": "rolling-dices"}

# An item's name, first match wins; then its category.
ITEM = [(r"crystal ball", "crystal-ball"), (r"crossbow", "crossbow"), (r"\bbow\b|longbow|shortbow|arrows?\b", "pocket-bow"),
        (r"sword|scimitar|rapier|blade|saber|sabre", "broadsword"), (r"\baxe|battleaxe|greataxe|handaxe", "battle-axe"),
        (r"dagger|knife", "plain-dagger"), (r"morningstar", "spiked-mace"), (r"\bmace", "flanged-mace"),
        (r"hammer|maul|war pick", "warhammer"), (r"trident", "trident"), (r"glaive|halberd", "glaive"),
        (r"spear|pike|javelin|lance", "spears"), (r"staff", "wizard-staff"), (r"club", "wood-club"), (r"whip", "whip"),
        (r"sling", "sling"), (r"musket|pistol", "musket"), (r"\bdarts?\b", "dart"), (r"sickle", "sickle"),
        (r"shield", "checked-shield"), (r"plate|breastplate", "breastplate"), (r"mail|chain shirt|scale|splint", "chain-mail"),
        (r"leather|padded|\bhide\b", "leather-armor"), (r"potion|elixir|\boil\b|philter|vial|flask|antitoxin|acid|alchemist's fire", "round-bottom-flask"),
        (r"\bring\b", "ring"), (r"wand", "fairy-wand"), (r"\brod\b", "crystal-wand"), (r"scroll", "scroll-unfurled"),
        (r"cloak|cape|robe|mantle", "cloak"), (r"boots|slippers|shoes", "boots"), (r"gloves|gauntlets|bracers", "gloves"),
        (r"amulet|necklace|periapt|medallion|talisman|brooch|scarab", "gem-pendant"),
        (r"\bbag\b|sack|backpack|pouch|haversack", "knapsack"), (r"rope|\bchain\b", "rope-coil"), (r"torch", "torch"),
        (r"lantern|lamp", "lantern-flame"), (r"tools|kit|supplies|utensils", "toolbox"),
        (r"lute|lyre|drum|flute|horn\b|bagpipes|viol|dulcimer|shawm|pan flute|instrument", "lyre"),
        (r"horse|pony|mule|camel|elephant|mastiff|donkey", "horse-head"), (r"ship|boat|galley|keelboat|longship|rowboat|warship", "sailboat"),
        (r"wagon|cart|carriage|chariot|sled", "old-wagon"), (r"ration|bread|food", "bread"), (r"\bbook\b|tome|manual|spellbook", "book-cover"),
        (r"\bkey\b", "key"), (r"\block\b|manacles", "padlock"), (r"\bgems?\b|jewel|ioun|stone\b", "gems"), (r"\bcoins?\b|gold piece", "coins"),
        (r"\btent\b", "camping-tent"), (r"trap", "wolf-trap"), (r"candle", "candle-light"), (r"\bmap\b|chart", "treasure-map"),
        (r"helm|hat\b|circlet|crown|headband|cap\b", "pointy-hat"), (r"deck|cards", "card-random"), (r"belt|girdle", "belt-armor"),
        (r"eyes|goggles|lenses", "invisible")]
ITEM_CATEGORY = [(r"armor", "breastplate"), (r"weapon|ammunition", "broadsword"), (r"potion", "round-bottom-flask"),
                 (r"ring", "ring"), (r"rod", "crystal-wand"), (r"scroll", "scroll-unfurled"), (r"staff", "wizard-staff"),
                 (r"wand", "fairy-wand"), (r"tool", "toolbox"), (r"mount|animal", "horse-head"), (r"vehicle", "sailboat")]

# A place's type on the Map.
PLACE = [(r"port|harbou?r|dock", "harbor-dock"), (r"village|hamlet", "village"), (r"city|capital", "castle"),
         (r"town", "village"), (r"swamp|marsh|fen|bog", "swamp"), (r"ruin", "ancient-ruins"), (r"isle|island", "island"),
         (r"fort|keep|castle|stronghold", "hill-fort"), (r"tower", "watchtower"), (r"forest|wood", "forest"),
         (r"mountain|peak|hill", "mountain-cave"), (r"cave|cavern|dungeon|mine", "cave-entrance"),
         (r"temple|shrine|abbey|church|monastery", "temple-gate"), (r"inn|tavern", "tavern-sign")]
PLACE_DEFAULT = "treasure-map"

# The Road's stops.
STOP = {"session": "rolling-dices", "d20": "dice-twenty-faces-twenty", "character": "person", "solo": "crossed-swords",
        "tests": "dice-target", "advantage": "perspective-dice-six", "turn": "hourglass", "conditions": "knocked-out-stars",
        "describe": "quill-ink", "conversation": "drama-masks", "improvise": "magick-trick", "prep": "treasure-map",
        "encounter": "monster-grasp", "fight": "battle-axe", "spotlight": "torch", "session-zero": "checked-shield",
        "one-shot": "dragon-head", "players": "tavern-sign"}

OTHER = ["d4", "perspective-dice-six", "dice-eight-faces-eight", "d10", "d12", "dice-twenty-faces-twenty", "rolling-dices",
         "hourglass", "dice-target", "quill-ink", "compass"]


def _first(rules, text):
    for pat, name in rules:
        if re.search(pat, text):
            return name
    return ""


def for_entry(e):
    """The icon for a library entry: by its own name where that's telling, then by its type, then by its kind."""
    kind, name = e.get("kind", ""), (e.get("name") or "").lower()
    d = e.get("data") if isinstance(e.get("data"), dict) else {}
    if kind == "monster":
        t = str(d.get("type") or (e.get("summary") or "")).lower()
        if name.startswith("swarm"):
            return MONSTER["swarm"]
        return next((v for k, v in MONSTER.items() if k in t), KIND["monster"])
    if kind in ("item", "magic-item"):
        return (_first(ITEM, name) or _first(ITEM_CATEGORY, str(d.get("category") or e.get("summary") or "").lower())
                or KIND[kind])
    if kind == "spell":
        s = str(d.get("school") or e.get("summary") or "").lower()
        return next((v for k, v in SCHOOL.items() if k in s), KIND["spell"])
    if kind == "class":
        base = str(d.get("subclass_of") or name).lower()
        return next((v for k, v in CLASS.items() if k in base or k in name), KIND["class"])
    if kind == "species":
        return next((v for k, v in SPECIES.items() if k in name), KIND["species"])
    if kind in ("condition", "glossary"):
        if name in CONDITION:
            return CONDITION[name]
        if name.removesuffix(" damage") in DAMAGE:
            return DAMAGE[name.removesuffix(" damage")]
    return KIND.get(kind, "open-book")


def for_place(kind):
    return _first(PLACE, (kind or "").lower()) or PLACE_DEFAULT


def every():
    """Every icon Olam uses, for building the sprite."""
    names = set(KIND.values()) | set(MONSTER.values()) | set(CLASS.values()) | set(SPECIES.values())
    names |= set(CONDITION.values()) | set(DAMAGE.values()) | set(SCHOOL.values()) | set(ABILITY.values())
    names |= set(DICE.values()) | set(STOP.values()) | set(OTHER) | {PLACE_DEFAULT}
    names |= {n for _, n in ITEM + ITEM_CATEGORY + PLACE}
    return sorted(names)
