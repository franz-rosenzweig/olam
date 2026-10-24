"""The Kiwix archives (ZIM files), searched in place with libzim: titles, full text, and a page's gist.

Nothing from them is copied into Olam's database; each archive carries its own full-text index.
"""
import re
import threading
from html import unescape

from libzim.reader import Archive
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher

from . import config

_lock = threading.Lock()
_zims = None


def all():
    """name -> {archive, book, shelf, label, ...}, one per ZIM file in config.ZIM_DIR."""
    global _zims
    with _lock:
        if _zims is None:
            out = {}
            for f in sorted(config.ZIM_DIR.glob("*.zim")):
                meta = next((dict(v, key=k) for k, v in config.ZIMS.items() if f.name.startswith(k)), None)
                if not meta:
                    continue
                try:
                    out[meta["key"]] = dict(meta, archive=Archive(str(f)), book=f.stem)
                except RuntimeError:
                    continue
            _zims = out
        return _zims


def kiwix_url(z, path):
    return f"{config.KIWIX_URL}/content/{z['book']}/{path}" if config.KIWIX_URL else ""


def is_page(z, path):
    """A question or an article, not a tag listing, a user page or a talk page."""
    if z["kind"] == "qa":
        return bool(re.match(r"questions/\d+/", path))
    return "Talk:" not in path and "User:" not in path


def titles(key, q, n=10):
    z = all().get(key)
    if not z or not q.strip():
        return 0, []
    s = SuggestionSearcher(z["archive"]).suggest(q)
    total = s.getEstimatedMatches()
    return total, [p for p in s.getResults(0, min(n * 2, total)) if is_page(z, p)][:n]


def fulltext(key, q, n=10):
    z = all().get(key)
    if not z or not q.strip():
        return 0, []
    s = Searcher(z["archive"]).search(Query().set_query(q))
    total = s.getEstimatedMatches()
    return total, [p for p in s.getResults(0, min(n * 2, total)) if is_page(z, p)][:n]


def text_of(html):
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|pre|blockquote)\s*>|<br\s*/?>", "\n", html)
    t = unescape(re.sub(r"<[^>]+>", " ", html))
    t = re.sub(r"[ \t ]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n\n", t).strip()


def clip(t, n):
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def page(key, path, full=False):
    """A page's title and gist. Q&A pages also give votes, answers, tags and the best answer."""
    z = all().get(key)
    if not z:
        return None
    try:
        e = z["archive"].get_entry_by_path(path)
        if e.is_redirect:
            e = e.get_redirect_entry()
        html = bytes(e.get_item().content).decode("utf8", "replace")
    except KeyError:
        return None
    out = {"zim": key, "path": e.path, "title": e.title, "shelf": z["shelf"], "source": z["label"],
           "license": z["license"], "url": kiwix_url(z, e.path), "note": z.get("note", ""), "original": original_url(key, e.path)}
    if z["kind"] == "qa":
        qa = re.search(r'datetime="asked[^"]*".{0,3000}?s-user-card--link">(.*?)</a>', html, re.S)
        out["asker"] = unescape(re.sub(r"<[^>]+>", "", qa.group(1))).strip() if qa else ""
        q = re.search(r'id="question"[^>]*data-score="(-?\d+)"', html)
        a = re.search(r'itemprop="answerCount">(\d+)<', html)
        out["votes"] = int(q.group(1)) if q else 0
        out["answers"] = int(a.group(1)) if a else 0
        out["tags"] = sorted(set(re.findall(r'href="[./]*questions/tagged/([^"]+)" class="post-tag', html)))[:6]
        bodies = re.findall(r'itemprop="text">(.*?)</div>\s*(?:<div class="mt24|<div class="mt24 mb12"|</div>)', html, re.S)
        qtext = text_of(bodies[0]) if bodies else ""
        best = None
        for m in re.finditer(r'<div id="answer-(\d+)" class="answer ?( accepted-answer)?\s*"[^>]*data-score="(-?\d+)"', html):
            rest = html[m.end():]
            body = re.search(r'itemprop="text">(.*?)</div>', rest, re.S)
            who = re.search(r'datetime="answered[^"]*".{0,3000}?s-user-card--link">(.*?)</a>', rest[:40000], re.S)
            cand = {"score": int(m.group(3)), "accepted": bool(m.group(2)), "text": text_of(body.group(1)) if body else "",
                    "author": unescape(re.sub(r"<[^>]+>", "", who.group(1))).strip() if who else ""}
            if best is None or (cand["accepted"] and not best["accepted"]) or (cand["score"] > best["score"] and not best["accepted"]):
                best = cand
        out["question"] = qtext if full else clip(qtext, 360)
        if best:
            out["answer"] = best["text"] if full else clip(best["text"], 700)
            out["answer_score"] = best["score"]
            out["accepted"] = best["accepted"]
            out["answerer"] = best["author"]
    else:
        main = re.search(r'(?s)<div[^>]*id="mw-content-text"[^>]*>(.*)', html)
        t = text_of(main.group(1) if main else html)
        t = re.sub(r"^\s*" + re.escape(e.title) + r"\s*", "", t)
        out["text"] = t if full else clip(t, 500)
    return out


def original_url(key, path):
    """Where a page lives on the open web, for credit and for reading it there."""
    if key.endswith("stackexchange.com"):
        return f"https://{key}/{path}"
    if key == "dandwiki":
        return "https://www.dandwiki.com/wiki/" + path.split("/", 1)[-1]
    return ""


def homebrew_note(p):
    """A homebrew page's kind from its title: "Inferno Owlbear (5e Creature)" -> ("Inferno Owlbear", "5e creature")."""
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", p["title"])
    return (m.group(1), m.group(2).lower()) if m else (p["title"], "")
