"""Find the legal clauses a question is about: BM25 over data/tax/articles.jsonl.

Why BM25 and not embeddings: standard library only, no extra API call per
question, and every hit can be explained by the words it matched, which the
page shows next to the answer.

Vietnamese is written in syllables ("người phụ thuộc" is three tokens), so
documents and questions are indexed as syllables plus syllable bigrams; the
bigram "phụ thuộc" then outweighs the common syllable "phụ" on its own.

Two fixes for BM25's blind spot (it matches spelling, not meaning):
- synonyms.json rewrites everyday words into the law's terms before search
  ("bán online" -> "thương mại điện tử");
- core.json lists clauses that go into every prompt (thresholds, methods),
  because almost every question about a household's tax needs them.

A question whose best score is below MIN_SCORE gets no clauses: the app then
answers that it found no legal basis instead of letting a model guess.
"""

import json
import math
import re
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

TAX = Path(__file__).resolve().parent / "data" / "tax"
K1, B = 1.5, 0.75
TOP_K = 8
MIN_SCORE = 10.0  # below this the best hit is noise
# A real tax question shares at least two legal phrases (syllable bigrams such as "nộp thuế",
# "môn bài") with some clause; off-topic questions ("con mèo nhà tôi…") share at most one, even
# when common syllables give them a score as high as a real question's. Measured on
# retrieval_eval.jsonl (min 2) against ten off-topic questions (max 1).
MIN_PHRASES = 2

WORD = re.compile(r"[0-9a-zà-ỹđ]+", re.I)


def fold(text: str) -> str:
    """Lowercase NFC; keeps diacritics, which carry meaning in Vietnamese (thuế ≠ thuê)."""
    return unicodedata.normalize("NFC", text).lower()


def strip_marks(text: str) -> str:
    """'thuế' -> 'thue', 'đ' -> 'd': how many people type on a phone without Vietnamese input."""
    s = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def unaccented(text: str) -> bool:
    return not re.search(r"[à-ỹđ]", fold(text))


def tokens(text: str) -> list[str]:
    syl = WORD.findall(fold(text))
    return syl + [f"{a}_{b}" for a, b in zip(syl, syl[1:])]


def in_force(r: dict, on: date) -> bool:
    start, end = r.get("hieu_luc_tu"), r.get("hieu_luc_den")
    return (not start or date.fromisoformat(start) <= on) and (not end or on < date.fromisoformat(end))


class Index:
    def __init__(self, records: list[dict], synonyms: dict[str, str], core: list[str]):
        self.records = records
        self.synonyms = sorted(synonyms.items(), key=lambda kv: -len(kv[0]))  # longest phrase first
        self.core = core
        texts = [r["tieu_de"] + "\n" + r["text"] for r in records]
        # Two views of the same clauses: as written, and without diacritics for questions typed without them.
        # Diacritics carry meaning (thuế "tax" vs thuê "rent"), so the plain view is used only when needed.
        self.views = {False: self._view(texts), True: self._view([strip_marks(t) for t in texts])}

    @staticmethod
    def _view(texts: list[str]) -> dict:
        docs = [Counter(tokens(t)) for t in texts]
        lens = [sum(d.values()) for d in docs]
        df = Counter(t for d in docs for t in d)
        n = len(texts)
        return {"docs": docs, "lens": lens, "avg": sum(lens) / max(n, 1),
                "idf": {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}}

    @classmethod
    def load(cls, on: date | None = None) -> "Index":
        on = on or date.today()
        records = [json.loads(l) for l in (TAX / "articles.jsonl").read_text(encoding="utf-8").splitlines() if l]
        records = [r for r in records if in_force(r, on)]
        synonyms = json.loads((TAX / "synonyms.json").read_text(encoding="utf-8")) if (TAX / "synonyms.json").exists() else {}
        core = json.loads((TAX / "core.json").read_text(encoding="utf-8")) if (TAX / "core.json").exists() else []
        return cls(records, synonyms, core)

    def expand(self, question: str, plain: bool) -> str:
        """Append the law's term for every everyday phrase found in the question."""
        q = fold(question)
        extra = [term for phrase, term in self.synonyms if (strip_marks(phrase) if plain else phrase) in q]
        text = question + ("\n" + "\n".join(extra) if extra else "")
        return strip_marks(text) if plain else text

    @staticmethod
    def score(v: dict, q: Counter, i: int) -> tuple[float, list[str]]:
        d, s, hits = v["docs"][i], 0.0, []
        norm = K1 * (1 - B + B * v["lens"][i] / v["avg"])
        for t in q:
            f = d.get(t)
            if f:
                s += v["idf"][t] * f * (K1 + 1) / (f + norm)
                hits.append(t)
        return s, hits

    def search(self, question: str, k: int = TOP_K) -> dict:
        """Top-k clauses plus the core clauses, each with its score and matched words."""
        plain = unaccented(question)
        v = self.views[plain]
        q = Counter(tokens(self.expand(question, plain)))
        scored = sorted(((*self.score(v, q, i), i) for i in range(len(self.records))), reverse=True)
        best = scored[0][0] if scored else 0.0
        phrases = max((sum("_" in t for t in m) for _, m, _ in scored[:k]), default=0)
        enough = best >= MIN_SCORE and phrases >= MIN_PHRASES
        hits = [] if not enough else [
            {"id": self.records[i]["id"], "score": round(s, 2),
             "matched": sorted({h.replace("_", " ") for h in m if "_" in h})[:6]}
            for s, m, i in scored[:k] if s > 0
        ]
        seen = {h["id"] for h in hits}
        core = [{"id": cid, "score": None, "matched": [], "core": True}
                for cid in self.core if cid not in seen and any(r["id"] == cid for r in self.records)]
        return {"best": round(best, 2), "enough": enough, "hits": hits + core}

    def get(self, rid: str) -> dict:
        return next(r for r in self.records if r["id"] == rid)


if __name__ == "__main__":
    import sys
    idx = Index.load()
    res = idx.search(" ".join(sys.argv[1:]) or "bán hàng online doanh thu bao nhiêu thì phải nộp thuế")
    print(f"best={res['best']} enough={res['enough']}")
    for h in res["hits"]:
        r = idx.get(h["id"])
        print(f"{h['score']!s:>6}  {h['id']:<22} {r['tieu_de'][:50]:<50} {', '.join(h['matched'])}")
