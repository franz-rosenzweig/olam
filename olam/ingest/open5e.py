"""Open5e's data files (github.com/open5e/open5e-api, data/v2) into Olam's entries.

The two SRDs go in whole, on the "rule" shelf. Third-party books (Kobold Press, EN Publishing, ...)
bring only their monsters, spells and magic items, on the "third" shelf: other versions, not the rules.
"""
import json
from collections import defaultdict
from pathlib import Path

from .. import config, db

OFFICIAL = {"srd-2024", "srd-2014"}
THIRD_KINDS = {"Creature", "CreatureAction", "CreatureActionAttack", "CreatureTrait", "Spell", "MagicItem"}
ABILITIES = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
SKILLS = ["acrobatics", "animal_handling", "arcana", "athletics", "deception", "history", "insight", "intimidation",
          "investigation", "medicine", "nature", "perception", "performance", "persuasion", "religion",
          "sleight_of_hand", "stealth", "survival"]


def cr_text(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v or "")
    return {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}.get(f, str(int(f)) if f == int(f) else str(f))


def sign(n):
    return ("+" if n >= 0 else "−") + str(abs(n))


def slug_of(pk, doc):
    return pk[len(doc) + 1:] if pk.startswith(doc + "_") else pk


def load(dirpath):
    out = {}
    for f in Path(dirpath).glob("*.json"):
        try:
            out[f.stem] = json.loads(f.read_text())
        except ValueError:
            pass
    return out


def creature(c, d, doc, shelf, edition, F):
    pk, f = d["pk"], d["fields"]
    acts = sorted(F["actions"].get(pk, []), key=lambda a: (a["fields"].get("order_in_statblock") or 0))
    actions = []
    for a in acts:
        af = a["fields"]
        atks = []
        for t in F["attacks"].get(a["pk"], []):
            tf = t["fields"]
            dice = f"{tf['damage_die_count']}d{str(tf['damage_die_type']).lower().lstrip('d')}" if tf.get("damage_die_count") else ""
            atks.append({"to_hit": tf.get("to_hit_mod"), "dice": dice, "bonus": tf.get("damage_bonus") or 0,
                         "type": tf.get("damage_type") or "", "reach": tf.get("reach"), "range": tf.get("range"),
                         "long_range": tf.get("long_range")})
        actions.append({"name": af["name"], "desc": af.get("desc") or "", "type": af.get("action_type") or "ACTION",
                        "cost": af.get("legendary_action_cost"), "uses": af.get("uses_type"), "attacks": atks})
    traits = [{"name": t["fields"]["name"], "desc": t["fields"].get("desc") or ""} for t in F["traits"].get(pk, [])]
    speed = {k: f.get(k) for k in ("walk", "fly", "swim", "climb", "burrow") if f.get(k)}
    senses = []
    for k, label in (("blindsight_range", "Blindsight"), ("darkvision_range", "Darkvision"),
                     ("tremorsense_range", "Tremorsense"), ("truesight_range", "Truesight")):
        if f.get(k):
            senses.append(f"{label} {f[k]} ft.")
    if f.get("passive_perception") is not None:
        senses.append(f"Passive Perception {f['passive_perception']}")
    skills = {s.replace("_", " ").title(): f.get(f"skill_bonus_{s}") for s in SKILLS if f.get(f"skill_bonus_{s}") is not None}
    data = {
        "size": (f.get("size") or "").title(), "type": (f.get("type") or "").replace("-", " ").title(),
        "alignment": f.get("alignment") or "", "ac": f.get("armor_class"), "ac_detail": f.get("armor_detail") or "",
        "hp": f.get("hit_points"), "hit_dice": f.get("hit_dice") or "", "speed": speed, "hover": f.get("hover"),
        "initiative": f.get("initiative_bonus"),
        "abilities": [{"k": a[:3].upper(), "score": f.get(f"ability_score_{a}") or 10,
                       "save": f.get(f"saving_throw_{a}")} for a in ABILITIES],
        "skills": skills, "senses": ", ".join(senses), "languages": f.get("languages_desc") or ", ".join(f.get("languages") or []) or "—",
        "cr": cr_text(f.get("challenge_rating")), "xp": f.get("experience_points_integer"),
        "resist": f.get("damage_resistances_display") or "", "immune": f.get("damage_immunities_display") or "",
        "vulnerable": f.get("damage_vulnerabilities_display") or "", "cond_immune": f.get("condition_immunities_display") or "",
        "traits": traits, "actions": actions,
    }
    body = "\n\n".join([f"**{t['name']}.** {t['desc']}" for t in traits] + [f"**{a['name']}.** {a['desc']}" for a in actions])
    summary = f"{data['size']} {data['type']}, CR {data['cr']}"
    db.put(c, id=f"{doc}/monster/{slug_of(pk, doc)}", kind="monster", name=f["name"], doc=doc, shelf=shelf,
           edition=edition, summary=summary, body=body, data=data)


def spell(c, s, doc, shelf, edition, F):
    f = s["fields"]
    comps = [x for x, on in (("V", f.get("verbal")), ("S", f.get("somatic")), ("M", f.get("material"))) if on]
    comp = ", ".join(comps) + (f" ({f['material_specified']})" if f.get("material") and f.get("material_specified") else "")
    lvl = f.get("level") or 0
    school = (f.get("school") or "").title() if isinstance(f.get("school"), str) else ""
    head = f"{school} cantrip" if lvl == 0 else f"Level {lvl} {school}"
    classes = [str(x).split("_", 1)[-1].replace("-", " ").title() for x in (f.get("classes") or [])]
    data = {"level": lvl, "school": school, "head": head + (" (ritual)" if f.get("ritual") else ""),
            "casting_time": (f.get("casting_time") or "").replace("_", " "), "range": f.get("range_text") or "",
            "components": comp, "duration": f.get("duration") or "", "concentration": bool(f.get("concentration")),
            "ritual": bool(f.get("ritual")), "classes": classes, "higher": f.get("higher_level") or ""}
    body = (f.get("desc") or "") + (f"\n\n**Using a Higher-Level Spell Slot.** {f['higher_level']}" if f.get("higher_level") else "")
    db.put(c, id=f"{doc}/spell/{slug_of(s['pk'], doc)}", kind="spell", name=f["name"], doc=doc, shelf=shelf,
           edition=edition, summary=head, body=body, data=data)


def magic_item(c, m, doc, shelf, edition):
    f = m["fields"]
    cat = (f.get("category") or "").replace("-", " ").title()
    rar = (f.get("rarity") or "").replace("-", " ")
    att = " (requires attunement)" if f.get("requires_attunement") else ""
    head = f"{cat}, {rar}{att}".strip(", ")
    db.put(c, id=f"{doc}/magic-item/{slug_of(m['pk'], doc)}", kind="magic-item", name=f["name"], doc=doc, shelf=shelf,
           edition=edition, summary=head, body=f.get("desc") or "", data={"head": head, "rarity": rar, "category": cat})


def ingest_doc(c, path, docrow):
    doc = docrow["key"]
    edition = docrow["edition"]
    shelf = "rule" if doc in OFFICIAL else "third"
    J = load(path)
    if doc not in OFFICIAL:
        J = {k: v for k, v in J.items() if k in THIRD_KINDS}
    by_parent = lambda name: _group(J.get(name, []))
    F = {"actions": by_parent("CreatureAction"), "attacks": by_parent("CreatureActionAttack"),
         "traits": by_parent("CreatureTrait")}
    c.execute("DELETE FROM entries WHERE doc=? AND kind!='glossary'", (doc,))  # the glossary comes from the PDF
    n = 0
    for x in J.get("Creature", []):
        creature(c, x, doc, shelf, edition, F); n += 1
    for x in J.get("Spell", []):
        spell(c, x, doc, shelf, edition, F); n += 1
    for x in J.get("MagicItem", []):
        magic_item(c, x, doc, shelf, edition); n += 1
    if doc in OFFICIAL:
        n += official_extras(c, J, doc, edition)
    return n


def _group(rows):
    g = defaultdict(list)
    for r in rows:
        g[r["fields"].get("parent")].append(r)
    return g


def official_extras(c, J, doc, edition):
    n = 0
    put = lambda **k: db.put(c, doc=doc, shelf="rule", edition=edition, **k)
    sets = {s["pk"]: s["fields"] for s in J.get("RuleSet", [])}
    for pk, s in sets.items():
        put(id=f"{doc}/rule/{slug_of(pk, doc)}", kind="rule", name=s["name"], grp="Playing the Game",
            summary="Rules · " + s["name"], body=s.get("desc") or ""); n += 1
    for r in J.get("Rule", []):
        f = r["fields"]
        grp = sets.get(f.get("ruleset"), {}).get("name", "")
        put(id=f"{doc}/rule/{slug_of(r['pk'], doc)}", kind="rule", name=f["name"], grp=grp,
            summary=f"Rules · {grp}", body=f.get("desc") or "", data={"order": f.get("index"), "set": f.get("ruleset")}); n += 1
    for x in J.get("ConditionDescription", []):
        f = x["fields"]
        name = (f.get("describes") or slug_of(x["pk"], doc)).replace("-", " ").title()
        put(id=f"{doc}/condition/{slug_of(x['pk'], doc)}", kind="condition", name=name, summary="Condition", body=f.get("desc") or ""); n += 1
    for model, kind, label in (("SkillDescription", "rule", "Skill"), ("AbilityDescription", "rule", "Ability"),
                               ("DamageTypeDescription", "rule", "Damage type"), ("CreatureTypeDescription", "rule", "Creature type"),
                               ("AlignmentDescription", "rule", "Alignment")):
        for x in J.get(model, []):
            f = x["fields"]
            name = (f.get("describes") or slug_of(x["pk"], doc)).replace("-", " ").title()
            put(id=f"{doc}/{label.lower().replace(' ', '-')}/{slug_of(x['pk'], doc)}", kind=kind, name=name, grp=label + "s",
                summary=label, body=f.get("desc") or ""); n += 1
    props = {x["pk"]: x["fields"] for x in J.get("WeaponProperty", [])}
    for pk, f in props.items():
        put(id=f"{doc}/weapon-property/{slug_of(pk, doc)}", kind="rule", name=f.get("name", ""), grp="Weapon properties",
            summary="Weapon property", body=f.get("desc") or ""); n += 1
    weapons = {x["pk"]: x["fields"] for x in J.get("Weapon", [])}
    armors = {x["pk"]: x["fields"] for x in J.get("Armor", [])}
    for x in J.get("Item", []):
        f = x["fields"]
        cat = (f.get("category") or "").replace("-", " ").title()
        data = {"cost": f.get("cost"), "weight": f.get("weight"), "category": cat}
        w, a = weapons.get(f.get("weapon")), armors.get(f.get("armor"))
        if w:
            data["weapon"] = {"damage": f"{w.get('damage_dice')} {w.get('damage_type') or ''}".strip(),
                              "simple": w.get("is_simple"), "range": w.get("range"), "long_range": w.get("long_range")}
        if a:
            data["armor"] = {"ac": a.get("ac_base"), "dex": a.get("ac_add_dexmod"), "cap": a.get("ac_cap_dexmod"),
                             "stealth_disadvantage": a.get("grants_stealth_disadvantage"), "str": a.get("strength_score_required")}
        put(id=f"{doc}/item/{slug_of(x['pk'], doc)}", kind="item", name=f["name"], summary=cat or "Equipment",
            body=f.get("desc") or "", data=data); n += 1
    for model, kind, child in (("Feat", "feat", "FeatBenefit"), ("Species", "species", "SpeciesTrait"),
                               ("Background", "background", "BackgroundBenefit")):
        kids = _group(J.get(child, []))
        for x in J.get(model, []):
            f = x["fields"]
            parts = [f.get("desc") or ""] + [f"**{k['fields'].get('name')}.** {k['fields'].get('desc') or ''}"
                                             for k in sorted(kids.get(x["pk"], []), key=lambda k: k["fields"].get("order") or 0)]
            summ = model if model != "Feat" else f"Feat · {(f.get('type') or '').replace('_', ' ').title()}".strip(" ·")
            put(id=f"{doc}/{kind}/{slug_of(x['pk'], doc)}", kind=kind, name=f["name"], summary=summ,
                body="\n\n".join(p for p in parts if p)); n += 1
    feats = _group(J.get("ClassFeature", []))
    items = _group(J.get("ClassFeatureItem", []))
    classes = {x["pk"]: x["fields"] for x in J.get("CharacterClass", [])}
    for pk, f in classes.items():
        parts = []
        for ft in feats.get(pk, []):
            lv = sorted({i["fields"]["level"] for i in items.get(ft["pk"], []) if i["fields"].get("level")})
            lvtxt = f" (level {', '.join(map(str, lv))})" if lv else ""
            parts.append((lv[0] if lv else 99, f"### {ft['fields']['name']}{lvtxt}\n\n{ft['fields'].get('desc') or ''}"))
        parent = classes.get(f.get("subclass_of"))
        summ = f"{parent['name']} subclass" if parent else f"Class · Hit Die {f.get('hit_dice') or ''}".strip()
        put(id=f"{doc}/class/{slug_of(pk, doc)}", kind="class", name=f["name"], summary=summ,
            body="\n\n".join(p for _, p in sorted(parts)), data={"subclass_of": f.get("subclass_of"), "hit_dice": f.get("hit_dice")}); n += 1
    return n


def run(c):
    root = config.OPEN5E
    systems = {g["pk"]: g["fields"].get("name") for g in json.loads((root / "GameSystem.json").read_text())}
    licenses = {l["pk"]: l["fields"].get("name") for l in json.loads((root / "License.json").read_text())}
    total = 0
    for docfile in sorted(root.glob("*/*/Document.json")):
        d = json.loads(docfile.read_text())[0]
        key, f = d["pk"], d["fields"]
        if key in ("elderberry-inn-icons", "core"):
            continue
        gs = f.get("gamesystem") or ""
        edition = {"5e-2024": "2024", "5e-2014": "2014", "a5e": "a5e"}.get(gs, gs)
        lic = ", ".join(licenses.get(x, x) for x in (f.get("licenses") or []))
        if config.DEMO and "cc-by-40" not in (f.get("licenses") or []):
            continue          # the public demo carries only what Creative Commons lets anyone share
        if config.DEMO:
            lic = licenses.get("cc-by-40", "Creative Commons Attribution 4.0")
        shelf = "rule" if key in OFFICIAL else "third"
        pub = f.get("publisher") or ""
        pub = next((p["fields"].get("name") for p in json.loads((docfile.parent.parent / "Publisher.json").read_text())
                    if p["pk"] == pub), pub) if (docfile.parent.parent / "Publisher.json").exists() else pub
        db.put_doc(c, key, f.get("display_name") or f.get("name"), pub, lic, f.get("permalink") or "", shelf, edition)
        n = ingest_doc(c, docfile.parent, {"key": key, "edition": edition})
        total += n
        print(f"  {key}: {n} entries ({systems.get(gs, gs)}, {lic})")
    c.commit()
    return total
