"""Turn the official legal texts in data/tax/sources/ into data/tax/articles.jsonl.

One JSONL record per khoản (clause), or per Điều when an article has no
numbered clauses. Each record carries the document's validity dates from
data/tax/sources.json, so retrieval can drop text that is no longer in force.

Amendments (data/tax/amendments.json) are applied here, so the record's `text`
is the text in force at the cut-off date. The original wording is kept in
`text_goc` and the amending document in `sua_doi_boi`, so a reader can always
see what changed and why.

    python app/preprocess.py            # rebuild articles.jsonl
    python app/preprocess.py --check    # also print article counts per document

Only this script touches the source files; the app reads articles.jsonl.
PDFs are read with `pdftotext` (poppler), the one external tool, used only here.
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

TAX = Path(__file__).resolve().parent / "data" / "tax"
SOURCES = TAX / "sources"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

CHAPTER = re.compile(r"^Chương\s+([IVXLC]+)\b")
ARTICLE = re.compile(r"^Điều\s+(\d+)\s*[.:]\s*(.*)$")
CLAUSE = re.compile(r"^(\d+)\.\s+(.*)$")
# Công báo page furniture: running headers ("PAGE 26  CÔNG BÁO/Số 713 + 714/Ngày …") and bare page numbers.
FURNITURE = re.compile(r"^(.*CÔNG BÁO/Số .*|PAGE \d+.*|\d{1,3})$")
FOOTNOTE_MARK = re.compile(r"\[\^\d+\]")
FOOTNOTES_START = "----- FOOTNOTES -----"  # consolidated texts (VBHN) list amendment notes after this line


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def docx_lines(path: Path) -> list[str]:
    z = zipfile.ZipFile(path)
    # Some government DOCX files store entries with backslash separators.
    name = next(n for n in z.namelist() if n.replace("\\", "/") == "word/document.xml")
    root = ET.fromstring(z.read(name))
    lines = []
    for p in root.iter(W + "p"):
        text = "".join(t.text or "" for t in p.iter(W + "t"))
        lines.append(text)
    return lines


def pdf_lines(path: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-raw", str(path), "-"], capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def text_lines(path: Path) -> list[str]:
    if path.suffix == ".docx":
        lines = docx_lines(path)
    elif path.suffix == ".pdf":
        lines = pdf_lines(path)
    else:  # .txt: a checked transcription, e.g. of a scanned PDF
        lines = path.read_text(encoding="utf-8").splitlines()
    clean = []
    for line in lines:
        if line.strip() == FOOTNOTES_START:
            break
        line = re.sub(r"[ \t\xa0]+", " ", FOOTNOTE_MARK.sub("", nfc(line))).strip()
        if line and not FURNITURE.match(line):
            clean.append(line)
    return clean


def split(doc: dict, lines: list[str]) -> list[dict]:
    """Group lines into one record per clause (or per article without clauses).

    Lines before the first article (preamble) and the signature block after the
    last one are dropped: they carry no rule a user could ask about.
    """
    records, chapter, art, cur = [], None, None, None

    def flush():
        if cur and cur["lines"]:
            records.append(cur)

    for line in lines:
        if m := CHAPTER.match(line):
            chapter = m[1]
            continue
        if m := ARTICLE.match(line):
            flush()
            art = {"dieu": int(m[1]), "tieu_de": m[2].strip(), "chuong": chapter}
            cur = {**art, "khoan": None, "lines": []}
            continue
        if art is None:
            continue
        if (m := CLAUSE.match(line)) and not line.startswith(("TM.", "KT.")):
            flush()
            cur = {**art, "khoan": int(m[1]), "lines": [line]}
            continue
        if line.isupper() and len(line) < 60 and cur["lines"]:
            # A chapter title line (e.g. "QUY ĐỊNH CHUNG") right after "Chương I" is caught above;
            # an all-caps line here is a signature block ("TM. CHÍNH PHỦ", "THỦ TƯỚNG"): stop.
            flush()
            cur, art = None, None
            continue
        cur["lines"].append(line)
    flush()

    out = []
    for r in records:
        rid = f"{doc['id']}:d{r['dieu']}" + (f":k{r['khoan']}" if r["khoan"] is not None else "")
        out.append({
            "id": rid, "doc": doc["id"], "so_hieu": doc["so_hieu"], "aliases": doc.get("aliases", [doc["so_hieu"]]),
            "trich_dan": doc.get("trich_dan", doc["so_hieu"]), "chuong": r["chuong"],
            "dieu": r["dieu"], "khoan": r["khoan"], "tieu_de": r["tieu_de"],
            "text": "\n".join(r["lines"]),
            "hieu_luc_tu": doc["hieu_luc_tu"], "hieu_luc_den": doc.get("hieu_luc_den"),
        })
    return out


def amend(records: list[dict], amendments: list[dict]) -> None:
    """Apply amendments in place.

    A target is a record id or an article id (`doc:dN`, meaning all its clauses).
    An amendment either replaces the whole text of one record (`text`) or
    replaces phrases (`replace`: [[old, new], ...]) in text and article title.
    A phrase that occurs in none of a target's records stops the build: the
    amendment and the source text disagree, and a person must look.
    """
    for a in amendments:
        for target in a["targets"]:
            hit = [r for r in records if r["id"] == target or r["id"].startswith(target + ":")]
            if not hit:
                sys.exit(f"amendment from {a['by']}: no record {target}")
            if "text" in a:
                if len(hit) != 1:
                    sys.exit(f"amendment from {a['by']}: whole-text target {target} must be one clause")
                hit[0].setdefault("text_goc", hit[0]["text"])
                hit[0]["text"] = a["text"]
                hit[0].setdefault("sua_doi_boi", []).append(a["by"])
            for old, new in a.get("replace", []):
                changed = [r for r in hit if old in r["text"] or old in r["tieu_de"]]
                if not changed:
                    sys.exit(f"amendment from {a['by']}: '{old}' not in {target}")
                for r in changed:
                    r.setdefault("text_goc", r["text"])
                    r["text"] = r["text"].replace(old, new)
                    r["tieu_de"] = r["tieu_de"].replace(old, new)
                    if a["by"] not in r.setdefault("sua_doi_boi", []):
                        r["sua_doi_boi"].append(a["by"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="print article and clause counts per document")
    args = ap.parse_args()

    docs = json.loads((TAX / "sources.json").read_text(encoding="utf-8"))
    amendments_file = TAX / "amendments.json"
    amendments = json.loads(amendments_file.read_text(encoding="utf-8")) if amendments_file.exists() else []

    records = []
    for doc in docs:
        if not doc.get("text_file"):
            continue  # listed for provenance only (e.g. a scan we have not transcribed)
        recs = split(doc, text_lines(SOURCES / doc["text_file"]))
        if args.check:
            arts = sorted({r["dieu"] for r in recs})
            print(f"{doc['id']}: {len(arts)} điều, {len(recs)} bản ghi (Điều {arts[0]}–{arts[-1]})")
        records += recs
    dup = [i for i, n in Counter(r["id"] for r in records).items() if n > 1]
    if dup:
        sys.exit(f"duplicate record ids (a document restarts its article numbering?): {dup[:5]}")
    amend(records, amendments)

    with (TAX / "articles.jsonl").open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(records)} bản ghi → {TAX / 'articles.jsonl'}")


if __name__ == "__main__":
    main()
