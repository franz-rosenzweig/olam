"""olam fetch | olam ingest | olam passwd | olam serve

    python -m olam.cli fetch [rules|zims]            download the open sources (rules by default; zims is ~1.5 GB)
    python -m olam.cli ingest [open5e|srd|calibre]   rebuild the library (all three by default)
    python -m olam.cli passwd                         set the password (asks twice)
    python -m olam.cli vault-setup                    the vault's World folders, plugin templates and map (never overwrites)
    python -m olam.cli serve                          run the web app (OLAM_HOSTS, OLAM_PORT)
"""
import getpass
import sys
import time

from . import auth, config, db


def ingest(parts):
    from .ingest import calibre, open5e, srd_pdf
    c = db.connect()
    t = time.time()
    if "open5e" in parts:
        print("Open5e:", open5e.run(c), "entries")
    if "srd" in parts:
        print("SRD 5.2 glossary:", srd_pdf.run(c), "terms")
    if "calibre" in parts and not config.DEMO and config.CALIBRE:
        print("Calibre: %d books, %d sections" % calibre.run(c))
    db.reindex(c)
    print("Done in %.0fs: %d entries" % (time.time() - t, c.execute("SELECT count(*) FROM entries").fetchone()[0]))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "help"
    if cmd == "fetch":
        from . import fetch
        fetch.main(argv[2:])
    elif cmd == "ingest":
        ingest(argv[2:] or ["open5e", "srd", "calibre"])
    elif cmd == "passwd":
        p = getpass.getpass("New password: ")
        if p != getpass.getpass("Again: ") or len(p) < 8:
            sys.exit("Passwords didn't match, or shorter than 8 characters")
        auth.set_password(p)
        print("Password set. Every browser is signed out.")
    elif cmd == "vault-setup":
        from . import vault
        made = vault.setup()
        print("\n".join(made) or "Nothing new: the vault already has everything.")
    elif cmd == "serve":
        from .server import main as serve
        serve()
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
