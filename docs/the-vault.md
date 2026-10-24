<sub>[Olam docs](README.md) › Building your world</sub>

# Your vault

A DM needs a world, and I didn't want that world locked inside an app. So Olam keeps it in an [Obsidian](https://obsidian.md) vault: a plain folder of Markdown notes that you own, can open in Obsidian on any device, and can back up or sync however you like. Olam reads the vault for the Map, People and Table screens, and writes notes into it when you ask it to.

The nice part is that Olam writes its notes in the formats of six community Obsidian plugins, so when you open the vault in Obsidian, you see the SAME world: the statblocks render, the map has its pins, and the encounters are ready for the initiative tracker.

## Setting it up

1. Make a new vault in Obsidian, or pick a folder for one. A new vault is best, so your world doesn't get mixed up with your other notes.
2. Tell Olam where it is: `OLAM_VAULT=/home/you/Obsidian/Olam` in `olam.env` (with Docker, uncomment the two vault lines in `compose.yaml`).
3. Run `vault-setup` once, and restart Olam:

```bash
.venv/bin/python -m olam.cli vault-setup        # or: docker compose run --rm olam vault-setup
```

`vault-setup` makes the folders, the templates and a blank parchment map, and tells you what it made. It never touches anything that's already there, so it's safe to run again.

4. In Obsidian, install the community plugins below. Olam works without them, but they're what make the notes come alive in Obsidian.

## The six plugins

| Plugin | What Olam writes for it |
|---|---|
| **Fantasy Statblocks** | A `statblock` block in every bestiary note, so the monster shows as a proper statblock |
| **Initiative Tracker** | An `encounter` block in each encounter note, with each monster's count, HP, AC, initiative and XP |
| **Dice Roller** | `dice:` lines, like `dice: 2d20kh+5` for an attack with advantage, in lesson notes and session notes |
| **Leaflet** | The world map note, with a pin for every note in `World/Places` that has a `location` |
| **Calendarium** | Session notes date themselves with `fc-date`, so your sessions land on your world's calendar |
| **Relations** | People name their ties (ally, enemy, family, friend, rival, mentor) in their frontmatter, and Relations draws the web |

## The folders

| Folder | What goes in it |
|---|---|
| `World/Maps` | `World map.png` (the picture) and `World map.md` (the Leaflet note) |
| `World/Places` | One note per place, with `location`, `type`, `visited` and `dm-only` in its frontmatter |
| `World/People` | One note per person: role, home, ties, what they want and fear, what the party knows, and their secrets |
| `World/Bestiary` | One note per monster, with its statblock |
| `World/Encounters` | One note per fight, with its Initiative Tracker block |
| `World/Sessions` | Your session notes |
| `World/Party.md` | The party: each character's name, HP, AC and initiative bonus |
| `Learn` | Your lesson notes, from **Write it in your words** |
| `Templates` | NPC, Place, Session, Monster and Encounter templates, for making notes by hand in Obsidian |

## Your map

`vault-setup` gives you a blank parchment sheet as `World/Maps/World map.png`. When you have a real map, whether you drew it, made it in a map maker, or found one you like, save it over that file with the same name, and Olam and Leaflet both pick it up. If it's a different shape from the blank sheet, also delete the three `bounds` lines in `World map.md`, and the next time you open Map, Olam writes new ones that fit your picture. It's best to do that before you place any pins. [Map and People](map-and-people.md) shows how to put places on it.

## From the Codex into your world

On any monster's wiki page there are two buttons:

- **Add to vault** makes a note for it in `World/Bestiary`, with its full statblock for Fantasy Statblocks, its CR, the book it came from and its license, and empty **Notes** and **In my world** sections for your own ideas. The 2024 version gets the plain name, and any other version says which one it is, like "Goblin (2014)", so you can keep both.
- **Add to encounter** adds it to `World/Encounters/Next encounter.md`, ready for the Initiative Tracker and for Olam's [Table](the-table.md). Press it again to add another one of the same monster. It makes the bestiary note too, if there isn't one yet, and keeps a running total of the encounter's XP.

When you're happy with the next encounter, you can rename the note to something like "Low Water at the Abbey" in Obsidian, and the next **Add to encounter** starts a new "Next encounter".

## What Olam changes, and what it doesn't

Olam is careful with your notes, because they're yours.

- It **makes** notes (a bestiary entry, a lesson note, a new place or person) and never overwrites one that's already there.
- It **edits** only the lines it needs to. Moving a pin changes the `location` line, marking a place visited changes the `visited` line, revealing a secret moves that one bullet, and so on. Everything else in the note stays exactly the way you wrote it.
- The one note it rewrites is `World/Encounters/Next encounter.md`, when you add a monster to it.
- It never reads or writes anything outside the vault, and it skips Obsidian's own `.obsidian` and `.trash` folders.

## Your notes on wiki pages

When something in the Codex comes up in your notes, like a monster you've put in a place or a rule you wrote about in a lesson note, it shows in the **In your world** section of its wiki page, with a few words of your note around it. That's the Yours shelf.

## Syncing it

Since the vault is just a folder, you can sync it any way you like: Obsidian Sync, Syncthing, iCloud, or git. Olam only needs to see the folder on the server, and whatever you change in Obsidian shows in Olam the next time you open the screen.

## Next step

With the vault set up, go to [Map and People](map-and-people.md) to start filling your world.

<sub>Next: [Map and People](map-and-people.md) →</sub>
