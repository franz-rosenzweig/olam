<sub>[Olam docs](README.md) › Getting started</sub>

# Install

Olam runs on a computer that stays on, like a home server, a NAS or a small cloud machine, and you open it in a browser from anywhere you can reach that computer. There are two ways to set it up: with Docker, which is the easiest, or straight from the code with Python. Either way it takes about ten minutes, plus the downloads.

If you just want to see it first, the demo at [stuffs.tiresia.xyz/olam](https://stuffs.tiresia.xyz/olam/) needs nothing installed.

## With Docker

You need Docker with Compose, and git.

```bash
git clone https://github.com/franz-rosenzweig/olam.git && cd olam
docker compose build
docker compose run --rm olam fetch          # the SRD 5.2.1 and Open5e's data, about 45 MB
docker compose run --rm olam ingest         # build the library, about a minute
docker compose run --rm olam passwd         # your password
docker compose up -d
```

Then open http://localhost:8462 and sign in. Everything Olam keeps (its library, the downloads and your password) lives in the `olam-data` volume, so rebuilding the container never loses anything.

## Without Docker

You need Python 3.13 or newer, and git.

```bash
git clone https://github.com/franz-rosenzweig/olam.git ~/olam && cd ~/olam
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m olam.cli fetch
.venv/bin/python -m olam.cli ingest
.venv/bin/python -m olam.cli passwd
.venv/bin/python -m olam.cli serve          # http://127.0.0.1:8462
```

Here everything lives in `data/` next to the code. To keep Olam running after you close the terminal, [Your own server](server.md) shows how to set it up as a service.

## The password

`passwd` asks for a password twice, and it has to be at least 8 characters. There's one password for the whole copy, since it's meant for you (and maybe whoever you play with). Once you're signed in, a browser stays signed in for a year. You can change the password later in **Settings**, and changing it signs out every other browser.

## The archives

The first `fetch` only gets the rules. The archives (RPG Stack Exchange, Mythology and Worldbuilding Q&A, and D&D Wiki) are about 1.5 GB more, and they're what fills the Expert, Craft and Idea shelves on every wiki page. I'd get them, because they're a big part of what makes Olam more than a rules search.

With Docker:

```bash
docker compose run --rm olam fetch zims
docker compose restart olam
docker compose --profile kiwix up -d        # optional: read them in full in Kiwix on :8461
```

Without Docker:

```bash
.venv/bin/python -m olam.cli fetch zims
```

Then restart Olam. Olam reads the archives directly, so Kiwix is only for when you want to browse a whole archive on its own.

## The pictures

Olam can show pictures too: old paintings of goblins and griffons, museum photos of swords and armour, and photos of the real animals behind the beasts. They come from Wikipedia and Wikimedia Commons, every one of them under a free license, and they're about 25 MB. Get them after `ingest`, since Olam looks them up by the names in your library:

```bash
docker compose run --rm olam fetch pictures       # or: .venv/bin/python -m olam.cli fetch pictures
```

There's no need to restart. Anything without a picture still has its icon, so Olam looks fine without them, just a lot less colourful.

## Turning on the AI

Ask, Summarize, the Game Master and the interviews use Claude. There are two ways to connect it:

- **An API key.** With Docker, put `ANTHROPIC_API_KEY=...` in a `.env` file next to `compose.yaml` before `up`. Without Docker, put the same line in `data/olam.env`.
- **Your Claude subscription.** Install the Claude CLI and sign in to it as the same user that runs Olam. Olam finds it on its own, so there's nothing to set.

With neither, the AI features are simply off and the rest of Olam works the same. [Ask and the AI](ask-and-the-ai.md) has the details.

## Your vault

To use the Map, People and Table screens, point Olam at an Obsidian vault. A new, empty vault is best. With Docker, uncomment the two vault lines in `compose.yaml` (the volume and `OLAM_VAULT`). Without Docker, add `OLAM_VAULT=/home/you/Obsidian/Olam` to `data/olam.env`. Then run `vault-setup` once:

```bash
.venv/bin/python -m olam.cli vault-setup        # or: docker compose run --rm olam vault-setup
```

It makes the World folders, a blank parchment map and the templates, and it never overwrites anything. [Your vault](the-vault.md) explains the rest.

## On your phone

The web app already fits a phone, so you can just open your server's address in the browser. On Android there's also a small app that shows Olam full screen, with Back and your sign-in working the way you'd expect. Get `Olam-<version>.apk` from [Releases](https://github.com/franz-rosenzweig/olam/releases), or add the repo to [Obtainium](https://github.com/ImranR98/Obtainium) so it updates itself. The first time it opens, it asks for your server's address, or opens the demo.

## Next step

Open Olam, sign in, and start the first lesson on the Learn screen. If you'd like a plan for your first evening, read [A first evening with Olam](first-evening.md).

<sub>Next: [A first evening with Olam](first-evening.md) →</sub>
