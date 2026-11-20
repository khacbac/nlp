# ABNQ Store support inbox: an AI judge checked against reply order

A working support tool for a made-up online xiangqi (Chinese chess) shop, ABNQ Store. For each customer
message two models write a reply draft, and an LLM judge picks the better
one. The judge is the one from the experiment (MT-Bench pair-v2 prompt,
`[[A]]`/`[[B]]`/`[[C]]` verdict), and it is checked against itself:

```
draft 1, draft 2 ──► run 1: A = draft 1, B = draft 2 ──► pick ┐
                 └─► run 2: A = draft 2, B = draft 1 ──► pick ┴─► same draft in both runs? ──► send
                                                                  otherwise (flip, half tie,
                                                                  bad format) ─────────────► a person picks
                                                     picked draft breaks a checked fact ──► a person picks
```

The experiment found that a 7B judge changes its verdict on 48.7% of pairs
when only the order changes. The app turns that finding into a routing rule:
a reply is sent automatically only if the judge's pick survives the swap.
The swap removes position bias, but the experiment also found that a
consistent judge is not a correct one: keeping only consistent verdicts
agreed with humans on 27.6% of pairs, while a plain comparison against the
gold answer reached 68.9%. In a shop the policy and stock table are the gold
answer, so a second layer (`factcheck.py`) checks each draft's amounts,
percentages, stock claims and promised dates against them by rule, and holds
a consistent pick whose draft contradicts them. It cannot judge cases that
need reading (is a bicycle knock "impact damage"?); those stay with the judge.

The report page shows, for the current inbox, how often the judge flipped,
how often it picked slot A, how many replies a single-pass judge would have
sent on position alone, and how many consistent picks the fact check held.

## Run

```
cp .env.example .env      # add GROQ_API_KEY and/or GEMINI_API_KEY
python app/server.py      # then open http://localhost:8010
```

Python 3.10+, standard library only. Settings (gear icon) pick the two
draft writers and the judge from the models your keys can reach.

To measure what each layer buys, run every trap ticket through the judge
several times and score the same judgments as single-pass, swap, and
swap + fact check (results in `results/bench.md`; the JSONL resumes):

```
python app/bench.py --judges groq-gpt-oss-20b,groq-gpt-oss-120b --repeats 3
```

## Files

| File | Role |
|---|---|
| `arbiter.py` | The core: judge both orders, combine into agree / tie / partial / flip / invalid |
| `factcheck.py` | Rule check of each draft against the policy and stock table; holds a consistent pick that breaks a fact |
| `llm.py` | Provider client (Groq, Gemini, OpenRouter); also used by `demo/server.py` |
| `server.py` | Inbox state and JSON API |
| `index.html` | The inbox UI |
| `data/policy.md`, `data/tickets.json` | Made-up shop policy and customer messages. Tickets with `canned` ship a fixed draft pair (one breaks a policy detail; `answer` names the correct one) instead of AI drafts; "Soạn gợi ý khác" switches them to AI drafts. Tickets marked `reserve` stay out of the inbox until the presenter presses N |
| `bench.py` | Batch run over the trap tickets: wrong / right / to-a-person for single-pass, swap, and swap + fact check |
| `DEMO.md` | Demo script with the answer key for the canned tickets |
| `data/products.json` | Catalog with stock; the policy's stock table is generated from it. `aliases`/`not` let the fact check spot a product named in a draft |
| `static/products/` | Product photos from Wikimedia Commons; authors and licenses at `/nguon-anh` |
| `test_arbiter.py` | Guards the routing rule and the fact check against the canned trap pairs |

Inbox progress is saved to `data/state.json` (gitignored); "Làm mới hộp thư"
in the settings sheet clears it.
