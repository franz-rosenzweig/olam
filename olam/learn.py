"""The Road: lessons (lessons/road.json), the reader's progress, and the Atlas of Rules it uncovers."""
import json
import re

from . import config, db, icons, library, zims

_road = None


def road():
    global _road
    if _road is None:
        _road = json.loads((config.LESSONS / "road.json").read_text())
    return _road


def progress():
    rows = db.connect().execute("SELECT * FROM progress").fetchall()
    out = {}
    for r in rows:
        out[r["stop"]] = {"status": r["status"], "steps": json.loads(r["steps"] or "[]"), "answers": json.loads(r["answers"] or "{}")}
    return out


def save(stop_id, status=None, steps=None, answers=None):
    c = db.connect()
    cur = progress().get(stop_id, {"status": "", "steps": [], "answers": {}})
    status = status if status is not None else cur["status"]
    steps = steps if steps is not None else cur["steps"]
    answers = answers if answers is not None else cur["answers"]
    c.execute("INSERT OR REPLACE INTO progress(stop,status,steps,answers,updated) VALUES (?,?,?,?,CURRENT_TIMESTAMP)",
              (stop_id, status, json.dumps(steps), json.dumps(answers)))
    c.commit()


def answer(stop_id, qi, choice):
    """Record an answer; the stop is done when every question is answered correctly."""
    stop = next(s for s in road()["stops"] if s["id"] == stop_id)
    p = progress().get(stop_id, {"status": "", "steps": [], "answers": {}})
    answers = dict(p["answers"])
    answers[str(qi)] = choice
    qs = stop.get("check") or []
    done = bool(qs) and all(answers.get(str(i)) == q["correct"] for i, q in enumerate(qs))
    save(stop_id, status="done" if done else (p["status"] or "started"), answers=answers)
    if not (choice == qs[qi]["correct"]):
        review_add(stop_id, qi)
    return state()


def complete(stop_id):
    save(stop_id, status="done")
    return state()


def review_add(stop_id, qi):
    c = db.connect()
    r = c.execute("SELECT value FROM cache WHERE key='review'").fetchone()
    items = json.loads(r[0]) if r else []
    k = f"{stop_id}:{qi}"
    if k not in items:
        items.append(k)
    db.cache_put("review", items)


def review(keys=None):
    """The missed questions. The demo passes the keys it keeps in the visitor's browser."""
    items = keys if keys is not None else (db.cache_get("review") or [])
    stops = {s["id"]: s for s in road()["stops"]}
    out = []
    for k in items:
        sid, qi = k.split(":")
        s = stops.get(sid)
        if s and int(qi) < len(s.get("check") or []):
            q = s["check"][int(qi)]
            out.append({"key": k, "stop": sid, "title": s["title"], **q})
    return out


def review_done(key):
    db.cache_put("review", [k for k in (db.cache_get("review") or []) if k != key])


def state(P=None, review_count=None):
    """Every stop with its status, the current one, and the atlas. The demo passes the visitor's own progress."""
    R = road()
    P = progress() if P is None else clean_progress(P)
    stops, current, known = [], None, set()
    prev_done = True
    for s in R["stops"]:
        p = P.get(s["id"], {})
        done = p.get("status") == "done"
        if done:
            known.update(s.get("teaches") or [])
        status = "done" if done else ("current" if prev_done and current is None else "locked")
        if status == "current":
            current = s["n"]
        prev_done = done
        stops.append({"n": s["n"], "id": s["id"], "title": s["title"], "track": s["track"], "minutes": s["minutes"], "icon": icons.STOP.get(s["id"], "open-book"),
                      "outline": bool(s.get("outline")), "status": status, "steps": p.get("steps", [])})
    names = {r["id"]: r["name"] for r in db.connect().execute(
        "SELECT id, name FROM entries WHERE id IN (%s)" % ",".join("?" * sum(len(g["rules"]) for g in R["regions"])),
        [x for g in R["regions"] for x in g["rules"]])}
    regions = []
    for g in R["regions"]:
        rules = [{"id": x, "name": names.get(x, x.rsplit("/", 1)[-1]), "known": x in known} for x in g["rules"]]
        regions.append({"id": g["id"], "name": g["name"], "short": g["short"], "rules": rules,
                        "known": sum(1 for r in rules if r["known"]), "total": len(rules)})
    teaching = set()
    if current:
        teaching = set(R["stops"][current - 1].get("teaches") or [])
    return {"stops": stops, "current": current or len(stops), "weeks": R["weeks"], "regions": regions,
            "teaching": sorted(teaching), "mastered": sum(r["known"] for r in regions),
            "total": sum(r["total"] for r in regions),
            "review": review_count if review_count is not None else len(db.cache_get("review") or [])}


def clean_progress(P):
    """Progress sent by a browser, reduced to known stops and plain values."""
    ids = {s["id"] for s in road()["stops"]}
    out = {}
    for k, v in (P or {}).items() if isinstance(P, dict) else []:
        if k in ids and isinstance(v, dict):
            out[k] = {"status": "done" if v.get("status") == "done" else ("started" if v.get("status") else ""),
                      "steps": [s for s in (v.get("steps") or []) if s in ("read", "see", "do", "check")][:4],
                      "answers": {str(a): int(b) for a, b in (v.get("answers") or {}).items() if str(a).isdigit() and isinstance(b, int)}}
    return out


def lesson(stop_id):
    s = next((x for x in road()["stops"] if x["id"] == stop_id), None)
    if not s:
        return None
    s = json.loads(json.dumps(s))
    s["sources"] = [src for src in (resolve(x) for x in (s.get("read") or {}).get("sources", [])) if src]
    for q in s.get("check") or []:
        e = library.get(q.get("src", "")) if q.get("src") else None
        q["src_label"] = f"Rule · SRD 5.2 · {e['name']}" if e else ""
    s["progress"] = progress().get(stop_id, {"status": "", "steps": [], "answers": {}})
    s["icon"] = icons.STOP.get(stop_id, "open-book")
    return s


def resolve(src):
    """A lesson source as the page shows it: its shelf, title and where it leads."""
    if "id" in src:
        e = library.get(src["id"])
        if not e:
            return None
        return {"type": "entry", "id": e["id"], "title": e["name"], "shelf": e["shelf"], "pic": e.get("pic"), "icon": e.get("icon"),
                "sub": f"SRD 5.2 · {e['kind_label']}" + (f" · {e['grp']}" if e.get("grp") and e["grp"] != e["kind_label"] else "")}
    if "zim" in src:
        z = zims.all().get(src["zim"])
        if not z:
            return None
        total, paths = zims.fulltext(src["zim"], src["q"], 6)
        pages = [p for p in (zims.page(src["zim"], x) for x in paths) if p]
        if z["kind"] == "qa":
            pages = sorted(pages, key=lambda p: -max(p.get("votes", 0), 0.5) * library.qa_weight(p))
        else:
            pages = [p for p in pages if library.is_homebrew(p)] or pages
        return {"type": "zim", "zim": src["zim"], "q": src["q"], "title": z["label"], "shelf": z["shelf"], "total": total,
                "note": z.get("note", ""), "pages": [{"title": p["title"], "url": p["url"], "path": p["path"], "votes": p.get("votes"),
                                                       "tags": p.get("tags", [])} for p in pages[:3]]}
    if "book" in src or "books" in src:
        c = db.connect()
        fq = library.fts_query(src["q"]) or ""
        fq = " OR ".join(re.findall(r'"[^"]+"\*?', fq))
        if not fq:
            return None
        key = src.get("book")
        if not key:     # "books": a shelf, so the best match among the reader's own books on it (books.json)
            r = c.execute("""SELECT e.doc FROM entries_fts JOIN entries e ON e.rowid = entries_fts.rowid
                             WHERE entries_fts MATCH ? AND e.kind='book' AND e.shelf=? ORDER BY bm25(entries_fts) LIMIT 1""",
                          (fq, src["books"])).fetchone()
            if not r:
                return None
            key = r["doc"]
        d = c.execute("SELECT * FROM docs WHERE key=?", (key,)).fetchone()
        if not d:
            return None
        rows = c.execute("""SELECT e.id, e.grp, snippet(entries_fts, 1, '[[', ']]', '…', 16) s FROM entries_fts
                            JOIN entries e ON e.rowid = entries_fts.rowid WHERE entries_fts MATCH ? AND e.doc=?
                            ORDER BY bm25(entries_fts) LIMIT 2""", (fq, key)).fetchall()
        return {"type": "book", "doc": key, "title": d["name"], "shelf": d["shelf"], "sub": "Your library",
                "passages": [{"id": r["id"], "snippet": r["s"]} for r in rows]}
    if "browse" in src:
        return {"type": "browse", "kind": src["browse"], "title": src.get("label", src["browse"]), "shelf": "rule", "sub": "SRD 5.2 · Codex"}
    return None
