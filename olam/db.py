"""Olam's SQLite file: the library index (entries + full text) and the reader's own state."""
import json
import sqlite3
import threading

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
  key TEXT PRIMARY KEY, name TEXT, publisher TEXT, license TEXT, url TEXT,
  shelf TEXT, edition TEXT, private INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS entries (
  rowid INTEGER PRIMARY KEY,
  id TEXT UNIQUE,          -- srd-2024/monster/owlbear, calibre/12/3
  kind TEXT,               -- monster, spell, magic-item, item, condition, rule, glossary, class, species, background, feat, book
  name TEXT,
  slug TEXT,
  doc TEXT,                -- docs.key
  shelf TEXT,              -- rule, third, expert, craft, idea, yours
  edition TEXT,            -- 2024, 2014, a5e, 4e
  grp TEXT,                -- a rule's chapter, a book's chapter
  summary TEXT,            -- one line for lists
  body TEXT,               -- the text, markdown
  data TEXT,               -- JSON: a stat block, a spell's header
  private INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS entries_name ON entries(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS entries_doc ON entries(doc);
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
  name, body, content='entries', content_rowid='rowid', tokenize='porter unicode61'
);
CREATE TABLE IF NOT EXISTS progress (
  stop TEXT PRIMARY KEY, status TEXT, steps TEXT, answers TEXT, updated TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS cache (
  key TEXT PRIMARY KEY, value TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chats (
  id TEXT PRIMARY KEY, kind TEXT, messages TEXT, updated TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

_local = threading.local()


def connect():
    c = getattr(_local, "conn", None)
    if c is None:
        config.DATA.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(config.DB, timeout=30)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.executescript(SCHEMA)
        _local.conn = c
    return c


def put_doc(c, key, name, publisher="", license="", url="", shelf="rule", edition="", private=0):
    c.execute("INSERT OR REPLACE INTO docs(key,name,publisher,license,url,shelf,edition,private) VALUES (?,?,?,?,?,?,?,?)",
              (key, name, publisher, license, url, shelf, edition, private))


def clear_doc(c, key):
    c.execute("DELETE FROM entries WHERE doc=?", (key,))


def put(c, *, id, kind, name, doc, shelf, edition="", grp="", summary="", body="", data=None, private=0, slug=""):
    c.execute("INSERT OR REPLACE INTO entries(id,kind,name,slug,doc,shelf,edition,grp,summary,body,data,private) "
              "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (id, kind, name, slug or id.rsplit("/", 1)[-1], doc, shelf, edition, grp, summary, body,
               json.dumps(data, ensure_ascii=False) if data is not None else None, private))


def reindex(c):
    c.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")
    c.commit()


def cache_get(key):
    r = connect().execute("SELECT value FROM cache WHERE key=?", (key,)).fetchone()
    return json.loads(r[0]) if r else None


def cache_put(key, value):
    c = connect()
    c.execute("INSERT OR REPLACE INTO cache(key,value) VALUES (?,?)", (key, json.dumps(value, ensure_ascii=False)))
    c.commit()
