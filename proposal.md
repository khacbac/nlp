# Does the Order Matter? Position Bias of LLM Judges on Vietnamese Answers

Final project proposal for NLP501.

## Description

LLMs are increasingly used to grade the outputs of other LLMs, but a judge
may change its verdict when the two answers being compared are simply
swapped. This project studies that one phenomenon in depth for Vietnamese:
how often the judge flips, on which kinds of answer pairs, whether flips
coincide with low judge confidence, and whether judging in both orders
improves agreement with human annotators. It uses an open-weight LLM as
the judge on about 150 Vietnamese reading-comprehension questions, with
human ratings as the reference, and requires no model training.

## What "swapping" means

The judge receives one question and two answers in a single prompt and
picks the better one. Each pair is judged twice. The answers are identical
in both runs; only which one is shown first (as "A") changes. A fair judge
picks the same underlying answer both times. A flip is a pair where the
winner in the first run differs from the winner in the second.

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

## Method

- **Data:** about 150 Vietnamese reading-comprehension questions with
  source passages (candidates: UIT-ViQuAD, VMLU Vi-SQuAD; access not yet
  confirmed). Each question is answered by models of different quality to
  form answer pairs.
- **Human reference:** two annotators rate answers independently on a 1-5
  scale using a written rubric, blind to the source model and to the
  judge's verdict. Inter-annotator agreement is reported with Cohen's
  kappa.
- **Judge:** an open-weight instruction-tuned LLM (candidate:
  Qwen2.5-Instruct) run on Google Colab, so verdict token probabilities
  are available.
- **Baselines for context:** word-overlap F1 and sentence-embedding cosine
  similarity, to show where simpler text-comparison methods from the
  course fail before the LLM judge is introduced.

## Link to the course

Grading an answer is a text-comparison problem, the "vector comparison"
step of the course pipeline. The baselines reuse bag-of-words and
embedding representations. The analysis of the judge relies on how a
Transformer decoder generates tokens from a probability distribution and
on positional information in its input.

## Expected outcome

- A measured flip rate for Vietnamese, with a comparison to English.
- An analysis of when flips occur and how they relate to judge confidence.
- A tested recommendation for using LLM judges more reliably.
- A live demo in which the judge reverses its verdict on the same pair of
  answers after a swap.

## Limitations

- About 150 questions and two annotators support preliminary conclusions
  only.
- Position bias is already documented for English; the contribution here
  is the Vietnamese setting and the analysis of when and why flips occur.
- The Vietnamese versus English comparison depends on translation quality,
  so differences may partly reflect translation rather than language.
- A literature search found no study of this bias against human ratings on
  long Vietnamese answers, but the search was not exhaustive.

## References

1. Zheng et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena.
   NeurIPS 2023. arXiv:2306.05685
2. Gu et al. A Survey on LLM-as-a-Judge. arXiv:2411.15594
3. Bui et al. VMLU Benchmarks: A Comprehensive Benchmark Toolkit for
   Vietnamese LLMs. ACL 2025. https://aclanthology.org/2025.acl-long.563
4. Fu and Liu. How Reliable is Multilingual LLM-as-a-Judge? Findings of
   EMNLP 2025. arXiv:2505.12201
