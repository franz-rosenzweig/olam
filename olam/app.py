"""Olam's web API and the web app itself (web/, plain files, no build step).

Two ways it runs: your own copy, behind a password, and the public demo (OLAM_DEMO=1), which has no login, no AI,
no books and no vault, and keeps each visitor's progress in their browser.
"""
import json
import re
import time
from collections import defaultdict, deque
from datetime import date

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, ai, auth, config, db, learn, library, pictures, vault, world, zims

app = FastAPI(title="Olam", docs_url=None, redoc_url=None, openapi_url=None)
OPEN = {"/api/login", "/api/me", "/api/credits", "/api/credits/pictures"}
# What the demo doesn't do: anything that runs the model, writes on the server, or reads the vault.
DEMO_OFF = re.compile(r"^/api/(ask|summary/|dm|note|vault|world|table|login|logout|account|settings|review(/done)?$|learn/[^/]+/(step|answer|complete)$)")
# What needs the model: off when there's no API key and no Claude CLI.
AI_ONLY = re.compile(r"^/api/(ask|summary/|world/interview)|^/api/dm$")
DOC_NOTES = {"spells-that-dont-suck": "Includes spells from Spells That Don't Suck by Omega Ankh and somanyrobots "
             "(https://www.somanyrobots.com/s/Spells-That-Dont-Suck-compressed.pdf) and from Kibbles' Casting Compendium 2.0 "
             "by KibblesTasty Homebrew LLC (https://www.kthomebrew.com/krd), both licensed CC-BY."}
HITS = defaultdict(deque)        # ip -> recent request times (the demo's limit)
FAILS = defaultdict(deque)       # ip -> recent failed sign-ins


def client_ip(request):
    """The visitor's address: Cloudflare's header first, since Caddy and the tunnel sit in front."""
    h = request.headers
    return h.get("cf-connecting-ip") or h.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host


def too_many(log, ip, limit, window):
    q, now = log[ip], time.time()
    while q and q[0] < now - window:
        q.popleft()
    return len(q) >= limit


@app.middleware("http")
async def guard(request: Request, call_next):
    p = request.url.path
    if p.startswith("/api/"):
        if config.DEMO:
            if DEMO_OFF.match(p):
                return JSONResponse({"error": "Not in the demo"}, status_code=403)
            ip = client_ip(request)
            if too_many(HITS, ip, 240, 60):
                return JSONResponse({"error": "Too many requests. Try again in a minute."}, status_code=429)
            HITS[ip].append(time.time())
        elif p not in OPEN and not auth.valid(request.cookies.get(auth.COOKIE)):
            return JSONResponse({"error": "Sign in first"}, status_code=401)
        elif not config.AI and AI_ONLY.match(p):
            return JSONResponse({"error": "The AI features are off"}, status_code=403)
    resp = await call_next(request)
    if p.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    elif re.search(r"\.(woff2|svg|png|webp|ico)$", p):
        resp.headers["Cache-Control"] = "public, max-age=86400"
    else:
        resp.headers["Cache-Control"] = "private, no-cache"
    return resp


@app.get("/api/me")
def me(request: Request):
    if config.DEMO:
        return {"signed_in": True, "configured": True, "demo": True, "ai": False}
    return {"signed_in": auth.valid(request.cookies.get(auth.COOKIE)), "configured": auth.configured(), "demo": False,
            "ai": config.AI}


@app.post("/api/login")
def login(request: Request, response: Response, body: dict = Body(...)):
    ip = client_ip(request)
    if too_many(FAILS, ip, 8, 900):
        raise HTTPException(429, "Too many tries. Wait a few minutes.")
    if not auth.configured():
        raise HTTPException(401, "No password set yet. Run olam passwd on the server.")
    if not auth.check_password(body.get("password") or ""):
        FAILS[ip].append(time.time())
        raise HTTPException(401, "That password didn’t work")
    FAILS.pop(ip, None)
    sign_in(request, response)
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie(auth.COOKIE)
    return {"ok": True}


def sign_in(request, response):
    secure = "https" in request.headers.get("cf-visitor", "") or request.url.scheme == "https"
    response.set_cookie(auth.COOKIE, auth.make_cookie(), max_age=auth.DAYS * 86400, httponly=True, samesite="lax", secure=secure)


@app.post("/api/account/password")
def change_password(request: Request, response: Response, body: dict = Body(...)):
    """A new password signs out every other browser; this one gets a fresh cookie."""
    ip = client_ip(request)
    if too_many(FAILS, ip, 8, 900):
        raise HTTPException(429, "Too many tries. Wait a few minutes.")
    if not auth.check_password(body.get("current") or ""):
        FAILS[ip].append(time.time())
        raise HTTPException(403, "That isn’t the current password")
    new = body.get("new") or ""
    if len(new) < 8:
        raise HTTPException(400, "At least 8 characters")
    auth.set_password(new)
    sign_in(request, response)
    return {"ok": True}


@app.post("/api/account/signout-others")
def signout_others(request: Request, response: Response):
    auth.new_secret()
    sign_in(request, response)
    return {"ok": True}


@app.get("/api/settings")
def settings():
    c = db.connect()
    books = c.execute("SELECT count(*) FROM docs WHERE key LIKE 'calibre/%'").fetchone()[0]
    return {"version": __version__,
            "vault": str(config.VAULT) if config.VAULT else "", "vault_ok": vault.ok(),
            "ai": "api" if config.AI and config.API_KEY else ("cli" if config.AI else "off"), "model": config.MODEL,
            "kiwix": config.KIWIX_URL, "calibre": str(config.CALIBRE) if config.CALIBRE else "", "books": books,
            "archives": [z["label"] for z in zims.all().values()],
            "entries": c.execute("SELECT count(*) FROM entries").fetchone()[0], "url": config.URL}


@app.get("/api/stats")
def stats():
    return library.stats()


@app.get("/api/search")
def search(q: str = "", kind: str = "", shelf: str = "", edition: str = "", books: int = 1, limit: int = 40):
    split = lambda s: [x for x in s.split(",") if x] or None
    return {"q": q, "results": library.search(q, split(kind), split(shelf), split(edition), min(limit, 100), bool(books))}


@app.get("/api/archives")
def archives(q: str = "", n: int = 4):
    return {"q": q, "archives": library.zim_hits(q, min(n, 10)) if q.strip() else []}


@app.get("/api/entry/{id:path}")
def entry(id: str):
    e = library.get(id)
    if not e:
        raise HTTPException(404, "Not found")
    d = library.docs().get(e["doc"], {})
    e["doc_name"], e["license"] = d.get("name", e["doc"]), d.get("license", "")
    return e


@app.get("/api/hub/{id:path}")
def hub(id: str):
    h = library.hub(id)
    if not h:
        raise HTTPException(404, "Not found")
    return h


@app.post("/api/summary/{id:path}")
def summary(id: str, fresh: int = 0):
    try:
        return ai.summary(id, bool(fresh))
    except KeyError:
        raise HTTPException(404, "Not found")
    except (RuntimeError, OSError) as e:
        raise HTTPException(502, str(e))


@app.get("/api/terms")
def terms():
    return library.terms()


@app.get("/api/browse")
def browse(kind: str = "", edition: str = "2024", letter: str = ""):
    return library.browse(kind or None, edition or None, letter or None)


@app.get("/api/zim/search")
def zim_search(zim: str, q: str, n: int = 10, mode: str = "text"):
    if zim not in zims.all():
        raise HTTPException(404, "No such archive")
    total, paths = (zims.titles if mode == "title" else zims.fulltext)(zim, q, min(n, 30))
    return {"total": total, "pages": [p for p in (zims.page(zim, x) for x in paths) if p]}


@app.get("/api/zim/page")
def zim_page(zim: str, path: str):
    p = zims.page(zim, path, full=True)
    if not p:
        raise HTTPException(404, "Not found")
    return p


@app.post("/api/ask")
def ask(body: dict = Body(...)):
    q = (body.get("q") or "").strip()
    if not q:
        raise HTTPException(400, "Ask something")
    try:
        return ai.ask(q[:500], bool(body.get("fresh")))
    except (RuntimeError, OSError) as e:
        raise HTTPException(502, str(e))


@app.get("/api/learn")
def learn_state():
    return learn.state()


@app.get("/api/learn/{stop}")
def lesson(stop: str):
    l = learn.lesson(stop)
    if not l:
        raise HTTPException(404, "No such stop")
    return l


@app.post("/api/learn/{stop}/step")
def lesson_step(stop: str, body: dict = Body(...)):
    p = learn.progress().get(stop, {"status": "", "steps": []})
    steps = list(dict.fromkeys(p["steps"] + [body.get("step", "")]))
    learn.save(stop, status=p.get("status") or "started", steps=steps)
    return learn.state()


@app.post("/api/learn/{stop}/answer")
def lesson_answer(stop: str, body: dict = Body(...)):
    return learn.answer(stop, int(body["qi"]), int(body["choice"]))


@app.post("/api/learn/{stop}/complete")
def lesson_complete(stop: str):
    return learn.complete(stop)


@app.post("/api/learn/state")
def learn_state_for(body: dict = Body(...)):
    """The demo's Road: the visitor's own progress in, the Road and the atlas out."""
    rv = [k for k in (body.get("review") or []) if isinstance(k, str)][:200]
    return learn.state(body.get("progress") or {}, len(rv))


@app.post("/api/review/list")
def review_list(body: dict = Body(...)):
    keys = [k for k in (body.get("keys") or []) if isinstance(k, str) and re.fullmatch(r"[\w-]+:\d+", k)][:200]
    return learn.review(keys)


@app.get("/api/credits")
def credits():
    """Who made what Olam shows, in the words each license asks for."""
    used = {r[0] for r in db.connect().execute("SELECT DISTINCT doc FROM entries")}
    docs = [dict(d, note=DOC_NOTES.get(d["key"], "")) for d in library.docs().values() if not d.get("private") and d["key"] in used]
    return {"docs": sorted(docs, key=lambda d: (d["shelf"] != "rule", d["name"] or "")),
            "archives": [{"label": z["label"], "license": z["license"], "book": z["book"]} for z in zims.all().values()],
            "pictures": picture_summary(), "icons": icon_artists(), "demo": config.DEMO}


def icon_artists():
    try:
        return sorted(set(json.loads((config.WEB / "icons.json").read_text()).values()))
    except (FileNotFoundError, ValueError):
        return []


def picture_summary():
    idx = pictures.index()
    lic = {}
    for p in {p["file"]: p for p in idx.values()}.values():
        lic[p["license"]] = lic.get(p["license"], 0) + 1
    return {"entries": len(idx), "files": len({p["file"] for p in idx.values()}), "licenses": lic}


@app.get("/api/credits/pictures")
def credits_pictures():
    """Every picture once, with who made it, its license and where it came from."""
    seen = {}
    for k, p in pictures.index().items():
        s = seen.setdefault(p["file"], {"src": "pictures/" + p["file"], "title": p["title"], "author": p["author"],
                                        "license": p["license"], "license_url": p["license_url"], "source": p["source"],
                                        "article": p["article"], "for": []})
        s["for"].append(k.split(":", 1)[1])
    return sorted(seen.values(), key=lambda s: s["title"].lower())


@app.get("/api/review")
def review():
    return learn.review()


@app.post("/api/review/done")
def review_done(body: dict = Body(...)):
    learn.review_done(body.get("key", ""))
    return learn.review()


@app.post("/api/dm")
def dm(body: dict = Body(...)):
    try:
        return ai.dm_turn(body.get("id") or "", (body.get("message") or "").strip()[:1500], (body.get("character") or "")[:400])
    except (RuntimeError, OSError) as e:
        raise HTTPException(502, str(e))


@app.get("/api/dm/{id}")
def dm_get(id: str):
    return ai.chat(id)


@app.get("/api/vault")
def vault_info():
    return {"vault": str(config.VAULT) if config.VAULT else "", "ok": bool(config.VAULT and config.VAULT.exists())}


@app.post("/api/note")
def note(body: dict = Body(...)):
    """A lesson note in the vault: Learn/06 Advantage & disadvantage.md, created once, never overwritten."""
    if not (config.VAULT and config.VAULT.exists()):
        raise HTTPException(409, "No vault set")
    s = learn.lesson(body.get("stop", ""))
    if not s:
        raise HTTPException(404, "No such stop")
    name = re.sub(r'[\\/:*?"<>|]', "", f"{s['n']:02d} {s['title']}")
    path = config.VAULT / "Learn" / f"{name}.md"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        links = "\n".join(f"- {x['title']} ({x.get('sub') or x.get('title')})" for x in s["sources"] if x["type"] == "entry")
        roll = (s.get("see") or {}).get("roll")
        practice = f"\n## Practice\n\n`dice: {vault.dice_for(roll)}`\n" if roll else ""
        path.write_text(f"---\nstop: {s['n']}\ntrack: {s['track']}\ndate: {date.today().isoformat()}\ntags: [olam, learn]\n---\n\n"
                        f"# {s['title']}\n\n## In my own words\n\n\n\n## What I'm still unsure about\n\n\n{practice}\n## Sources\n\n{links}\n")
    return {"path": str(path.relative_to(config.VAULT)), "vault": config.VAULT.name}


@app.post("/api/vault/monster")
def vault_monster(body: dict = Body(...)):
    """A Fantasy Statblocks note for a monster, in World/Bestiary."""
    if not vault.ok():
        raise HTTPException(409, "No vault set")
    try:
        return {"path": vault.monster(body.get("id", "")), "vault": config.VAULT.name}
    except KeyError:
        raise HTTPException(404, "Not a monster")


@app.post("/api/vault/encounter")
def vault_encounter(body: dict = Body(...)):
    """Add a monster to the Initiative Tracker encounter in World/Encounters/Next encounter.md."""
    if not vault.ok():
        raise HTTPException(409, "No vault set")
    try:
        return dict(vault.encounter_add(body.get("id", "")), vault=config.VAULT.name)
    except KeyError:
        raise HTTPException(404, "Not a monster")


# ---------- the world in the vault: Map, People, Table ----------

def worldly(fn, *a):
    """Run a world call and turn its errors into plain HTTP answers."""
    try:
        return fn(*a)
    except RuntimeError as e:
        raise HTTPException(409, str(e))
    except FileExistsError as e:
        raise HTTPException(409, str(e))
    except (FileNotFoundError, KeyError, IndexError) as e:
        raise HTTPException(404, str(e) or "Not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/world/map")
def world_map():
    return worldly(world.map_info)


@app.post("/api/world/place")
def world_place(body: dict = Body(...)):
    return {"rel": worldly(world.place_create, body.get("name", ""), body.get("type", ""), body.get("location") or [50, 80])}


@app.post("/api/world/place/set")
def world_place_set(body: dict = Body(...)):
    worldly(world.place_set, body.get("rel", ""), body.get("key", ""), body.get("value"))
    return {"ok": True}


@app.get("/api/world/note")
def world_note(rel: str):
    fm, body, _ = worldly(world.read, rel)
    return {"rel": rel, "name": rel.rsplit("/", 1)[-1].removesuffix(".md"), "body": body}


@app.get("/api/world/people")
def world_people():
    return worldly(world.people)


@app.get("/api/world/person")
def world_person(rel: str):
    return worldly(world.person, rel)


@app.post("/api/world/person")
def world_person_new(body: dict = Body(...)):
    return {"rel": worldly(world.person_create, body.get("name", ""), body.get("role", ""), body.get("home", ""))}


@app.post("/api/world/person/reveal")
def world_person_reveal(body: dict = Body(...)):
    return worldly(world.person_reveal, body.get("rel", ""), int(body.get("i", -1)))


@app.post("/api/world/person/add")
def world_person_add(body: dict = Body(...)):
    return worldly(world.person_add, body.get("rel", ""), body.get("where", ""), body.get("text", ""))


@app.post("/api/world/interview")
def world_interview(body: dict = Body(...)):
    rel = body.get("rel", "")
    if not rel.startswith(world.PEOPLE + "/"):
        raise HTTPException(400, "Not a person")
    try:
        return ai.interview(rel, (body.get("message") or "")[:800], body.get("history") or [])
    except (RuntimeError, OSError) as e:
        raise HTTPException(502, str(e))


@app.get("/api/world/encounters")
def world_encounters():
    return worldly(world.encounter_notes)


@app.get("/api/world/party")
def world_party():
    return worldly(world.party)


@app.post("/api/world/party")
def world_party_save(body: dict = Body(...)):
    return worldly(world.party_save, body.get("members") or [])


@app.get("/api/table")
def table_get():
    return world.table_get()


@app.post("/api/table")
def table_put(body: dict = Body(...)):
    return world.table_put(body.get("state") or {})


@app.post("/api/table/end")
def table_end(body: dict = Body(...)):
    return worldly(world.table_end, body.get("state") or world.table_get())


@app.get("/api/vault/file")
def vault_file(rel: str):
    """An image from the vault (a map, a portrait). Nothing else is served."""
    p = worldly(world.path_of, rel)
    if p.suffix.lower() not in world.IMAGES or not p.is_file():
        raise HTTPException(404, "Not an image")
    return FileResponse(p, headers={"Cache-Control": "private, max-age=300"})


app.mount("/static", StaticFiles(directory=config.WEB), name="static")
app.mount("/pictures", StaticFiles(directory=pictures.DIR, check_dir=False), name="pictures")


@app.get("/")
@app.get("/{rest:path}")
def index(rest: str = ""):
    if rest.startswith("api/"):
        raise HTTPException(404, "Not found")
    f = config.WEB / rest
    if rest and f.is_file() and config.WEB in f.resolve().parents:
        return FileResponse(f)
    return FileResponse(config.WEB / "index.html", headers={"Cache-Control": "no-cache"})
