# Results (vi)

Pairs: 1500 valid of 1500 (format errors 0.0%). Intervals: 95%, bootstrap over questions.

## RQ1 How often does the judge flip?

| Measure | Value |
|---|---|
| Flip rate | 48.7% [45.9%, 51.5%] |
| Flip rate, pairs with no tie verdict | 34.8% [31.3%, 38.3%] |
| Slot A wins both runs | 42.5% [39.6%, 45.4%] |
| Slot B wins both runs | 6.2% [4.7%, 7.8%] |
| First-Position Preference | +0.363 [+0.325, +0.399] |
| Verdict labels consistent (ties allowed) | 50.9% |
| Tie verdicts | 24.3% |
| Verdict written before the explanation | 85.5% |

| Model pair | Flip rate | FPP |
|---|---|---|
| qwen – gpt-oss | 43.2% [38.8%, 47.8%] | +0.268 [+0.212, +0.322] |
| qwen – gemini | 51.6% [47.2%, 55.8%] | +0.416 [+0.366, +0.466] |
| gpt-oss – gemini | 51.2% [46.8%, 55.6%] | +0.404 [+0.350, +0.456] |

## RQ2 Flips by human score gap

| \|gap\| | Pairs | Flip rate |
|---|---|---|
| 0 | 645 | 56.6% [52.3%, 60.6%] |
| 0.5–1 | 659 | 43.7% [39.8%, 47.7%] |
| 1.5–2 | 136 | 36.0% [28.7%, 43.8%] |
| ≥ 2.5 | 18 | 44.4% [16.7%, 76.9%] |

## RQ3 Confidence margin

| | Mean margin |
|---|---|
| Consistent pairs | +0.882 [+0.870, +0.895] |
| Flipped pairs | +0.870 [+0.857, +0.883] |
| Difference | +0.012 [-0.004, +0.029] |
| AUC (margin predicts consistency) | 0.564 |

| Margin quartile | Flip rate |
|---|---|
| Q1 (0.03–0.80) | 51.2% [46.4%, 56.1%] |
| Q2 (0.80–0.96) | 54.9% [49.6%, 60.2%] |
| Q3 (0.96–1.00) | 51.5% [46.1%, 57.0%] |
| Q4 (1.00–1.00) | 37.1% [31.5%, 43.1%] |

## RQ4 Agreement with human annotators (pairs with a human winner)

| Method | Agreement |
|---|---|
| One order (mean of both single runs) | 37.1% [34.3%, 40.1%] |
| Consistent pairs only | 27.6% [23.1%, 32.4%] (coverage 57.6% [54.0%, 61.2%]) |
| BPC (average both orders) | 34.8% [31.3%, 38.6%] |
| Baseline: word-overlap F1 vs gold | 68.9% [65.3%, 72.4%] |
| Baseline: embedding cosine vs gold | 57.1% [53.3%, 60.9%] |

## Ranking

| Model | Human mean (1–5) | BPC win rate |
|---|---|---|
| qwen | 4.52 | 35.7% |
| gpt-oss | 4.27 | 67.3% |
| gemini | 4.82 | 47.0% |

## Length

- BPC picks the longer answer: 69.2% [66.7%, 71.6%]
- Flip rate, length gap above median: 36.1% [32.4%, 40.0%]; at or below: 61.1% [57.3%, 64.6%]

## Annotator agreement

| Pair | n | Cohen's κ | Quadratic κ |
|---|---|---|---|
| A+B | 252 | 0.700 | 0.772 |
| A+C | 252 | 0.615 | 0.735 |
| A+D | 249 | 0.617 | 0.782 |
| B+C | 249 | 0.648 | 0.756 |
| B+D | 249 | 0.758 | 0.822 |
| C+D | 249 | 0.649 | 0.708 |

Krippendorff's α: ordinal 0.739, interval 0.760
