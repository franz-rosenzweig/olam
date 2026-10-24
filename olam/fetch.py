"""Download the open-licensed sources into the data folder, from where each one is published.

    rules     Open5e's data (a sparse git checkout of data/v2) and the SRD 5.2.1 PDF: about 45 MB
    zims      the Kiwix archives in config.ZIMS, the newest of each: about 1.5 GB

Run `olam ingest` afterwards to build the library from them.
"""
import re
import shutil
import subprocess
import sys
import urllib.request

from . import config

OPEN5E_GIT = "https://github.com/open5e/open5e-api.git"
SRD_URL = "https://media.dndbeyond.com/compendium-images/srd/5.2/SRD_CC_v5.2.1.pdf"
KIWIX = "https://download.kiwix.org/zim/"
# Where each archive lives on Kiwix's download server.
FOLDERS = {"rpg.stackexchange.com": "stack_exchange", "mythology.stackexchange.com": "stack_exchange",
           "worldbuilding.stackexchange.com": "stack_exchange", "dandwiki": "other"}


def download(url, dest):
    tmp = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Olam (self-hosted)"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        total, done, shown = int(r.headers.get("Content-Length") or 0), 0, -1
        while chunk := r.read(1 << 20):
            f.write(chunk)
            done += len(chunk)
            pct = done * 100 // total if total else -1
            if total and pct // 10 != shown:
                shown = pct // 10
                print(f"  {dest.name}: {pct}% of {total >> 20} MB", flush=True)
    tmp.replace(dest)


def open5e():
    repo = config.DATA / "open5e" / "repo"
    if (repo / ".git").exists():
        print("Open5e: updating")
        subprocess.run(["git", "-C", str(repo), "pull", "--ff-only", "--quiet"], check=True)
    else:
        print("Open5e: downloading data/v2")
        repo.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none", "--sparse", OPEN5E_GIT, str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "sparse-checkout", "set", "data/v2"], check=True)


def srd():
    if config.SRD_PDF.exists():
        print("SRD 5.2.1: already here")
        return
    print("SRD 5.2.1: downloading")
    download(SRD_URL, config.SRD_PDF)


def latest_zim(prefix):
    """The newest file for one archive on Kiwix's server, by the date in its name."""
    folder = KIWIX + FOLDERS[prefix] + "/"
    html = urllib.request.urlopen(urllib.request.Request(folder, headers={"User-Agent": "Olam (self-hosted)"}), timeout=60).read().decode()
    names = set(re.findall(rf'href="({re.escape(prefix)}_en_all_(?:nopic_)?\d{{4}}-\d{{2}}\.zim)"', html))
    if not names:
        return None, None
    name = max(names, key=lambda n: (re.search(r"(\d{4}-\d{2})\.zim$", n).group(1), "nopic" in n))
    return name, folder + name


def zims(only=()):
    for prefix in only or FOLDERS:
        if prefix not in FOLDERS:
            print(f"{prefix}: not an archive Olam knows ({', '.join(FOLDERS)})")
            continue
        name, url = latest_zim(prefix)
        if not name:
            print(f"{prefix}: not found on {KIWIX}")
            continue
        dest = config.ZIM_DIR / name
        if dest.exists():
            print(f"{prefix}: {name} is the newest")
            continue
        print(f"{prefix}: downloading {name}")
        download(url, dest)
        for old in config.ZIM_DIR.glob(prefix + "_*.zim"):
            if old != dest:
                old.unlink()
                print(f"  removed the older {old.name}")


def main(args):
    what = args[0] if args else "rules"
    if what == "rules":
        if not shutil.which("git"):
            sys.exit("Open5e's data comes with git: install git first")
        open5e()
        srd()
        print("Done. Now run: olam ingest")
    elif what == "zims":
        zims(args[1:])
        print("Done. Restart Olam (and kiwix-serve, if you run it) to pick them up.")
    else:
        print(__doc__)
