"""The Rules Glossary of SRD 5.2.1 (pages 176–191 of the PDF) into one entry per term.

Open5e's data has the "Playing the Game" chapter but not the glossary, which is where 2024 keeps
most rules terms (Advantage, Prone, Grappled, the actions). The PDF's fonts tell its parts apart:
GillSans-SemiBold 12 pt starts a term, 10.5 pt is a heading inside one, Cambria is the text,
Cambria-BoldItalic is a run-in heading, and plain GillSans is a list item.
"""
import re

from pypdf import PdfReader

from .. import config, db

FIRST, LAST = 176, 191  # printed page numbers, which match the PDF's own


def fragments(reader):
    out = []
    for i in range(FIRST - 1, LAST):
        def visit(text, cm, tm, fd, fs):
            if not text or not text.strip():
                if text and "\n" in text:
                    out.append(("nl", "\n"))
                return
            font = ((fd.get("/BaseFont") if fd else "") or "").split("+")[-1]
            size = round(tm[0] * fs, 1)
            t = text
            if "SemiBold" in font:
                if t.strip().isdigit() or "System Reference" in t:
                    return
                kind = "term" if size >= 11.5 else ("sub" if size >= 10 else "th")
            elif font.startswith("Cambria-BoldItalic"):
                kind = "runin"
            elif font.startswith("Cambria-Italic"):
                kind = "italic"
            elif font.startswith("Cambria"):
                kind = "text"
            elif font.startswith("GillSans"):
                if "System Reference" in t:
                    return
                kind = "item"
            else:
                return
            out.append((kind, t))
        reader.pages[i].extract_text(visitor_text=visit)
    return out


def clean(s):
    s = s.replace("­", "")
    s = re.sub(r"(\w) ?-\s*\n\s*(\w)", r"\1\2", s)      # words broken across lines: "Dex -\nterity"
    s = re.sub(r"[ \t]*\n[ \t]*", " ", s)
    return re.sub(r"\s{2,}", " ", s).strip()


def build(frags):
    terms, cur, started = [], None, False
    para = []

    def flush_para():
        if cur is not None and para:
            txt = clean("".join(para))
            if txt:
                cur["parts"].append(txt)
        para.clear()

    for kind, t in frags:
        if kind == "term":
            if not started:
                if t.strip() == "Rules Definitions":
                    started = True
                continue
            flush_para()
            name = clean(t)
            if cur is not None and cur["parts"] == [] and not name.startswith(("[",)):
                # a term split over two text runs ("Attack" + "[Action]")
                pass
            cur = {"name": name, "parts": []}
            terms.append(cur)
            continue
        if not started or cur is None:
            continue
        if kind == "sub":
            flush_para(); cur["parts"].append("### " + clean(t))
        elif kind == "th":
            flush_para(); cur["parts"].append("**" + clean(t) + "**")
        elif kind == "item":
            flush_para(); cur["parts"].append("- " + clean(t))
        elif kind == "runin":
            flush_para()                                   # a run-in heading always opens a paragraph
            para.append("**" + t.strip() + "** ")
        elif kind == "italic":
            para.append("*" + t.strip() + "* ")
        elif kind == "nl":
            para.append("\n")
        else:
            opens = re.match(r"^ \S", t) and t.strip() != "-"   # one leading space: an indented new paragraph
            just_runin = len(para) == 1 and para[0].startswith("**")
            if opens and not just_runin and para and "".join(para).strip():
                flush_para()
            para.append(t)
    flush_para()
    merged = []
    for t in terms:
        if merged and re.fullmatch(r"\[[^\]]+\]", t["name"]):
            merged[-1]["name"] += " " + t["name"]; merged[-1]["parts"] += t["parts"]
        else:
            merged.append(t)
    return merged


def run(c):
    reader = PdfReader(str(config.SRD_PDF))
    terms = build(fragments(reader))
    doc = "srd-2024"
    c.execute("DELETE FROM entries WHERE id LIKE 'srd-2024/glossary/%'")
    for t in terms:
        m = re.match(r"^(.*?)\s*\[([^\]]+)\]$", t["name"])
        name, tag = (m.group(1), m.group(2)) if m else (t["name"], "")
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        body = "\n\n".join(t["parts"])
        body = re.sub(r"(\w)\* \*(\w)", r"\1 \2", body)       # "*See* *also*" split over two runs
        body = re.sub(r"\*See also\*\s*", "*See also* ", body)
        db.put(c, id=f"{doc}/glossary/{slug}", kind="glossary", name=name, doc=doc, shelf="rule", edition="2024",
               grp="Rules Glossary", summary=f"Rules Glossary · {tag}" if tag else "Rules Glossary", body=body,
               data={"tag": tag, "pages": f"{FIRST}–{LAST}"})
    c.commit()
    return len(terms)
