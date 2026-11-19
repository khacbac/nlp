# Quất Store support inbox: an AI judge checked against reply order

A working support tool for a made-up shop, Quất Store. For each customer
message two models write a reply draft, and an LLM judge picks the better
one. The judge is the one from the experiment (MT-Bench pair-v2 prompt,
`[[A]]`/`[[B]]`/`[[C]]` verdict), and it is checked against itself:

```
draft 1, draft 2 ──► run 1: A = draft 1, B = draft 2 ──► pick ┐
                 └─► run 2: A = draft 2, B = draft 1 ──► pick ┴─► same draft in both runs? ──► send
                                                                  otherwise (flip, half tie,
                                                                  bad format) ─────────────► a person picks
```

The experiment found that a 7B judge changes its verdict on 48.7% of pairs
when only the order changes. The app turns that finding into a routing rule:
a reply is sent automatically only if the judge's pick survives the swap.
The report page shows, for the current inbox, how often the judge flipped,
how often it picked slot A, and how many replies a single-pass judge would
have sent on position alone.

## Run

```
cp .env.example .env      # add GROQ_API_KEY and/or GEMINI_API_KEY
python app/server.py      # then open http://localhost:8010
```

Python 3.10+, standard library only. Settings (gear icon) pick the two
draft writers and the judge from the models your keys can reach.

## Files

| File | Role |
|---|---|
| `arbiter.py` | The core: judge both orders, combine into agree / tie / partial / flip / invalid |
| `llm.py` | Provider client (Groq, Gemini, OpenRouter); also used by `demo/server.py` |
| `server.py` | Inbox state and JSON API |
| `index.html` | The inbox UI |
| `data/policy.md`, `data/tickets.json` | Made-up shop policy and customer messages |
| `test_arbiter.py` | Guards the routing rule |

Inbox progress is saved to `data/state.json` (gitignored); "Làm mới hộp thư"
in the settings sheet clears it.
