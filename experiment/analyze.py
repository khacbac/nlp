"""Compute the evaluation criteria from the judge's verdicts and the human scores.

Inputs (all in data/, git-ignored):
    judgments_<lang>.jsonl   from judge.py, one line per (pair, order)
    key.csv                  answer_id -> qid, model, annotators
    grading_sheet_A..D.csv   annotator scores
    questions.jsonl, answers_*.jsonl   gold answers and answer texts (baselines, lengths)

Outputs (results/):
    metrics_<lang>.json      every number, with 95% bootstrap intervals
    summary_<lang>.md        the same numbers as readable tables
    figures/*.svg, *.png     the charts used in the report and the slides

Definitions (proposal, "Evaluation criteria"). For one pair (X, Y), run 1
shows X first (order "xy") and run 2 shows Y first (order "yx"). p_x is the
judge's probability for X, renormalised over the A/B labels.

    winner of a run    X if p_x > 0.5, else Y
    flip               the two runs pick different winners, i.e. the same
                       slot (A or B) wins both times
    FPP                P(win | first) - P(win | second) = share of pairs where
                       slot A wins twice minus share where slot B wins twice
    margin             |p_x - p_y| averaged over both runs
    BPC                X wins if the mean of p_x over both runs > 0.5
    human winner       the answer with the higher mean annotator score

Intervals bootstrap over questions, not pairs: the three pairs of one
question share the passage and the annotators, so they are not independent.

Usage:
    python analyze.py
"""

import argparse
import csv
import itertools
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
DATA = HERE / "data"
MODELS = ["qwen", "gpt-oss", "gemini"]
PAIRS = list(itertools.combinations(MODELS, 2))
ANNOTATORS = "ABCD"
GAP_BINS = [(0, 0, "0"), (0.5, 1, "0.5–1"), (1.5, 2, "1.5–2"), (2.5, 4, "≥ 2.5")]
B = 2000
SEED = 7


# ---------------------------------------------------------------- loading

def read_jsonl(path: Path) -> list[dict]:
    rows = []
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_scores(scores_dir: Path, key_path: Path):
    """Return {(qid, model): [score, score]}, {(qid, model, annotator): score}, flagged qids."""
    key = {r["answer_id"]: r for r in read_csv(key_path)}
    per_answer: dict[tuple[str, str], list[int]] = defaultdict(list)
    by_annotator: dict[tuple[str, str, str], int] = {}
    gold_wrong: set[str] = set()
    for a in ANNOTATORS:
        path = scores_dir / f"grading_sheet_{a}.csv"
        if not path.exists():
            continue
        for r in read_csv(path):
            k = key.get(r["answer_id"])
            if not k:
                continue
            if "gold_sai" in r.get("note", "").lower():
                gold_wrong.add(k["qid"])
            s = r.get("score", "").strip()
            if s in {"1", "2", "3", "4", "5"}:
                per_answer[(k["qid"], k["model"])].append(int(s))
                by_annotator[(k["qid"], k["model"], a)] = int(s)
    return per_answer, by_annotator, gold_wrong


def pair_table(judgments: list[dict], human: dict, answers: dict, gold: dict, gold_wrong: set) -> list[dict]:
    """One row per (qid, X, Y) with both runs, human scores and baselines."""
    runs = {(j["qid"], j["x"], j["y"], j["order"]): j for j in judgments}
    rows = []
    for (qid, x, y, order), r1 in runs.items():
        if order != "xy":
            continue
        r2 = runs.get((qid, x, y, "yx"))
        if r2 is None:
            continue
        row = {"qid": qid, "x": x, "y": y, "pair": f"{x} – {y}",
               "valid": r1.get("p_x") is not None and r2.get("p_x") is not None,
               "verdict_1": r1.get("winner"), "verdict_2": r2.get("winner"),
               "p1x": r1.get("p_x"), "p2x": r2.get("p_x"),
               "judgment_1": r1.get("judgment", ""), "judgment_2": r2.get("judgment", "")}
        hx, hy = human.get((qid, x)), human.get((qid, y))
        row["hx"] = float(np.mean(hx)) if hx and len(hx) == 2 else None
        row["hy"] = float(np.mean(hy)) if hy and len(hy) == 2 else None
        row["gold_wrong"] = qid in gold_wrong
        ax, ay = answers.get((qid, x), ""), answers.get((qid, y), "")
        row["len_x"], row["len_y"] = len(ax.split()), len(ay.split())
        row["f1_x"], row["f1_y"] = token_f1(ax, gold.get(qid, "")), token_f1(ay, gold.get(qid, ""))
        rows.append(row)
    return rows


# ---------------------------------------------------------------- baselines

def normalize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    return re.findall(r"\w+", text)


def token_f1(pred: str, gold: str) -> float:
    """SQuAD-style word-overlap F1."""
    p, g = normalize(pred), normalize(gold)
    common = sum((Counter(p) & Counter(g)).values())
    if not p or not g or not common:
        return 0.0
    prec, rec = common / len(p), common / len(g)
    return 2 * prec * rec / (prec + rec)


def embedding_cosines(rows: list[dict], answers: dict, gold: dict) -> bool:
    """Add cos_x / cos_y (answer vs gold) if sentence-transformers is installed."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return False
    model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    keys = sorted({(r["qid"], m) for r in rows for m in (r["x"], r["y"])})
    texts = [answers.get(k, "") for k in keys] + [gold.get(k[0], "") for k in keys]
    emb = model.encode(texts, normalize_embeddings=True, batch_size=64)
    n = len(keys)
    cos = {k: float(emb[i] @ emb[n + i]) for i, k in enumerate(keys)}
    for r in rows:
        r["cos_x"], r["cos_y"] = cos[(r["qid"], r["x"])], cos[(r["qid"], r["y"])]
    return True


# ---------------------------------------------------------------- agreement

def cohen_kappa(a: list[int], b: list[int], weighted: bool = False) -> float:
    cats = [1, 2, 3, 4, 5]
    n = len(a)
    obs = np.zeros((5, 5))
    for i, j in zip(a, b):
        obs[i - 1, j - 1] += 1
    obs /= n
    exp = np.outer(obs.sum(1), obs.sum(0))
    w = np.array([[((i - j) / 4) ** 2 if weighted else float(i != j) for j in cats] for i in cats])
    denom = (w * exp).sum()
    return float(1 - (w * obs).sum() / denom) if denom else float("nan")


def krippendorff_alpha(units: list[list[int]], level: str = "ordinal") -> float:
    """Krippendorff's alpha for units with >= 2 ratings each (values 1-5)."""
    cats = [1, 2, 3, 4, 5]
    o = np.zeros((5, 5))
    for vals in units:
        m = len(vals)
        if m < 2:
            continue
        for i, j in itertools.permutations(range(m), 2):
            o[vals[i] - 1, vals[j] - 1] += 1 / (m - 1)
    n_c = o.sum(1)
    n = n_c.sum()

    def delta(c: int, k: int) -> float:
        if level == "interval":
            return float((cats[c] - cats[k]) ** 2)
        lo, hi = min(c, k), max(c, k)
        return float((n_c[lo:hi + 1].sum() - (n_c[lo] + n_c[hi]) / 2) ** 2)

    d = np.array([[delta(c, k) for k in range(5)] for c in range(5)])
    d_o = (o * d).sum() / n
    d_e = (np.outer(n_c, n_c) * d).sum() / (n * (n - 1))
    return float(1 - d_o / d_e) if d_e else float("nan")


# ---------------------------------------------------------------- bootstrap

class Boot:
    """Weighted means under a question-level bootstrap.

    Each replicate draws questions with replacement; a pair's weight is the
    number of times its question was drawn, so every pair-level mean is
    sum(w * v) / sum(w) over the pairs that pass a mask.
    """

    def __init__(self, qids: list[str], seed: int = SEED):
        uniq = sorted(set(qids))
        idx = {q: i for i, q in enumerate(uniq)}
        rng = np.random.default_rng(seed)
        counts = rng.multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)), size=B)
        self.w = counts[:, [idx[q] for q in qids]].astype(float)

    def mean(self, values, mask=None) -> dict:
        v = np.asarray(values, dtype=float)
        m = np.ones_like(v, bool) if mask is None else np.asarray(mask, bool)
        if not m.any():
            return {"value": None, "lo": None, "hi": None, "n": 0}
        point = float(v[m].mean())
        w = self.w[:, m]
        tot = w.sum(1)
        reps = (w * v[m]).sum(1)[tot > 0] / tot[tot > 0]
        lo, hi = np.percentile(reps, [2.5, 97.5])
        return {"value": point, "lo": float(lo), "hi": float(hi), "n": int(m.sum())}

    def diff(self, values, mask_a, mask_b) -> dict:
        """Mean over mask_a minus mean over mask_b, with an interval."""
        v = np.asarray(values, dtype=float)
        a, b = np.asarray(mask_a, bool), np.asarray(mask_b, bool)
        if not a.any() or not b.any():
            return {"value": None, "lo": None, "hi": None}
        wa, wb = self.w[:, a], self.w[:, b]
        ok = (wa.sum(1) > 0) & (wb.sum(1) > 0)
        reps = (wa * v[a]).sum(1)[ok] / wa.sum(1)[ok] - (wb * v[b]).sum(1)[ok] / wb.sum(1)[ok]
        lo, hi = np.percentile(reps, [2.5, 97.5])
        return {"value": float(v[a].mean() - v[b].mean()), "lo": float(lo), "hi": float(hi)}


def auc(scores, labels) -> float | None:
    """Probability that a random positive outranks a random negative (ties count half)."""
    s, y = np.asarray(scores, float), np.asarray(labels, bool)
    pos, neg = s[y], s[~y]
    if not len(pos) or not len(neg):
        return None
    gt = (pos[:, None] > neg[None, :]).mean()
    eq = (pos[:, None] == neg[None, :]).mean()
    return float(gt + eq / 2)


# ---------------------------------------------------------------- metrics

def compute(rows: list[dict], by_annotator: dict, has_cos: bool) -> dict:
    out: dict = {}
    out["pairs_total"] = len(rows)
    out["format_error_rate"] = sum(not r["valid"] for r in rows) / len(rows) if rows else None
    rows = [r for r in rows if r["valid"]]
    out["pairs_valid"] = len(rows)

    p1x = np.array([r["p1x"] for r in rows])
    p2x = np.array([r["p2x"] for r in rows])
    x1, x2 = p1x > 0.5, p2x > 0.5          # X wins run 1 / run 2
    flip = x1 != x2
    a_both = x1 & ~x2                      # slot A won both runs
    b_both = ~x1 & x2
    margin = (np.abs(2 * p1x - 1) + np.abs(2 * p2x - 1)) / 2
    bpc_x = (p1x + p2x) / 2 > 0.5
    pair = np.array([r["pair"] for r in rows])
    bs = Boot([r["qid"] for r in rows])

    # Verdict labels (with ties), as Zheng et al. (2023) Table 2 report them.
    v1 = [r["verdict_1"] for r in rows]
    v2 = [r["verdict_2"] for r in rows]
    out["labels"] = {
        "consistent": float(np.mean([a == b for a, b in zip(v1, v2)])),
        "biased_first": float(np.mean([a == "x" and b == "y" for a, b in zip(v1, v2)])),
        "biased_second": float(np.mean([a == "y" and b == "x" for a, b in zip(v1, v2)])),
        "involves_tie": float(np.mean([a != b and "tie" in (a, b) for a, b in zip(v1, v2)])),
        "tie_rate": float(np.mean([v == "tie" for v in v1 + v2])),
        # MT-Bench asks for the explanation first; a verdict at the start means it was not.
        "verdict_first": float(np.mean([r[k].lstrip().startswith("[[") for r in rows
                                        for k in ("judgment_1", "judgment_2")])),
    }

    # RQ1
    out["flip_rate"] = bs.mean(flip)
    no_tie = np.array([a != "tie" and b != "tie" for a, b in zip(v1, v2)])
    out["flip_rate_no_tie"] = bs.mean(flip, no_tie)
    fpp = a_both.astype(float) - b_both.astype(float)
    out["fpp"] = bs.mean(fpp)
    out["first_slot_wins_both"] = bs.mean(a_both)
    out["second_slot_wins_both"] = bs.mean(b_both)
    out["by_pair"] = {}
    for x, y in PAIRS:
        m = pair == f"{x} – {y}"
        out["by_pair"][f"{x} – {y}"] = {"flip_rate": bs.mean(flip, m), "fpp": bs.mean(fpp, m),
                                        "bpc_x_wins": bs.mean(bpc_x, m)}

    # RQ3
    out["margin"] = {
        "flipped": bs.mean(margin, flip),
        "consistent": bs.mean(margin, ~flip),
        "difference": bs.diff(margin, ~flip, flip),
        "auc_consistent": auc(margin, ~flip),
    }
    edges = np.quantile(margin, [0, .25, .5, .75, 1])
    out["flip_by_margin_quartile"] = []
    for i in range(4):
        m = (margin >= edges[i]) & ((margin <= edges[i + 1]) if i == 3 else (margin < edges[i + 1]))
        out["flip_by_margin_quartile"].append({"range": [float(edges[i]), float(edges[i + 1])],
                                               **bs.mean(flip, m)})

    # Length (verbosity) context
    dlen = np.array([abs(r["len_x"] - r["len_y"]) for r in rows])
    longer_x = np.array([r["len_x"] > r["len_y"] for r in rows])
    diff_len = np.array([r["len_x"] != r["len_y"] for r in rows])
    out["length"] = {
        "bpc_prefers_longer": bs.mean(bpc_x == longer_x, diff_len),
        "flip_rate_len_gap_above_median": bs.mean(flip, dlen > np.median(dlen)),
        "flip_rate_len_gap_at_or_below_median": bs.mean(flip, dlen <= np.median(dlen)),
    }

    # Human-based criteria (RQ2, RQ4)
    has_h = np.array([r["hx"] is not None and r["hy"] is not None and not r["gold_wrong"] for r in rows])
    out["pairs_with_human"] = int(has_h.sum())
    if has_h.any():
        gap = np.array([(r["hx"] - r["hy"]) if h else 0.0 for r, h in zip(rows, has_h)])
        agap = np.abs(gap)
        out["flip_by_human_gap"] = []
        for lo, hi, label in GAP_BINS:
            m = has_h & (agap >= lo) & (agap <= hi)
            out["flip_by_human_gap"].append({"gap": label, **bs.mean(flip, m)})

        decided = has_h & (gap != 0)
        human_x = gap > 0
        out["agreement"] = {
            "single_order_xy": bs.mean(x1 == human_x, decided),
            "single_order_yx": bs.mean(x2 == human_x, decided),
            "single_order_mean": bs.mean(((x1 == human_x).astype(float) + (x2 == human_x)) / 2, decided),
            "consistent_only": bs.mean(x1 == human_x, decided & ~flip),
            "consistent_coverage": bs.mean(~flip, decided),
            "bpc": bs.mean(bpc_x == human_x, decided),
            "f1_baseline": bs.mean(np.array([r["f1_x"] > r["f1_y"] for r in rows]) == human_x,
                                   decided & np.array([r["f1_x"] != r["f1_y"] for r in rows])),
        }
        if has_cos:
            cx = np.array([r["cos_x"] > r["cos_y"] for r in rows])
            out["agreement"]["cosine_baseline"] = bs.mean(cx == human_x, decided)
        out["agreement_by_pair"] = {}
        for x, y in PAIRS:
            m = decided & (pair == f"{x} – {y}")
            out["agreement_by_pair"][f"{x} – {y}"] = {"single_order_mean": bs.mean(
                ((x1 == human_x).astype(float) + (x2 == human_x)) / 2, m), "bpc": bs.mean(bpc_x == human_x, m)}

    # Model ranking: human mean score and BPC win rate over the model's pairs
    rank = {}
    for mname in MODELS:
        wins, games = 0, 0
        for r, b in zip(rows, bpc_x):
            if mname == r["x"]:
                wins, games = wins + b, games + 1
            elif mname == r["y"]:
                wins, games = wins + (not b), games + 1
        hs = [r["hx"] for r in rows if r["x"] == mname and r["hx"] is not None] + \
             [r["hy"] for r in rows if r["y"] == mname and r["hy"] is not None]
        rank[mname] = {"bpc_win_rate": wins / games if games else None,
                       "human_mean": float(np.mean(hs)) if hs else None}
    out["ranking"] = rank

    # Annotator agreement
    pairs_ab = defaultdict(lambda: ([], []))
    units = defaultdict(list)
    for (qid, model, a), s in by_annotator.items():
        units[(qid, model)].append((a, s))
    for (qid, model), vals in units.items():
        if len(vals) == 2:
            (a1, s1), (a2, s2) = sorted(vals)
            pairs_ab[a1 + a2][0].append(s1)
            pairs_ab[a1 + a2][1].append(s2)
    out["annotators"] = {
        "kappa": {k: {"n": len(v[0]), "kappa": cohen_kappa(*v), "kappa_quadratic": cohen_kappa(*v, weighted=True)}
                  for k, v in sorted(pairs_ab.items())},
        "alpha_ordinal": krippendorff_alpha([[s for _, s in v] for v in units.values()], "ordinal")
        if units else None,
        "alpha_interval": krippendorff_alpha([[s for _, s in v] for v in units.values()], "interval")
        if units else None,
    }
    return out


# ---------------------------------------------------------------- output

def fmt(m: dict | None, pct: bool = True) -> str:
    if not m or m.get("value") is None:
        return "–"
    f = (lambda v: f"{100 * v:.1f}%") if pct else (lambda v: f"{v:+.3f}")
    return f"{f(m['value'])} [{f(m['lo'])}, {f(m['hi'])}]"


def summary(res: dict, lang: str) -> str:
    L = [f"# Results ({lang})", "",
         f"Pairs: {res['pairs_valid']} valid of {res['pairs_total']} "
         f"(format errors {100 * res['format_error_rate']:.1f}%). Intervals: 95%, bootstrap over questions.", "",
         "## RQ1 How often does the judge flip?", "",
         "| Measure | Value |", "|---|---|",
         f"| Flip rate | {fmt(res['flip_rate'])} |",
         f"| Flip rate, pairs with no tie verdict | {fmt(res['flip_rate_no_tie'])} |",
         f"| Slot A wins both runs | {fmt(res['first_slot_wins_both'])} |",
         f"| Slot B wins both runs | {fmt(res['second_slot_wins_both'])} |",
         f"| First-Position Preference | {fmt(res['fpp'], pct=False)} |",
         f"| Verdict labels consistent (ties allowed) | {100 * res['labels']['consistent']:.1f}% |",
         f"| Tie verdicts | {100 * res['labels']['tie_rate']:.1f}% |",
         f"| Verdict written before the explanation | {100 * res['labels']['verdict_first']:.1f}% |", "",
         "| Model pair | Flip rate | FPP |", "|---|---|---|"]
    for k, v in res["by_pair"].items():
        L.append(f"| {k} | {fmt(v['flip_rate'])} | {fmt(v['fpp'], pct=False)} |")
    if res.get("flip_by_human_gap"):
        L += ["", "## RQ2 Flips by human score gap", "", "| \\|gap\\| | Pairs | Flip rate |", "|---|---|---|"]
        for b in res["flip_by_human_gap"]:
           L.append(f"| {b['gap']} | {b['n']} | {fmt(b)} |")
    m = res["margin"]
    L += ["", "## RQ3 Confidence margin", "", "| | Mean margin |", "|---|---|",
         f"| Consistent pairs | {fmt(m['consistent'], pct=False)} |",
         f"| Flipped pairs | {fmt(m['flipped'], pct=False)} |",
         f"| Difference | {fmt(m['difference'], pct=False)} |",
         f"| AUC (margin predicts consistency) | {m['auc_consistent']:.3f} |", "",
         "| Margin quartile | Flip rate |", "|---|---|"]
    for i, q in enumerate(res["flip_by_margin_quartile"], 1):
        L.append(f"| Q{i} ({q['range'][0]:.2f}–{q['range'][1]:.2f}) | {fmt(q)} |")
    if res.get("agreement"):
        a = res["agreement"]
        L += ["", "## RQ4 Agreement with human annotators (pairs with a human winner)", "",
             "| Method | Agreement |", "|---|---|",
             f"| One order (mean of both single runs) | {fmt(a['single_order_mean'])} |",
             f"| Consistent pairs only | {fmt(a['consistent_only'])} (coverage {fmt(a['consistent_coverage'])}) |",
             f"| BPC (average both orders) | {fmt(a['bpc'])} |",
             f"| Baseline: word-overlap F1 vs gold | {fmt(a['f1_baseline'])} |"]
        if "cosine_baseline" in a:
           L.append(f"| Baseline: embedding cosine vs gold | {fmt(a['cosine_baseline'])} |")
    L += ["", "## Ranking", "", "| Model | Human mean (1–5) | BPC win rate |", "|---|---|---|"]
    for k, v in res["ranking"].items():
        hm = f"{v['human_mean']:.2f}" if v["human_mean"] is not None else "–"
        L.append(f"| {k} | {hm} | {100 * v['bpc_win_rate']:.1f}% |")
    ln = res["length"]
    L += ["", "## Length", "",
         f"- BPC picks the longer answer: {fmt(ln['bpc_prefers_longer'])}",
         f"- Flip rate, length gap above median: {fmt(ln['flip_rate_len_gap_above_median'])}; "
         f"at or below: {fmt(ln['flip_rate_len_gap_at_or_below_median'])}"]
    an = res["annotators"]
    if an["kappa"]:
        L += ["", "## Annotator agreement", "", "| Pair | n | Cohen's κ | Quadratic κ |", "|---|---|---|---|"]
        for k, v in an["kappa"].items():
           L.append(f"| {k[0]}+{k[1]} | {v['n']} | {v['kappa']:.3f} | {v['kappa_quadratic']:.3f} |")
        L += ["", f"Krippendorff's α: ordinal {an['alpha_ordinal']:.3f}, interval {an['alpha_interval']:.3f}"]
    return "\n".join(L) + "\n"


def figures(res: dict, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ink, muted, grid, surface = "#13242C", "#56686F", "#D2DBDF", "#FFFFFF"
    flip_c, x_c = "#C2255C", "#0B7285"
    plt.rcParams.update({"font.family": "sans-serif", "font.size": 12, "axes.edgecolor": grid,
                         "axes.labelcolor": muted, "xtick.color": muted, "ytick.color": muted,
                         "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": surface,
                         "axes.facecolor": surface, "svg.fonttype": "none"})
    out_dir.mkdir(parents=True, exist_ok=True)

    def bars(ax, labels, items, color, pct=True):
        vals = [(i["value"] or 0) for i in items]
        lo = [v - (i["lo"] if i["lo"] is not None else v) for v, i in zip(vals, items)]
        hi = [(i["hi"] if i["hi"] is not None else v) - v for v, i in zip(vals, items)]
        scale = 100 if pct else 1
        ax.bar(labels, [scale * v for v in vals], color=color, width=0.55,
               yerr=[[scale * v for v in lo], [scale * v for v in hi]],
               error_kw={"ecolor": ink, "elinewidth": 1.2, "capsize": 4})
        for i, v in enumerate(vals):
            ax.text(i, scale * (v + hi[i]) + (2 if pct else 0.02), f"{scale * v:.0f}%" if pct else f"{v:.2f}",
                    ha="center", color=ink, fontsize=12)
        ax.yaxis.grid(True, color=grid, linewidth=0.8)
        ax.set_axisbelow(True)

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(out_dir / f"{name}.svg")
        fig.savefig(out_dir / f"{name}.png", dpi=200)
        plt.close(fig)

    # RQ1: flip rate per model pair
    fig, ax = plt.subplots(figsize=(6.4, 4))
    labels = ["Tất cả"] + list(res["by_pair"])
    bars(ax, labels, [res["flip_rate"]] + [v["flip_rate"] for v in res["by_pair"].values()], flip_c)
    ax.set_ylabel("Tỉ lệ flip (%)")
    ax.set_ylim(0, 100)
    save(fig, "rq1_flip_rate")

    # RQ2: flip rate by human gap
    if res.get("flip_by_human_gap"):
        fig, ax = plt.subplots(figsize=(6.4, 4))
        g = res["flip_by_human_gap"]
        bars(ax, [f'{b["gap"]}\n(n = {b["n"]})' for b in g], g, flip_c)
        ax.set_xlabel("Chênh lệch điểm người chấm |X − Y|")
        ax.set_ylabel("Tỉ lệ flip (%)")
        ax.set_ylim(0, 100)
        save(fig, "rq2_flip_by_gap")

    # RQ3: flip rate by confidence quartile
    fig, ax = plt.subplots(figsize=(6.4, 4))
    q = res["flip_by_margin_quartile"]
    bars(ax, ["Q1\nthấp nhất", "Q2", "Q3", "Q4\ncao nhất"], q, flip_c)
    ax.set_xlabel("Độ tự tin của judge (margin, theo tứ phân vị)")
    ax.set_ylabel("Tỉ lệ flip (%)")
    ax.set_ylim(0, 100)
    save(fig, "rq3_flip_by_margin")

    # RQ4: agreement with humans
    if res.get("agreement"):
        a = res["agreement"]
        items = [("Một thứ tự", a["single_order_mean"]), ("Chỉ cặp\nnhất quán", a["consistent_only"]),
                 ("BPC", a["bpc"]), ("F1\n(baseline)", a["f1_baseline"])]
        if "cosine_baseline" in a:
            items.append(("Cosine\n(baseline)", a["cosine_baseline"]))
        fig, ax = plt.subplots(figsize=(6.4, 4))
        bars(ax, [i[0] for i in items], [i[1] for i in items], x_c)
        ax.set_ylabel("Khớp với người chấm (%)")
        ax.set_ylim(0, 100)
        save(fig, "rq4_agreement")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="vi")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--out-dir", type=Path, default=HERE / "results")
    parser.add_argument("--no-embeddings", action="store_true", help="skip the cosine baseline")
    args = parser.parse_args()
    out_dir = args.out_dir

    judgments = read_jsonl(args.data_dir / f"judgments_{args.lang}.jsonl")
    if not judgments:
        raise SystemExit(f"no judgments_{args.lang}.jsonl in {args.data_dir}: run judge.py first")
    questions = {q["qid"]: q for q in read_jsonl(args.data_dir / "questions.jsonl")}
    gold = {k: q["gold_answers"][0] for k, q in questions.items() if q.get("gold_answers")}
    answers = {}
    for m in MODELS:
        for r in read_jsonl(args.data_dir / f"answers_{m}.jsonl"):
            answers[(r["qid"], m)] = r.get("answer", "")
    per_answer, by_annotator, gold_wrong = load_scores(args.data_dir, args.data_dir / "key.csv")

    rows = pair_table(judgments, per_answer, answers, gold, gold_wrong)
    has_cos = False if args.no_embeddings else embedding_cosines(rows, answers, gold)
    res = compute(rows, by_annotator, has_cos)
    res["gold_wrong_questions"] = len(gold_wrong)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"metrics_{args.lang}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    (out_dir / f"summary_{args.lang}.md").write_text(summary(res, args.lang), encoding="utf-8")
    figures(res, out_dir / "figures")
    # Pair-level rows for the demo and qualitative analysis; names models, so git-ignored.
    with (args.data_dir / f"pairs_{args.lang}.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print((out_dir / f"summary_{args.lang}.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
