<sub>[Olam docs](README.md) › Running your own copy</sub>

# Your own server

Running your own copy of Olam means one small Python program on a machine that stays on, and one folder that holds everything it keeps. This page covers the settings, the commands, keeping it running, the demo, updating and backups. If you haven't installed it yet, start with [Install](install.md).

## The data folder

Everything Olam keeps lives in one folder: `data/` next to the code, `/data` in the container, or wherever `OLAM_DATA` points.

| | What it is |
|---|---|
| `olam.db` | The library and its search index, your progress on the Road, Review, saved answers and summaries, Game Master chats, and the Table |
| `auth.json` | Your password (hashed, never stored as you typed it) and the secret that signs the sign-in cookie |
| `olam.env` | Your settings (see below) |
| `books.json` | Corrections and shelves for your Calibre books (see [Where it all comes from](sources.md#your-own-books)) |
| `srd/`, `open5e/`, `zim/` | The downloads from `fetch` |
| `pictures/` | The pictures from `fetch pictures`, and `index.json`, which says where each one came from and its license |

Your vault is NOT in here. It stays wherever it is, and Olam only reads and writes it there.

## Settings

Every setting is an environment variable, and any of them can also go in `olam.env` in the data folder, which is the easiest place, since the service and the command line both read it. `olam.env.example` lists every one, and every line is optional.

| Setting | What it does | Default |
|---|---|---|
| `OLAM_DATA` | The data folder. This one has to be set in the environment, since `olam.env` lives in it | `data/` |
| `OLAM_HOSTS` | The addresses to listen on, comma-separated | `127.0.0.1` |
| `OLAM_PORT` | The port | `8462` |
| `OLAM_URL` | Olam's own address, for the links it writes into vault notes | worked out from the above |
| `OLAM_VAULT` | Your Obsidian vault | none |
| `OLAM_CALIBRE` | A Calibre library, the folder with `metadata.db` | none |
| `OLAM_KIWIX_URL` | kiwix-serve, for **Open in Kiwix**, like `http://localhost:8461` | none |
| `ANTHROPIC_API_KEY` | A Claude API key, for the AI features | none |
| `OLAM_CLAUDE` | Where the Claude CLI is, if it isn't on the path | found on its own |
| `OLAM_MODEL` | The model for the AI features | `claude-sonnet-5-5` |
| `OLAM_AI` | `0` turns the AI features off | on, when there's a key or the CLI |
| `OLAM_DEMO` | `1` runs Olam as a public demo (see below) | off |
| `OLAM_DB` | The database file, for a demo next to your own copy | `olam.db` in the data folder |

Restart Olam after you change a setting. **Settings** in the app is where you change your password, sign out other browsers, and pick **Auto**, **Light** or **Dark** (Auto follows your phone or computer). It also shows what this copy is connected to: the vault, the AI and its model, Kiwix, Calibre and how many books, the archives, and how many entries are in the library.

## The commands

All of them run as `.venv/bin/python -m olam.cli <command>`, or `docker compose run --rm olam <command>` with Docker.

| Command | What it does |
|---|---|
| `fetch` | Downloads the rules: Open5e's data (with git) and the SRD 5.2.1 PDF, about 45 MB. Run it again to update Open5e's data. |
| `fetch zims` | Downloads the newest Kiwix archives, about 1.5 GB, and removes older copies. Name one to fetch only that one, like `fetch zims dandwiki`. Restart Olam afterwards. |
| `fetch pictures` | Finds pictures on Wikipedia and Wikimedia Commons for the library's monsters, gear, classes and species, about 25 MB. Run it after `ingest`. Olam shows them straight away. |
| `ingest` | Builds the library from the downloads, about a minute. `ingest open5e`, `ingest srd` or `ingest calibre` rebuilds just one part. |
| `passwd` | Sets the password, at least 8 characters, and signs out every browser. |
| `vault-setup` | Makes the vault's World folders, templates and blank map. Never overwrites anything. |
| `serve` | Runs the web app. |

## Keeping it running

`systemd/olam.service` is a user service. Copy it to `~/.config/systemd/user/`, change the paths in it if Olam isn't in `~/olam`, and turn it on:

```bash
systemctl --user daemon-reload && systemctl --user enable --now olam
loginctl enable-linger $USER        # so it starts at boot, without you logging in
```

The service puts `~/.local/bin` on the path, which is where the Claude CLI usually is. With Docker, `restart: unless-stopped` in `compose.yaml` does the same job.

## Reaching it from your other devices

Out of the box, Olam only listens on the computer it runs on. There are a few ways to reach it from your phone or another computer:

- **On your home network or a VPN like Tailscale:** add the computer's address there to `OLAM_HOSTS`, like `OLAM_HOSTS=127.0.0.1,192.168.1.20`, and open `http://192.168.1.20:8462`.
- **Behind a reverse proxy** like Caddy or nginx: Olam only uses relative paths, so it works at the root of a domain or under a path like `/olam/`. Behind HTTPS, the sign-in cookie is marked secure on its own.
- **In Docker,** it already listens on every address inside the container, and `compose.yaml` publishes port 8462.

If you put it on the internet, the password is all that stands in front of it, so make it a good one. Olam allows 8 wrong passwords per address every 15 minutes, and **Settings** has **Sign out other browsers** if you ever lose a device.

Set `OLAM_URL` to the address you actually use, so the "by way of Olam" links in your vault notes open the right place.

## Kiwix

Olam reads the archives on its own, so Kiwix is optional. It's nice when you want to browse a whole archive, like reading RPG Stack Exchange by tag. With Docker, `docker compose --profile kiwix up -d` starts it on port 8461. Without Docker, run `kiwix-serve` on the files in `data/zim/`. Then set `OLAM_KIWIX_URL`, and archive pages get an **Open in Kiwix** button. It only shows when you open Olam on the same host name as Kiwix, because that's the only place the link would work.

## The public demo

`OLAM_DEMO=1` runs Olam as a public demo, like the one at [stuffs.tiresia.xyz/olam](https://stuffs.tiresia.xyz/olam/). It has the SRDs, the archives and only the Creative Commons third-party books, with no sign-in, no AI, no Calibre books and no vault, and each visitor's progress stays in their own browser. It's limited to 240 requests a minute per address, and it never reads `olam.env`.

Give it its own library, so none of your own books end up in it. Built with `OLAM_DEMO=1`, the library also leaves out the Open Game License books:

```bash
OLAM_DEMO=1 OLAM_DB=data/demo.db .venv/bin/python -m olam.cli ingest open5e srd
```

`systemd/olam-demo.service` runs it next to your own copy, on port 8463. Put a reverse proxy in front of it.

## Updating

```bash
cd ~/olam && git pull
.venv/bin/pip install -r requirements.txt
systemctl --user restart olam
```

With Docker, `git pull`, then `docker compose build` and `docker compose up -d`. If an update changes how the library is built, run `ingest` again too; it never hurts to. To get the newest sources, run `fetch` (and `fetch zims`), then `ingest`, then restart.

## Backups

The things you can't get back are in two places:

- **The data folder**, mainly `olam.db` (your progress, Review, and the fight in progress), `auth.json`, `olam.env` and `books.json`. The downloads can always be fetched again, so you can leave `srd/`, `open5e/` and `zim/` out of your backup.
- **Your vault**, which is your whole world. Back it up the way you'd back up any folder of notes.

If something doesn't work for you, [open an issue](https://github.com/franz-rosenzweig/olam/issues) and I'll take a look.

<sub>Next: [How it's made](developing.md) →</sub>
