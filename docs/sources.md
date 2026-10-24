<sub>[Olam docs](README.md) › Learning the game</sub>

# Where it all comes from

Everything Olam shows you comes from somewhere you can check, and every piece of it sits on a shelf with a badge, so you always know how far to trust it. This page lists the shelves, every source, and the license each one is shared under. The **Credits & licenses** page in the app, at the bottom of the rail, has the same list, in the words each license asks for.

Nothing in Olam's code is rules text. `olam fetch` downloads each source from wherever it's published, and `olam ingest` builds the library from what it downloaded.

## The shelves

| Badge | What it is | Where it comes from |
|---|---|---|
| **Rule** | Official rules | SRD 5.2.1 (the 2024 rules) and SRD 5.1 (2014), through the PDF and Open5e's data |
| **3rd-party** | Published, but not official | Open5e: Kobold Press, EN Publishing (A5e), Black Flag and others |
| **Expert** | Experienced players answering | RPG Stack Exchange and Mythology Q&A |
| **Craft** | How to build a world | Worldbuilding Q&A |
| **Idea** | Inspiration, not rules | D&D Wiki homebrew, and the books in your library |
| **Yours** | Your own notes | your Obsidian vault |

There are two more badges you'll see now and then. **Summary** marks a summary Claude wrote from the sources on the page, and **Private** marks a passage from your own books, which only you can see.

## The rules

- **SRD 5.2.1** by Wizards of the Coast LLC, from [dndbeyond.com/srd](https://www.dndbeyond.com/srd), licensed CC BY 4.0. These are the 2024 rules, and they're what Olam teaches. The Rules Glossary (where 2024 keeps most of its terms, like Advantage, Prone, Grappled and the actions) is read straight from the PDF, and the rest comes through Open5e's data.
- **SRD 5.1**, the 2014 rules, under CC BY 4.0 and the Open Game License, through Open5e's data. They show up as the 2014 version of an entry, and in the Codex when you choose **2014** or **Every edition**.

## Third-party books

[Open5e's data](https://github.com/open5e/open5e-api) also has books from other publishers, under the Open Game License or Creative Commons: Kobold Press (the Tome of Beasts books, Creature Codex, Deep Magic and the Black Flag SRD), EN Publishing (Level Up, or A5e), Green Ronin (the Tal'dorei Campaign Setting), and a few more. The demo only has the Creative Commons ones. Olam brings in only their monsters, spells and magic items, and puts them on the 3rd-party shelf. They show up as other versions of an entry, and in the Codex when you turn on **3rd-party books**. They're never mixed in with the rules, because they're not the rules.

## The archives

These are offline copies of whole websites, from [Kiwix](https://download.kiwix.org/zim/). Olam searches them in place and shows the best pages on each wiki page.

- **RPG Stack Exchange** (CC BY-SA). Years of questions and answers about running and playing tabletop games, voted on by people who know the rules well. This is the Expert shelf, and it's where the edge cases get answered.
- **Mythology Q&A** (CC BY-SA). Questions about myths and legends, which is where the "Myth roots" on a monster's page come from.
- **Worldbuilding Q&A** (CC BY-SA). Questions about building believable worlds, on the Craft shelf.
- **D&D Wiki** (GFDL). Fan-made homebrew. It's on the Idea shelf and marked **not official** everywhere it shows, because anyone can write on it and none of it has been playtested.

Every archive page in Olam names its authors and links back to the original.

## Your own books

If you have a [Calibre](https://calibre-ebook.com/) library, Olam can search your books too. Point `OLAM_CALIBRE` at the folder with Calibre's `metadata.db` and run `olam ingest calibre`. Olam reads the library without ever changing it, splits each EPUB into sections about a page long, and indexes them, so your books show up in the Codex under **Your library** and in the **In your books** section of a wiki page.

Your books NEVER leave your server. Their passages are marked Private, they're not in the demo, they're not on the Credits page, and Olam only shows a short passage with a link to the book.

Every book starts on the Idea shelf, since most of a library is fiction, myth and history. If a book should be somewhere else, like a rulebook you own, or one whose title or author Calibre has wrong, put it in `books.json` in the data folder, by its Calibre book ID:

```json
{
  "123": {"shelf": "rule", "edition": "2024", "note": "my own copy"},
  "456": {"title": "The right title", "author": "The right author"}
}
```

Every key is optional. Books on the Rule shelf are also the ones Ask uses as "your rulebooks". Run `olam ingest calibre` again after you change it.

## Your notes

The Yours shelf is your vault. When a monster, a place or a rule comes up in your notes, it shows in the **In your world** section of its wiki page. See [Your vault](the-vault.md).

## The fonts

The type is IM FELL English by Igino Marini and Alegreya Sans by Juan Pablo del Peral (Huerta Tipográfica), both under the SIL Open Font License. It's in `web/fonts/OFL.txt`.

## Next step

Now that you know where things come from, the next part is building your own world: [Your vault](the-vault.md).

<sub>Next: [Your vault](the-vault.md) →</sub>
