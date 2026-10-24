"""Calibre-Web's library (read only) into Olam: each EPUB as sections of about a page, private to this server.

Shelves come from config.BOOKS (books.json in the data folder); every other book is an "idea" (fiction, myth, history). The text never
leaves the server: these entries are private and Olam shows only short passages with a link to the book.
"""
import re
import sqlite3
import zipfile
from html import unescape
from pathlib import Path

from .. import config, db

CHUNK = 1800


def books():
    con = sqlite3.connect(f"file:{config.CALIBRE / 'metadata.db'}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute("""
        SELECT b.id, b.title, b.path, b.pubdate,
          (SELECT group_concat(a.name, ', ') FROM authors a JOIN books_authors_link l ON l.author=a.id WHERE l.book=b.id) AS authors,
          (SELECT d.name FROM data d WHERE d.book=b.id AND d.format='EPUB') AS epub
        FROM books b""").fetchall()
    con.close()
    return rows


def spine_texts(path):
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    container = z.read("META-INF/container.xml").decode("utf8", "replace")
    opf_path = re.search(r'full-path="([^"]+)"', container).group(1)
    opf = z.read(opf_path).decode("utf8", "replace")
    base = opf_path.rsplit("/", 1)[0] + "/" if "/" in opf_path else ""
    manifest = {m.group(1): m.group(2) for m in re.finditer(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf)}
    manifest.update({m.group(2): m.group(1) for m in re.finditer(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)})
    for idref in re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf):
        href = manifest.get(idref)
        if not href:
            continue
        p = base + unescape(href)
        if p not in names:
            continue
        html = z.read(p).decode("utf8", "replace")
        head = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.S | re.I)
        title = clean(head.group(1)) if head else ""
        body = re.sub(r"(?is)<(script|style|head)[^>]*>.*?</\1>", " ", html)
        body = re.sub(r"(?i)</(p|div|h[1-6]|li|tr|br)\s*>|<br\s*/?>", "\n", body)
        text = clean_keep_lines(re.sub(r"<[^>]+>", " ", body))
        if text:
            yield title, text


def clean(s):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def clean_keep_lines(s):
    lines = [re.sub(r"[ \t ]+", " ", unescape(x)).strip() for x in s.split("\n")]
    return "\n".join(x for x in lines if x)


def chunks(text):
    paras, cur = text.split("\n"), ""
    for p in paras:
        if len(cur) + len(p) > CHUNK and cur:
            yield cur
            cur = ""
        cur += (p + "\n\n")
    if cur.strip():
        yield cur


def run(c):
    if not config.CALIBRE:
        return 0, 0
    c.execute("DELETE FROM entries WHERE doc LIKE 'calibre/%'")
    c.execute("DELETE FROM docs WHERE key LIKE 'calibre/%'")
    n_books = n = 0
    for b in books():
        if not b["epub"]:
            continue
        path = config.CALIBRE / b["path"] / (b["epub"] + ".epub")
        if not path.exists():
            continue
        over = config.BOOKS.get(b["id"], {})
        title = over.get("title") or b["title"]
        author = over.get("author") or b["authors"] or ""
        shelf = over.get("shelf", "idea")
        edition = over.get("edition", "")
        key = f"calibre/{b['id']}"
        db.put_doc(c, key, title, author, "your library", "", shelf, edition, private=1)
        try:
            sections = list(spine_texts(path))
        except (zipfile.BadZipFile, KeyError, AttributeError, OSError):
            continue
        n_books += 1
        i = 0
        chapter = ""
        for title_h, text in sections:
            chapter = title_h or chapter
            for part in chunks(text):
                i += 1
                db.put(c, id=f"{key}/{i}", kind="book", name=title, doc=key, shelf=shelf, edition=edition,
                       grp=chapter, summary=author, body=part, private=1, data={"section": i, "note": over.get("note", "")})
                n += 1
    c.commit()
    return n_books, n
