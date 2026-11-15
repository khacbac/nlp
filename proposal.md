# Position Bias in LLM-as-a-Judge: Analysis and a Vietnamese Case Study

Final project proposal for NLP501.22 (Natural Language Processing).

- **Team:** ABNQ: Hồ Khắc Bắc, Đặng Thành Nhân, Nguyễn Việt Anh, Lê Trọng Quang
- **Lecturer:** Nguyễn Sĩ Thìn

## Topic at a glance

| Field | Content |
|---|---|
| Topic | Thiên vị vị trí của giám khảo LLM: phân tích và kiểm chứng trên tiếng Việt (Position Bias in LLM-as-a-Judge: Analysis and a Vietnamese Case Study) |
| Area | NLP Evaluation |
| Scope | Why an LLM judge changes its verdict when only the order of two answers changes: how to measure it, its causes, and mitigations; checked with a small experiment on Vietnamese reading-comprehension answers. |
| Technical content | Pairwise comparison vs. single-answer grading; consistency under swapping (flip rate). Position, verbosity and self-enhancement bias; label token bias for "A"/"B". Mitigation: judging both orders, Balanced Position Calibration; confidence from token probabilities. |
| Models / methods | Answers from 3 free models (Qwen2.5-7B-Instruct, ChatGPT, Gemini Flash); MT-Bench pairwise judge prompt, Balanced Position Calibration, Qwen2.5-Instruct (open-weight judge); baselines word-overlap F1 and sentence-embedding cosine. |
| Data / benchmark | MT-Bench, Vicuna-80 (figures from the original papers); UIT-ViQuAD 2.0 for the team's experiment (Vietnamese, 150 questions × 3 answers = 450 pairs, two annotators). |
| Expected outcome | The six evaluation criteria measured on Vietnamese, vs. English; when flips occur (by quality gap and judge confidence); a recommendation on judging both orders, tested against human ratings, with a ranking of Qwen, ChatGPT and Gemini on Vietnamese; a live flip demo. |
| Open question | How can we tell when an LLM judge's verdict is trustworthy, especially for a lower-resource language such as Vietnamese? |
| References | Zheng et al. (NeurIPS 2023, MT-Bench) arXiv:2306.05685; Wang et al. (2023, LLMs are not Fair Evaluators) arXiv:2305.17926 |

## Description

LLMs are increasingly used to grade the outputs of other LLMs, but a judge
may change its verdict when the two answers being compared are simply
swapped. This project studies that phenomenon for Vietnamese: how often the
judge flips, on which kinds of answer pairs, whether flips coincide with low
judge confidence, and whether judging in both orders improves agreement with
human annotators. It uses an open-weight LLM as the judge on about 150
Vietnamese reading-comprehension questions, with human ratings as the
reference, and requires no model training.

## What "swapping" means

The judge receives one question and two answers in a single prompt and
picks the better one. Each pair is judged twice. The answers are identical
in both runs; only which one is shown first (as "A") changes. A fair judge
picks the same underlying answer both times. A flip is a pair where the
winner in the first run differs from the winner in the second.

## Motivation and evidence

**Order affects human judges.** Jury scores in the Eurovision Song Contest
and European figure skating rise with serial position, both when judges
score at the end and when they score after each performance (Bruine de
Bruin, 2005). In a large-scale English writing test in China (67,500
essays, 88 raters, 146,727 scores), a rater's score for an essay is pulled
toward the score they gave the previous essay (Zhao et al., 2017),
consistent with Attali (2011).

**Order affects LLM judges.** On very similar answer pairs, Claude-v1,
GPT-3.5 and GPT-4 keep their verdict after a swap in only 23.8%, 46.2% and
65.0% of cases (Zheng et al., 2023, Table 2). With ChatGPT as the judge,
Vicuna-13B can "beat" ChatGPT on 66 of 80 questions just by changing the
order of the answers (Wang et al., 2023). GPT-4's consistency rises from
67.5% to 98.8% as the quality gap between the two compared models grows
(Zheng et al., 2023, Table 11).

**Proposed causes.** For humans: impressions built up candidate by
candidate rather than memory alone (Bruine de Bruin, 2005), scale
calibration along a series (Unkelbach et al., 2012), and semi-automatic
rating of similar essays (Attali, 2011; Zhao et al., 2017). For LLMs: the
training data or the left-to-right causal architecture (Zheng et al.,
2023), prior preference for certain label tokens (Zheng et al., 2024), and
uneven use of information across positions in the context (Liu et al.). On
both sides order matters most when the two items are hard to tell apart.
Sharing that condition does not imply sharing a mechanism.

**The gap.** Across 25 languages, LLM judges reach a Fleiss' kappa of only
about 0.3 between languages, worst for low-resource ones (Fu and Liu,
2025). No study was found that measures position bias on long Vietnamese
answers against human ratings.

## Research questions

1. How often does an LLM judge flip its verdict when the order of two
   Vietnamese answers is swapped?
2. Are flips concentrated on pairs that human annotators rate as close in
   quality?
3. Do flips coincide with low judge confidence, measured by the token
   probabilities the judge assigns to each verdict?
4. Does judging in both orders and keeping only consistent verdicts
   improve agreement with human annotators?

A secondary condition compares the flip rate on the same content in
Vietnamese and in English.

## Approach

1. **Data:** 150 answerable questions (`is_impossible = false`) with their
   source passages from the validation split of UIT-ViQuAD 2.0 (VLSP 2021
   ViMRC; public copy on Hugging Face: `taidng/UIT-ViQuAD2.0`). Questions
   asking "why" or "how" are preferred so that answers are long enough to
   compare, and the sample is spread across many articles. The gold answer
   span is shown to the annotators as a reference. The English condition
   uses a machine translation of the same 150 items.
2. **Answer pairs:** three free-to-use models answer every question with
   the same prompt: Qwen2.5-7B-Instruct (on Colab), ChatGPT (free tier) and
   Gemini Flash (Google AI Studio free tier). The three answers per
   question are paired three ways (Qwen–ChatGPT, Qwen–Gemini,
   ChatGPT–Gemini), 450 pairs in total.
3. **Grading in parallel:**
   - *Human reference:* two annotators rate answers independently on a 1-5
     scale using a written rubric, blind to the source model and to the
     judge's verdict. Inter-annotator agreement is reported with Cohen's
     kappa.
   - *LLM judge:* an open-weight instruction-tuned LLM (candidate:
     Qwen2.5-Instruct) run on Google Colab. Each pair is judged in both
     orders and the verdict token probabilities are saved. No model is
     trained.
4. **Analysis:** the six evaluation criteria below, computed over all
   pairs and per model pair. Word-overlap F1 and sentence-embedding cosine
   serve as context baselines.

## Evaluation criteria

P1 and P2 are the probabilities the judge gives an answer in run 1 and
run 2, after mapping the "A"/"B" labels back to X/Y.

| Criterion | For | How it is computed |
|---|---|---|
| Flip Rate | RQ1 | Position-following flips ÷ all pairs. Flip: P1(X) > P1(Y) but P2(Y) > P2(X), or the reverse. |
| First-Position Preference | RQ1 | P(win \| first) − P(win \| second), for X and for Y. Positive means the judge favours the first slot. |
| Confidence Margin | RQ3 | Δ = \|P(win) − P(lose)\|, averaged over both runs; compared between flipped and consistent pairs. |
| Human Score Gap | RQ2 | Mean annotator score for X − for Y; pairs are binned by gap and Flip Rate is computed per bin. |
| Balanced Position Calibration | RQ4 | Average the scores of both orders (Wang et al., 2023). Human agreement compared for one order, consistent pairs only, and after BPC. |
| Vietnamese vs. English | Secondary | Recompute the criteria on an English translation of the same pairs. |

## Techniques

| Technique | Used to | Why this one |
|---|---|---|
| 3 free models write the answers | Create the pairs | Qwen, ChatGPT and Gemini are free to use and differ in Vietnamese ability, giving both clear-gap and close pairs; they are what a low-budget team would actually choose between. |
| Pairwise judging in both orders | Measure flips | Position bias only shows when there are two positions to swap; single-answer grading cannot measure it. This is how Zheng et al. (2023) measure it. |
| Open-weight judge (Qwen2.5-Instruct) | Act as the judge | Full access to token probabilities, runs on Colab, supports Vietnamese. Not every paid API returns token probabilities. |
| Token probabilities of "A" / "B" | Measure confidence | Read directly from the decoder output of the same run, with no extra runs and no reliance on the model stating its own confidence. |
| Balanced Position Calibration | Mitigate | Combines the two orders already judged, with no training (Wang et al., 2023). |
| Two annotators + Cohen's kappa | Provide the reference | Kappa removes chance agreement, so it shows whether the rubric is clear enough to serve as the reference. |
| Word-overlap F1, sentence-embedding cosine | Baselines | F1 is the standard metric for SQuAD-style reading comprehension; both reuse course representations and show why an LLM judge is needed. |

Out of scope: training or fine-tuning the judge, and using a paid API as
the main judge.

## Link to the course

Grading an answer is a text-comparison problem, the "vector comparison"
step of the course pipeline. The baselines reuse bag-of-words and
embedding representations. The analysis of the judge relies on how a
Transformer decoder generates tokens from a probability distribution and
on positional information in its input.

## Expected outcome

- The six evaluation criteria measured on Vietnamese, with a comparison
  to English, overall and per model pair.
- A ranking of Qwen, ChatGPT and Gemini on Vietnamese answers, based on
  position-corrected (BPC) verdicts checked against human ratings.
- An analysis of when flips occur and how they relate to judge confidence.
- A tested recommendation for using LLM judges more reliably.
- A live demo in which the judge reverses its verdict on the same pair of
  answers after a swap.

## Future direction

A harness that picks a free model: once the judge is known to be
trustworthy (both orders, BPC), it can compare Qwen, ChatGPT and Gemini
per question type, and a routing layer can send each question to the
cheapest free model that is good enough, calling another model only when
needed. If the judge is position-biased, that ranking is wrong too, so
this project is the groundwork.

## Limitations

- About 150 questions (450 pairs) and two annotators support preliminary
  conclusions only; each annotator rates 450 answers.
- Qwen both writes answers and acts as the judge, so the judge may favour
  Qwen's answers (self-enhancement bias). This cannot create flips, since
  each pair is judged in both orders, but it can shift the winner; pairs
  involving Qwen are reported separately.
- The free tiers of ChatGPT and Gemini may change model versions over
  time; the model name and generation date are recorded.
- Position bias is already documented for English; the contribution here
  is the Vietnamese setting and the analysis of when and why flips occur.
- The Vietnamese versus English comparison depends on translation quality,
  so differences may partly reflect translation rather than language.
- A literature search found no study of this bias against human ratings on
  long Vietnamese answers, but the search was not exhaustive.

## References

1. Bruine de Bruin, W. (2005). Save the last dance for me: unwanted serial
   position effects in jury evaluations. Acta Psychologica 118(3),
   245-260. doi:10.1016/j.actpsy.2004.08.005
2. Zhao, H., Andersson, B., Guo, B., & Xin, T. (2017). Sequential Effects
   in Essay Ratings: Evidence of Assimilation Effects Using
   Cross-Classified Models. Frontiers in Psychology 8:933.
   doi:10.3389/fpsyg.2017.00933
3. Unkelbach, C., Ostheimer, V., Fasold, F., & Memmert, D. (2012). A
   calibration explanation of serial position effects in evaluative
   judgments. Organizational Behavior and Human Decision Processes 119,
   103-113.
4. Attali, Y. (2011). Sequential effects in essay ratings. Educational and
   Psychological Measurement 71, 68-79. doi:10.1177/0013164410387344
5. Zheng et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.
   NeurIPS 2023 Datasets and Benchmarks. arXiv:2306.05685
6. Wang et al. Large Language Models are not Fair Evaluators. 2023.
   arXiv:2305.17926
7. Zheng et al. Large Language Models Are Not Robust Multiple Choice
   Selectors. ICLR 2024. arXiv:2309.03882
8. Liu et al. Lost in the Middle: How Language Models Use Long Contexts.
   TACL. arXiv:2307.03172
9. Fu and Liu. How Reliable is Multilingual LLM-as-a-Judge? Findings of
   EMNLP 2025. arXiv:2505.12201
10. Gu et al. A Survey on LLM-as-a-Judge. arXiv:2411.15594
11. Nguyen, K. V., Tran, S. Q., Nguyen, L. T., Huynh, T. V., Luu, S. T., &
    Nguyen, N. L.-T. (2022). VLSP 2021 - ViMRC Challenge: Vietnamese Machine
    Reading Comprehension. arXiv:2203.11400. Dataset:
    https://huggingface.co/datasets/taidng/UIT-ViQuAD2.0
