"""Judge every answer pair in both orders with an open-weight LLM.

For each question the three answers form three pairs (X, Y):
qwen-gpt-oss, qwen-gemini, gpt-oss-gemini. Each pair is judged twice with
the MT-Bench pairwise prompt (Zheng et al., 2023, Fig. 5):

    order "xy": X is shown as Assistant A, Y as Assistant B
    order "yx": Y is shown as Assistant A, X as Assistant B

Only the order changes between the two runs. The judge writes an
explanation and then a verdict "[[A]]", "[[B]]" or "[[C]]" (tie). Decoding
is greedy (temperature 0), so a rerun gives the same verdict and repetition
stability (Shi et al., 2024) is 1 by construction.

Confidence comes from the same run: at the verdict token we read the
probabilities of "A", "B" and "C" from the top-k log-probabilities. p_x and
p_y are those of A/B renormalised over A+B and mapped back to X/Y, so the
two runs of a pair are directly comparable.

The judge sees the passage, the question and the two raw answers (not the
gold answer, and not the emphasis-stripped text shown to annotators).

Output: judgments_<lang>.jsonl, one line per (pair, order). The script is
safe to stop and rerun: finished (pair, order) rows are skipped, and a
half-written last line is ignored.

Usage (Colab / Kaggle T4 GPU; pip install vllm):
    python judge.py --answers-dir /content/drive/MyDrive/nlp-answers \
                    --out-dir /content/drive/MyDrive/nlp-answers
    python judge.py --limit 10      # first 10 questions only, as a trial
"""

import argparse
import itertools
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).parent / "data"
MODELS = ["qwen", "gpt-oss", "gemini"]
JUDGE_MODEL = "Qwen/Qwen2.5-7B-Instruct-AWQ"  # 4-bit, fits a 16 GB T4
TOP_LOGPROBS = 20
MAX_TOKENS = 768

# MT-Bench "pair-v2" system prompt, verbatim (FastChat judge_prompts.jsonl).
SYSTEM_PROMPT = (
    "Please act as an impartial judge and evaluate the quality of the responses provided by two AI "
    "assistants to the user question displayed below. You should choose the assistant that follows the "
    "user's instructions and answers the user's question better. Your evaluation should consider factors "
    "such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. "
    "Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position "
    "biases and ensure that the order in which the responses were presented does not influence your decision. "
    "Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the "
    "assistants. Be as objective as possible. After providing your explanation, output your final verdict by "
    'strictly following this format: "[[A]]" if assistant A is better, "[[B]]" if assistant B is better, '
    'and "[[C]]" for a tie.'
)
# MT-Bench pair-v2 user template; the passage is added to the question, since
# the answer models were asked to answer from it.
USER_TEMPLATE = """[User Question]
{question}

[The Start of Assistant A's Answer]
{answer_a}
[The End of Assistant A's Answer]

[The Start of Assistant B's Answer]
{answer_b}
[The End of Assistant B's Answer]"""
QUESTION_TEMPLATE = "Đoạn văn:\n{context}\n\nCâu hỏi: {question}"

VERDICT_RE = re.compile(r"\[\[([ABC])\]\]")


def read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file, skipping a half-written line left by a killed run."""
    rows = []
    if path.exists():
        for line in path.open(encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"  skipping a broken line in {path.name}")
    return rows


def make_pairs(questions: list[dict], answers: dict[tuple[str, str], str]) -> list[dict]:
    """All three model pairs per question, each in both orders."""
    jobs = []
    for q in questions:
        for x, y in itertools.combinations(MODELS, 2):
            if (q["qid"], x) not in answers or (q["qid"], y) not in answers:
                continue
            for order in ("xy", "yx"):
                jobs.append({"qid": q["qid"], "x": x, "y": y, "order": order, "q": q})
    return jobs


def messages(job: dict, answers: dict[tuple[str, str], str]) -> list[dict]:
    q = job["q"]
    first, second = (job["x"], job["y"]) if job["order"] == "xy" else (job["y"], job["x"])
    user = USER_TEMPLATE.format(
        question=QUESTION_TEMPLATE.format(context=q["context"], question=q["question"]),
        answer_a=answers[(q["qid"], first)],
        answer_b=answers[(q["qid"], second)],
    )
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def read_verdict(tokens: list[str], top: list[dict[str, float]]) -> tuple[str | None, dict[str, float]]:
    """Find the last "[[A|B|C]]" in the generated tokens and the label probabilities there.

    tokens: decoded text of each generated token.
    top:    for each position, {decoded candidate token: logprob} (top-k, includes the chosen one).
    A tokenizer may emit "[[A" as one token or "[[" then "A"; either way the
    candidates at the token holding the letter are stripped of "[" and spaces,
    and probabilities are summed per leading letter.
    """
    text = "".join(tokens)
    matches = list(VERDICT_RE.finditer(text))
    if not matches:
        return None, {}
    letter_at = matches[-1].start(1)
    pos = 0
    for i, tok in enumerate(tokens):
        if pos <= letter_at < pos + len(tok):
            probs = {"A": 0.0, "B": 0.0, "C": 0.0}
            prefix = text[pos:letter_at]  # e.g. "[[" when the token is "[[A"
            for cand, logprob in top[i].items():
                if not cand.startswith(prefix):
                    continue
                label = cand[len(prefix):].lstrip("[ ")[:1]
                if label in probs:
                    probs[label] += math.exp(logprob)
            return matches[-1].group(1), probs
        pos += len(tok)
    return matches[-1].group(1), {}


def to_xy(order: str, verdict: str | None, probs: dict[str, float]) -> dict:
    """Map the A/B labels of one run back to the underlying answers X and Y."""
    a, b = ("x", "y") if order == "xy" else ("y", "x")
    winner = {"A": a, "B": b, "C": "tie"}.get(verdict) if verdict else None
    pa, pb = probs.get("A", 0.0), probs.get("B", 0.0)
    if pa + pb == 0:
        return {"winner": winner, "p_x": None, "p_y": None}
    p = {a: pa / (pa + pb), b: pb / (pa + pb)}
    return {"winner": winner, "p_x": p["x"], "p_y": p["y"]}


def judge_chunks(jobs: list[dict], answers: dict, model: str, size: int = 100):
    """Yield (job, record fields) in chunks, so a disconnect loses at most one chunk."""
    from vllm import LLM, SamplingParams  # only needed on the GPU machine

    llm = LLM(model, quantization="awq" if "AWQ" in model else None, dtype="half",
              max_model_len=6144, gpu_memory_utilization=0.9)
    params = SamplingParams(temperature=0, max_tokens=MAX_TOKENS, logprobs=TOP_LOGPROBS)
    for start in range(0, len(jobs), size):
        chunk = jobs[start:start + size]
        outputs = llm.chat([messages(j, answers) for j in chunk], params, use_tqdm=False)
        for job, o in zip(chunk, outputs):
            out = o.outputs[0]
            tokens, top = [], []
            for tid, lp in zip(out.token_ids, out.logprobs or []):
                tokens.append(lp[tid].decoded_token or "")
                cands: dict[str, float] = {}
                for c in lp.values():  # two ids can decode to the same text; keep both masses
                    key = c.decoded_token or ""
                    cands[key] = math.log(math.exp(cands.get(key, -math.inf)) + math.exp(c.logprob))
                top.append(cands)
            verdict, probs = read_verdict(tokens, top)
            yield job, {
                "verdict": verdict,
                "p_label": probs,
                "finish_reason": out.finish_reason or "",
                "judgment": out.text.strip(),
            }
        print(f"  [{start + len(chunk)}/{len(jobs)}]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="vi", help="tag for the output file (English condition: later)")
    parser.add_argument("--model", default=JUDGE_MODEL)
    parser.add_argument("--limit", type=int, help="only the first N questions (trial run)")
    parser.add_argument("--questions", type=Path, default=DATA / "questions.jsonl")
    parser.add_argument("--answers-dir", type=Path, default=DATA)
    parser.add_argument("--out-dir", type=Path, default=DATA)
    args = parser.parse_args()
    out_path = args.out_dir / f"judgments_{args.lang}.jsonl"

    questions = read_jsonl(args.questions)[: args.limit]
    answers = {}
    for m in MODELS:
        for r in read_jsonl(args.answers_dir / f"answers_{m}.jsonl"):
            if r.get("answer"):
                answers[(r["qid"], m)] = r["answer"]
    jobs = make_pairs(questions, answers)
    done = {(r["qid"], r["x"], r["y"], r["order"]) for r in read_jsonl(out_path)}
    todo = [j for j in jobs if (j["qid"], j["x"], j["y"], j["order"]) not in done]
    print(f"{len(todo)} judgments to run, {len(jobs) - len(todo)} already done -> {out_path}")
    if not todo:
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    with out_path.open("a", encoding="utf-8") as out:
        if out.tell() > 0:  # a killed run may leave a line without "\n"
            with out_path.open("rb") as f:
                f.seek(-1, os.SEEK_END)
                if f.read(1) != b"\n":
                    out.write("\n")
        for job, res in judge_chunks(todo, answers, args.model):
            mapped = to_xy(job["order"], res["verdict"], res["p_label"])
            errors += res["verdict"] is None
            out.write(json.dumps({
                "qid": job["qid"], "x": job["x"], "y": job["y"], "order": job["order"],
                **mapped, **res,
                "judge_model": args.model, "lang": args.lang,
                "judged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }, ensure_ascii=False) + "\n")
            out.flush()
    print(f"done; {errors} judgments without a readable verdict (format errors)")


if __name__ == "__main__":
    main()
