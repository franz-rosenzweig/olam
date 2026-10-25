"""Search across every shelf, and the wiki's hub pages: one topic, every source, each with its shelf."""
import json
import re

from . import config, db, pictures, zims

SHELVES = {
    "rule": "Rule", "third": "3rd-party", "expert": "Expert", "craft": "Craft", "idea": "Idea", "yours": "Yours",
}
KIND_LABEL = {"monster": "Monster", "spell": "Spell", "magic-item": "Magic item", "item": "Equipment", "condition": "Condition",
              "rule": "Rule", "glossary": "Rules Glossary", "class": "Class", "species": "Species", "background": "Background",
              "feat": "Feat", "book": "Book"}


def row(r, snippet=None):
    d = dict(r)
    d.pop("rowid", None)
    if d.get("data"):
        d["data"] = json.loads(d["data"])
    d["kind_label"] = KIND_LABEL.get(d["kind"], d["kind"])
    d["shelf_label"] = SHELVES.get(d["shelf"], d["shelf"])
    pictures.decorate(d)
    if snippet is not None:
        d["snippet"] = snippet
    return d


def docs():
    return {r["key"]: dict(r) for r in db.connect().execute("SELECT * FROM docs")}


def fts_query(q):
    words = re.findall(r"[\w’']+", q.lower())
    words = [w.replace("’", "'").strip("'") for w in words if w.strip("'’")]
    if not words:
        return None
    return " ".join(f'"{w}"*' if i == len(words) - 1 else f'"{w}"' for i, w in enumerate(words))


def search(q, kinds=None, shelves=None, editions=None, limit=40, books=True):
    """Entries matching q, best first: exact names, then names that start with q, then full text."""
    c = db.connect()
    fq = fts_query(q)
    if not fq:
        return []
    where, args = ["entries_fts MATCH ?"], [fq]
    if kinds:
        where.append(f"e.kind IN ({','.join('?' * len(kinds))})"); args += kinds
    if shelves:
        where.append(f"e.shelf IN ({','.join('?' * len(shelves))})"); args += shelves
    if editions:
        where.append(f"(e.edition IN ({','.join('?' * len(editions))}) OR e.edition='')"); args += editions
    if not books:
        where.append("e.kind != 'book'")
    sql = f"""SELECT e.*, snippet(entries_fts, 1, '[[', ']]', '…', 18) AS snip,
                bm25(entries_fts, 8.0, 1.0) AS score
              FROM entries_fts JOIN entries e ON e.rowid = entries_fts.rowid
              WHERE {' AND '.join(where)} ORDER BY score LIMIT 400"""
    rows = c.execute(sql, args).fetchall()
    ql = q.strip().lower()
    edition_rank = {"2024": 0, "": 1, "2014": 2, "a5e": 3, "4e": 5}
    shelf_rank = {"rule": 0, "third": 2, "idea": 3}

    def key(r):
        n = (r["name"] or "").lower()
        exact = 0 if n == ql else (1 if n.startswith(ql) else 2)
        return (exact, 1 if r["kind"] == "book" else 0, shelf_rank.get(r["shelf"], 1), edition_rank.get(r["edition"], 4), r["score"])
    rows = sorted(rows, key=key)
    out, seen_books = [], {}
    for r in rows:
        if r["kind"] == "book":                     # one hit per book, the best one
            if seen_books.get(r["doc"]):
                continue
            seen_books[r["doc"]] = 1
        out.append(row(r, r["snip"]))
        if len(out) >= limit:
            break
    for o in out:
        o.pop("score", None); o.pop("snip", None)
        if o["kind"] != "book":
            o["body"] = None
        else:
            o["body"] = None
    return out


def qa_weight(p):
    """How much a Q&A page's votes count here: D&D 2024 answers most, other games least."""
    t = p.get("tags") or []
    return 3 if "dnd-5e-2024" in t else 2 if any(x.startswith("dnd-5e") for x in t) else \
        1.5 if any(x.startswith(("dnd", "dungeons-and-dragons", "adnd")) for x in t) else 0.3


def rank_qa(pages, name=""):
    n = norm(name)
    return sorted(pages, key=lambda p: (-(1 if n and n in norm(p["title"]) else 0), -max(p.get("votes", 0), 0.5) * qa_weight(p)))


def is_homebrew(p):
    return not re.match(r"^(\d+e |)SRD", p["title"]) and "Talk:" not in p["title"] and "(" in p["title"]


def zim_hits(q, n=5):
    """Per archive: how many pages mention q, and the best few."""
    out = []
    for key, z in zims.all().items():
        tn, tpaths = zims.titles(key, q, n * 3)
        fn, fpaths = zims.fulltext(key, q, n * 3)
        paths = list(dict.fromkeys(tpaths + fpaths))
        pages = [p for p in (zims.page(key, x) for x in paths) if p]
        if z["kind"] == "qa":
            pages = rank_qa(pages, q)
        elif key == "dandwiki":
            pages = [p for p in pages if is_homebrew(p)]
        pages = pages[:n]
        out.append({"zim": key, "label": z["label"], "shelf": z["shelf"], "shelf_label": SHELVES[z["shelf"]],
                    "license": z["license"], "note": z.get("note", ""), "total": max(tn, fn), "pages": pages,
                    "browse": f"{config.KIWIX_URL}/search?books.name={z['book'].rsplit('_', 1)[0]}&pattern={q}" if config.KIWIX_URL else ""})
    return out


def get(id):
    r = db.connect().execute("SELECT * FROM entries WHERE id=?", (id,)).fetchone()
    return row(r) if r else None


def norm(name):
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def terms():
    """The 2024 rules terms the app links wherever they appear: glossary entries and conditions."""
    c = db.connect()
    rows = c.execute("SELECT id, name, summary, kind FROM entries WHERE doc='srd-2024' AND kind IN ('glossary','condition') ORDER BY length(name) DESC").fetchall()
    seen, out = set(), []
    for r in rows:
        if r["name"].lower() in seen or len(r["name"]) < 4:
            continue
        seen.add(r["name"].lower())
        out.append({"id": r["id"], "name": r["name"], "summary": r["summary"]})
    return out


def hub(id):
    """Everything Olam knows about one entry, grouped by shelf."""
    e = get(id)
    if not e:
        return None
    c = db.connect()
    D = docs()
    e["doc_name"] = D.get(e["doc"], {}).get("name", e["doc"])
    e["license"] = D.get(e["doc"], {}).get("license", "")
    name = e["name"]
    n = norm(name)
    sections = {}

    # Other versions: the same name in other editions and third-party books.
    others = c.execute("SELECT * FROM entries WHERE name = ? COLLATE NOCASE AND id != ? AND kind != 'book' ORDER BY shelf, edition",
                       (name, id)).fetchall()
    if e["kind"] == "monster":
        others += c.execute("SELECT * FROM entries WHERE kind='monster' AND id != ? AND name LIKE ? AND name != ? COLLATE NOCASE LIMIT 12",
                            (id, f"%{name}%", name)).fetchall()
    vs = []
    for r in others:
        o = row(r)
        o["doc_name"] = D.get(o["doc"], {}).get("name", o["doc"])
        o["license"] = D.get(o["doc"], {}).get("license", "")
        o.pop("body", None)
        vs.append(o)
    sections["versions"] = vs

    # Rules it leans on: glossary terms named in its text, and the glossary entry of the same name.
    body = (e.get("body") or "") + json.dumps(e.get("data") or {})
    rel = []
    for t in terms():
        if t["id"] != id and re.search(r"\b" + re.escape(t["name"]) + r"\b", body):
            rel.append(t)
    sections["terms"] = rel[:16]

    # Your library: books that mention it (private), best passage per book.
    hits = []
    fq = '"' + name.replace('"', "") + '"'
    for r in c.execute("""SELECT e.*, snippet(entries_fts, 1, '[[', ']]', '…', 24) AS snip FROM entries_fts
                          JOIN entries e ON e.rowid = entries_fts.rowid
                          WHERE entries_fts MATCH ? AND e.kind='book' ORDER BY bm25(entries_fts) LIMIT 60""", (fq,)):
        if any(h["doc"] == r["doc"] for h in hits):
            continue
        h = row(r, r["snip"])
        h.pop("body", None)
        h["note"] = (h.get("data") or {}).get("note", "")
        hits.append(h)
        if len(hits) >= 6:
            break
    sections["books"] = hits

    # The archives: expert answers, homebrew, worldbuilding, myth.
    rpg_n, rpg = zims.titles("rpg.stackexchange.com", name, 12)
    ft_n, ft = zims.fulltext("rpg.stackexchange.com", name, 12)
    paths = list(dict.fromkeys(rpg + ft))[:24]
    qa = rank_qa([p for p in (zims.page("rpg.stackexchange.com", x) for x in paths) if p], name)
    sections["expert"] = {"total": max(rpg_n, ft_n), "pages": qa[:8]}

    hb_n, hb = zims.titles("dandwiki", name, 60)
    home = []
    for x in hb:
        p = zims.page("dandwiki", x)
        if not p or not is_homebrew(p):
            continue
        p["name"], p["kind"] = zims.homebrew_note(p)
        p["text"] = re.sub(r"^\s*" + re.escape(p["name"]) + r"\s*", "", p.get("text") or "")
        home.append(p)
    fn, _ = zims.fulltext("dandwiki", name, 1)
    sections["homebrew"] = {"total": len(home), "mentions": fn, "pages": home[:8]}

    wb_n, wb = zims.fulltext("worldbuilding.stackexchange.com", name, 4)
    sections["craft"] = {"total": wb_n, "pages": [p for p in (zims.page("worldbuilding.stackexchange.com", x) for x in wb) if p]}

    myth = []
    words = [name] + [w for w in re.findall(r"[A-Za-z]{4,}", name) if w.lower() != name.lower()]
    if " " not in name and zims.fulltext("mythology.stackexchange.com", name, 1)[0] == 0:
        words += split_compound(name)
    for w in words:
        mn, mp = zims.fulltext("mythology.stackexchange.com", w, 3)
        for x in mp:
            p = zims.page("mythology.stackexchange.com", x)
            if p and all(p["path"] != m["path"] for m in myth):
                p["about"] = w
                myth.append(p)
        if len(myth) >= 4:
            break
    sections["myth"] = myth[:4]

    sections["yours"] = vault_mentions(name)
    e["summary_ai"] = db.cache_get("summary:" + id)
    return {"entry": e, "sections": sections}


def split_compound(name):
    """"Owlbear" -> ["owl", "bear"]: the split whose halves the mythology archive knows best."""
    w = name.lower()
    best, best_n = [], 0
    for i in range(3, len(w) - 2):
        a, b = w[:i], w[i:]
        na = zims.fulltext("mythology.stackexchange.com", a, 1)[0]
        nb = zims.fulltext("mythology.stackexchange.com", b, 1)[0]
        if min(na, nb) > best_n:
            best, best_n = [a, b], min(na, nb)
    return best


def vault_mentions(name, limit=8):
    if not config.VAULT or not config.VAULT.exists():
        return []
    out = []
    pat = re.compile(re.escape(name), re.I)
    for f in config.VAULT.rglob("*.md"):
        if ".obsidian" in f.parts or ".trash" in f.parts:
            continue
        try:
            t = f.read_text(errors="replace")
        except OSError:
            continue
        m = pat.search(t)
        if m:
            s = t[max(0, m.start() - 120): m.end() + 160].replace("\n", " ")
            out.append({"note": str(f.relative_to(config.VAULT)), "title": f.stem, "snippet": s.strip()})
            if len(out) >= limit:
                break
    return out


def browse(kind=None, edition=None, letter=None, limit=500):
    c = db.connect()
    where, args = ["kind != 'book'"], []
    if kind:
        where.append("kind = ?"); args.append(kind)
    if edition:
        where.append("edition = ?"); args.append(edition)
    if letter:
        where.append("name LIKE ?"); args.append(letter + "%")
    rows = c.execute(f"SELECT id,kind,name,doc,shelf,edition,grp,summary FROM entries WHERE {' AND '.join(where)} "
                     f"ORDER BY name COLLATE NOCASE LIMIT ?", args + [limit]).fetchall()
    return [pictures.decorate(dict(r)) for r in rows]


def stats():
    c = db.connect()
    by = {f"{r['shelf']}": r["n"] for r in c.execute("SELECT shelf, count(*) n FROM entries GROUP BY shelf")}
    z = {k: v["archive"].article_count for k, v in zims.all().items()}
    return {"entries": sum(by.values()), "by_shelf": by, "archives": z, "pages": sum(by.values()) + sum(z.values())}
