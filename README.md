# Position Bias in LLM-as-a-Judge: a Vietnamese Case Study

Final project for NLP501 (Natural Language Processing). Team ABNQ: Hồ Khắc Bắc, Đặng Thành Nhân, Nguyễn Việt Anh, Lê Trọng Quang. Lecturer: Nguyễn Sĩ Thìn.

| Path | Content |
|---|---|
| `report.md` | Final report |
| `proposal.md`, `proposal.html` | Project proposal |
| `experiment/` | Pipeline: question selection, answer generation, two-order judging, analysis; data and results (see `experiment/README.md`) |
| `app/` | Tax inbox demo for household businesses with a position-robust arbiter (see `app/README.md`) |
| `demo.html`, `demo/server.py` | Interactive order-swap (flip) demo |
| `papers/` | Literature review cards and comparison matrix |
| `specs/` | Design notes for the tax inbox app |
| `assets/` | Figures |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your own API keys
python experiment/analyze.py
python app/server.py
python demo/server.py       # then open http://localhost:8000
```
