"""What Olam asks the model, and how: the Claude API when there's a key (ANTHROPIC_API_KEY), otherwise the Claude CLI
signed in to a Claude subscription (see config.AI).

Every answer is built from numbered sources Olam found first, and cites them, so the reader can check it.
"""
import hashlib
import json
import os
import re
import subprocess
import uuid

from . import config, db, library, zims

TUTOR = ("You are Olam, a patient tutor for someone learning Dungeons & Dragons with the 2024 rules (SRD 5.2). "
         "Write plainly and warmly, like a friend who knows the rules well.")


def run(text, timeout=240, model=None):
    if config.API_KEY:
        return run_api(text, timeout, model)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    r = subprocess.run([config.CLAUDE, "--print", "--model", model or config.MODEL], input=text,
                       capture_output=True, text=True, timeout=timeout, env=env)
    out = (r.stdout or "").strip()
    if r.returncode != 0 or not out:
        t = " ".join((r.stderr or r.stdout or "").split())[-300:]
        raise RuntimeError("The model didn't answer: " + re.sub(r"(?i)\bclaude(\s+code)?\b", "the model", t) if t else "No answer came back")
    return out


def run_api(text, timeout=240, model=None):
    import anthropic
    client = anthropic.Anthropic(timeout=timeout)
    try:
        # A policy decline is re-run on the model Anthropic recommends for it, inside the same call.
        r = client.beta.messages.create(model=model or config.MODEL, max_tokens=16000,
                                        betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                                        messages=[{"role": "user", "content": text}])
    except anthropic.AuthenticationError:
        raise RuntimeError("The API key didn't work")
    except anthropic.RateLimitError:
        raise RuntimeError("The model is busy. Try again in a minute.")
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"The model didn't answer ({e.status_code})")
    except anthropic.APIConnectionError:
        raise RuntimeError("Couldn't reach the model")
    if r.stop_reason == "refusal":
        raise RuntimeError("The model declined to answer that")
    out = "".join(b.text for b in r.content if b.type == "text").strip()
    if not out:
        raise RuntimeError("No answer came back")
    return out


def clip(t, n):
    t = re.sub(r"\s+", " ", t or "").strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


STOP = set("a an the of to in on at for and or but is are was were be been how what why when who which does do did can could "
           "should would will with without into from by about if then than that this these those it its my your i you we they "
           "me us them as so not no yes vs versus work works get got".split())


def keywords(q):
    words = [w.lower().strip("'’") for w in re.findall(r"[\w’']+", q)]
    return [w for w in words if w and w not in STOP and len(w) > 1]


def gather(q, n_rules=6, n_expert=3, n_books=2):
    """Numbered sources for a question: 2024 rules first, then expert answers, then the reader's rulebooks."""
    kw = keywords(q)
    if not kw:
        return []
    c = db.connect()
    fq = " OR ".join(f'"{w}"*' for w in kw)
    rows = c.execute("""SELECT e.id, e.name, e.kind, e.doc, e.shelf, e.edition, e.body, bm25(entries_fts, 6.0, 1.0) AS s
                        FROM entries_fts JOIN entries e ON e.rowid = entries_fts.rowid
                        WHERE entries_fts MATCH ? AND e.doc='srd-2024' AND e.kind IN ('glossary','rule','condition','spell','monster','feat','class','species','background','item','magic-item')
                        ORDER BY s LIMIT 40""", (fq,)).fetchall()
    kwset = set(kw)

    def name_hit(r):
        n = set(re.findall(r"\w+", r["name"].lower()))
        return -len(n & kwset) - sum(1 for w in kw if any(x.startswith(w[:5]) for x in n))
    rows = sorted(rows, key=lambda r: (name_hit(r), 0 if r["kind"] in ("glossary", "rule", "condition") else 1, r["s"]))
    seen, picked = set(), []
    for r in rows:                      # a condition and its glossary entry say the same thing: keep one
        if r["name"].lower() not in seen:
            seen.add(r["name"].lower()); picked.append(r)
    rows = picked[:n_rules]
    out = []
    for r in rows:
        out.append({"kind": "entry", "id": r["id"], "title": r["name"], "shelf": "rule",
                    "label": f"Rule · SRD 5.2 · {library.KIND_LABEL.get(r['kind'], r['kind'])}", "text": clip(r["body"], 1800)})
    total, paths = zims.fulltext("rpg.stackexchange.com", " ".join(kw), 12)
    pages = [p for p in (zims.page("rpg.stackexchange.com", x, full=True) for x in paths) if p and p.get("answer")]
    pages = sorted(pages, key=lambda p: -max(p["votes"], 0.5) * library.qa_weight(p))
    for p in pages[:n_expert]:
        ed = "2024 rules" if "dnd-5e-2024" in p["tags"] else ("2014 rules" if "dnd-5e-2014" in p["tags"] else ", ".join(p["tags"][:2]))
        out.append({"kind": "zim", "zim": "rpg.stackexchange.com", "path": p["path"], "title": p["title"], "shelf": "expert",
                    "label": f"Expert · RPG Stack Exchange · {ed} · {p['votes']} votes", "url": p["url"],
                    "text": "Question: " + clip(p["question"], 600) + "\nTop answer: " + clip(p["answer"], 1400)})
    rows = c.execute("""SELECT e.id, e.name, e.grp, e.body FROM entries_fts JOIN entries e ON e.rowid = entries_fts.rowid
                        WHERE entries_fts MATCH ? AND e.kind='book' AND e.shelf='rule' ORDER BY bm25(entries_fts) LIMIT ?""",
                     (fq, n_books)).fetchall()
    for r in rows:
        first = next((l.strip() for l in (r["body"] or "").split("\n") if 3 < len(l.strip()) < 70), "")
        out.append({"kind": "entry", "id": r["id"], "title": f"{r['name']} · {first or r['grp']}", "shelf": "rule",
                    "label": "Rule · your library", "text": clip(r["body"], 1200), "private": True})
    return out


def numbered(sources):
    return "\n\n".join(f"[{i}] {s['label']} — {s['title']}\n{s['text']}" for i, s in enumerate(sources, 1))


def ask(q, fresh=False):
    key = "ask:" + hashlib.sha1(" ".join(q.lower().split()).encode()).hexdigest()
    if not fresh:
        hit = db.cache_get(key)
        if hit:
            return hit
    sources = gather(q)
    if not sources:
        return {"q": q, "answer": "", "sources": [], "empty": True}
    prompt = (f"{TUTOR}\n\nAnswer the question using only the numbered sources below. Cite them inline like [1] or [2][3]. "
              "Lead with the official 2024 rules (sources marked Rule). Use expert answers for edge cases, and say so when an "
              "expert answer is about the 2014 rules or another game. If the sources don't answer the question, say that plainly "
              "instead of guessing. Keep it short: a direct answer in two or three sentences, then at most four short bullet "
              "points if they help. Plain text; bullets start with '- '. No headings.\n\n"
              f"Question: {q}\n\nSources:\n\n{numbered(sources)}")
    answer = run(prompt)
    out = {"q": q, "answer": answer, "sources": [{k: v for k, v in s.items() if k != "text"} for s in sources]}
    db.cache_put(key, out)
    return out


def summary(id, fresh=False):
    key = "summary:" + id
    if not fresh:
        hit = db.cache_get(key)
        if hit:
            return hit
    h = library.hub(id)
    if not h:
        raise KeyError(id)
    e, s = h["entry"], h["sections"]
    src = [{"label": f"Rule · {e['doc_name']}", "title": e["name"], "text": clip((e.get("body") or "") + " " + json.dumps(e.get("data") or {})[:1500], 2400)}]
    for p in s["expert"]["pages"][:3]:
        src.append({"label": "Expert · RPG Stack Exchange", "title": p["title"], "text": clip(p.get("question", "") + " " + p.get("answer", ""), 900)})
    for p in s["myth"][:2]:
        src.append({"label": "Idea · Mythology Q&A", "title": p["title"], "text": clip(p.get("question", "") + " " + p.get("answer", ""), 600)})
    prompt = (f"{TUTOR}\n\nWrite two or three plain sentences that sum up \"{e['name']}\" for a new player or GM: what it is, and "
              "the one or two things that matter most at the table. Use only the numbered sources and cite them like [1]. "
              "No preamble, no markdown.\n\n" + numbered(src))
    out = {"text": run(prompt), "sources": [{k: v for k, v in x.items() if k != "text"} for x in src]}
    db.cache_put(key, out)
    return out


DM_RULES = ("You are the Game Master for a short solo D&D adventure (2024 rules, SRD 5.2) with a brand-new player who is "
            "learning to play. Keep each reply under 140 words. Describe the scene vividly but briefly, then ask what they do. "
            "When the outcome is uncertain, ask the player to roll and name the roll exactly, like 'Roll a Dexterity (Stealth) "
            "check' or 'Make an attack roll'; they roll in the app and tell you the total. Set the DC yourself and keep it secret "
            "until after the roll. Whenever a rule comes up for the first time, add one short line at the end that starts with "
            "'Rule:' and explains it in plain words. Be generous and fun; never kill the character. The adventure should "
            "take about 15 exchanges and include one conversation, one bit of exploration and one small fight. Write plain "
            "text: no markdown, no asterisks; put the Rule line on its own last line.")


def dm_turn(chat_id, message, character=""):
    c = db.connect()
    r = c.execute("SELECT messages FROM chats WHERE id=?", (chat_id,)).fetchone() if chat_id else None
    msgs = json.loads(r[0]) if r else []
    if not chat_id:
        chat_id = uuid.uuid4().hex[:12]
    if message:
        msgs.append({"who": "you", "text": message})
    transcript = "\n\n".join(("PLAYER: " if m["who"] == "you" else "GM: ") + m["text"] for m in msgs[-30:])
    start = "" if msgs else "Start the adventure now: set the opening scene in two short paragraphs and ask what the character does."
    prompt = (f"{DM_RULES}\n\nThe player's character: {character or 'a level 1 adventurer the player will describe'}.\n\n"
              f"{('Story so far:' + chr(10) + transcript) if transcript else ''}\n\n{start}\nGM:")
    reply = run(prompt, timeout=240)
    reply = re.sub(r"^\s*GM:\s*", "", reply)
    msgs.append({"who": "gm", "text": reply})
    c.execute("INSERT OR REPLACE INTO chats(id,kind,messages,updated) VALUES (?,?,?,CURRENT_TIMESTAMP)", (chat_id, "dm", json.dumps(msgs)))
    c.commit()
    return {"id": chat_id, "messages": msgs}


def chat(chat_id):
    r = db.connect().execute("SELECT messages FROM chats WHERE id=?", (chat_id,)).fetchone()
    return {"id": chat_id, "messages": json.loads(r[0]) if r else []}


def interview(rel, message, history):
    """An NPC answers in character, from their vault note. A detail worth keeping comes back on a last line, 'New: ...'."""
    from . import world
    _, _, text = world.read(rel)
    name = rel.rsplit("/", 1)[-1].removesuffix(".md")
    talk = "\n".join(("DM: " if h.get("who") == "you" else f"{name.upper()}: ") + str(h.get("text", ""))[:800]
                     for h in (history or [])[-12:])
    prompt = (f"You are {name}, a character in the DM's Dungeons & Dragons world. The DM is interviewing you to get to know "
              "you before a game. Stay in character, speak in your own voice, and keep each reply under 90 words. Everything "
              "you say must fit your note below; you may invent small, consistent details, but never contradict the note. "
              "Guard your secrets as the character would, though a good question may make you slip. If you invent a detail "
              "worth remembering, end with one last line that starts 'New: ' and states it plainly in the third person. "
              f"No markdown.\n\nYour note:\n{text[:6000]}\n\n{('Conversation so far:' + chr(10) + talk) if talk else ''}\n"
              f"DM: {message}\n{name.upper()}:")
    reply = run(prompt, timeout=180)
    reply = re.sub(rf"^\s*{re.escape(name.upper())}:\s*", "", reply)
    new = ""
    m = re.search(r"\n?\s*New:\s*(.+)\s*$", reply)
    if m:
        new, reply = m.group(1).strip(), reply[:m.start()].strip()
    return {"reply": reply, "new": new}
