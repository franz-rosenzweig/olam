<sub>[Olam docs](README.md) › Under the hood</sub>

# How it's made

Olam is small on purpose: FastAPI and SQLite on the server, plain JavaScript in the browser with no build step, and libzim to read the archives right where they are. This page is a map of the code, how a lesson is written, and how to check a change. If you'd like to add a lesson or a source and get stuck, [open an issue](https://github.com/franz-rosenzweig/olam/issues) and I'll help.

## Working from the code

Set it up the same way as [Install](install.md) without Docker, then run `serve` and reload the browser as you change things. There's nothing to build: the server serves `web/` as it is, and a change to a Python file needs a restart.

## The code

| | |
|---|---|
| `olam/config.py` | Every setting, read from the environment and `olam.env`, and the list of archives with their shelves |
| `olam/app.py` | The web API and the guard in front of it: sign-in, the demo's limits, and what's off without the AI |
| `olam/server.py` | Runs the app on each address in `OLAM_HOSTS` |
| `olam/cli.py` | `fetch`, `ingest`, `passwd`, `vault-setup` and `serve` |
| `olam/db.py` | The SQLite database: `docs` (the books), `entries` and their full-text index, `progress`, `cache` and `chats` |
| `olam/fetch.py` | Downloads the sources from where they're published |
| `olam/ingest/` | Builds the library: `open5e.py` (the SRDs and the third-party books), `srd_pdf.py` (the 2024 Rules Glossary, from the PDF) and `calibre.py` (your books) |
| `olam/library.py` | Search, browsing, and the hub that puts a wiki page together from every shelf |
| `olam/zims.py` | The Kiwix archives: title and full-text search, and a page's question and best answer |
| `olam/learn.py` | The Road, progress, Review and the Atlas |
| `olam/ai.py` | Everything Olam asks Claude, through the API or the CLI, always from numbered sources |
| `olam/vault.py` | Notes in the plugins' formats: statblocks, encounters, dice lines, templates and the map |
| `olam/world.py` | Map, People and Table: reading notes and changing only the lines that need it |
| `olam/auth.py` | The password (scrypt) and the signed cookie |
| `web/app.js` | The shell, the router, and the Codex, wiki, Ask, Review, Credits and Settings pages |
| `web/learn.js` | The Road, a lesson's four steps and their exercises, and the Atlas |
| `web/world.js` | Map, People, Table and the players' screen |
| `lessons/road.json` | The lessons |
| `android/` | The Android app (see [its README](../android/README.md)) |
| `tools/walk.py` | A walk through the app in headless Chrome, with screenshots |

## How a lesson is written

The whole Road is one file, `lessons/road.json`, with three parts: `weeks` (the six week names), `regions` (the Atlas, each with the rules in it), and `stops`. A stop looks like this:

```json
{
  "n": 6, "id": "advantage", "title": "Advantage & disadvantage", "track": "Rules", "minutes": 25,
  "teaches": ["srd-2024/glossary/advantage", "srd-2024/glossary/heroic-inspiration"],
  "read": { "lead": "...", "cards": [], "points": [], "lists": [], "sources": [] },
  "see": { "text": "...", "chips": [], "roll": {} },
  "do": { "type": "advantage" },
  "check": [ { "q": "...", "opts": ["...", "...", "..."], "correct": 1, "why": "...", "src": "srd-2024/rule/..." } ]
}
```

- `teaches` is the list of rules (library entry IDs) that clear on the Atlas when the stop is done.
- `read` has a `lead` paragraph, then optional `cards` (`title`, `text`, `tone`), `points` (short lines, with `**bold**` for the start) and `lists` (`title`, `items`). Its `sources` can be a library entry (`{"id": ...}`), an archive search (`{"zim": "rpg.stackexchange.com", "q": "..."}`), the reader's own books (`{"books": "rule", "q": "..."}`), or a page of the Codex (`{"browse": "monster", "label": "..."}`). Archive and book sources are searched when the lesson opens, so they find whatever this copy of Olam has.
- `see` is either a scene with a `roll` (`bonus`, `target`, `target_label`, `mode` of `normal`, `adv` or `dis`, and the `dice` it shows) or a short exchange in `lines` (`who`, `text`, `tag`).
- `do` names an exercise: `sort` (with `prompt`, `buckets` and `items` of `{t, a}`), `modifier`, `array`, `dm` or `advantage`. The exercises themselves are in `web/learn.js`.
- `check` is the questions. `correct` is the index of the right option, `why` is shown after an answer, and `src` is the rule it comes from.

A stop with `"outline": true` and only a `read` is an outline, which shows a **Mark as read** button instead of the four steps. That's how stops 7 to 18 are written for now, so the easiest way to help is to turn one of them into a full lesson.

## Adding an archive

The archives are listed in `ZIMS` in `olam/config.py`, by the start of the file name, each with its shelf, label, license and kind (`qa` for Stack Exchange sites, `wiki` for a wiki). `olam/fetch.py` has where each one lives on Kiwix's download server. Any `.zim` file in `data/zim/` whose name matches is picked up when Olam starts. A new source always gets a shelf, because the badge is the whole point.

## Checking a change

`tools/walk.py OUTDIR` signs in, walks every screen in a headless Chrome running in a container (`OLAM_CHROME`), saves a screenshot of each, and reports any JavaScript errors. `--mobile` does it at phone size. It's worth running after any change to the web app, because it catches the screen you forgot to look at.

For anything that touches the vault, I'd point `OLAM_VAULT` at a copy of a vault, not your real one, until you're sure it only changes what it should.
