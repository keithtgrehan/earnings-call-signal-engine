# Netflix Retrieval Demo

## Boundary First

This demo adds a supporting-only retrieval layer over the existing Netflix case pack.

What remains canonical:

- transcript-backed chunks
- deterministic guidance / QA / shareholder-letter artifacts
- explicit source locators and spans

What retrieval adds:

- faster navigation to bounded evidence rows
- lexical and semantic follow-up search
- row-to-row similarity without dropping provenance

What retrieval does **not** do:

- it does not adjudicate truth
- it does not replace transcript review
- it does not make predictive or statistical claims

## Example 1: Find guidance pressure moments

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  "guidance pressure moments" \
  --case-id netflix_q1_2022 \
  --mode hybrid \
  --top-k 5
```

Representative hits:

- `guidance_row:1`: Q1 miss versus the prior 2.5M paid-net-add guide
- `guidance_row:42`: tactical clarification around churn and Q1 performance
- `guidance_row:4`: explicit caution against over-reading the negative Q2 guide
- `guidance_row:8`: slower revenue growth and the need to manage through it

Use:

- surfaces pressure-oriented guidance rows quickly
- keeps the reviewer on transcript-backed spans rather than vague summaries

## Example 2: Find ad-supported strategy moments

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  "ad-supported strategy moments" \
  --case-id netflix_q1_2022 \
  --mode hybrid \
  --top-k 6
```

Representative hits:

- `qa_pair_011_question`: analyst question on a lower-priced ad-supported tier
- `qa_pair_011_answer`: management answer describing ads as a gradual, not short-term, path
- transcript chunk rows for the same exchange, still carrying exact source locators

Use:

- helps a reviewer jump straight to the most relevant question/answer span pair
- still keeps the transcript span as the inspection target

## Example 3: Find growth slowdown / competition discussion

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  "growth slowdown competition discussion" \
  --case-id netflix_q1_2022 \
  --mode hybrid \
  --top-k 6
```

Representative hits:

- `qa_pair_002_answer`: explicit Q1 miss explanation with churn / macro / acquisition context
- `qa_pair_001_answer`: lower acquisition, account sharing, and competition framing
- shareholder-letter paragraph rows that mirror the same slowdown / competition discussion

Use:

- links the transcript discussion with the management-authored document context
- keeps both results pinned to explicit bounded artifacts

## Example 4: Find semantically similar spans to a skeptical analyst question

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  --case-id netflix_q1_2022 \
  --mode hybrid \
  --top-k 5 \
  --like-row-id qa_pair_011_question
```

Representative hits:

- `qa_pair_009_answer`: another monetization / advertising-adjacent answer span
- `qa_pair_011_answer`: the direct management response to the seeded skeptical question
- nearby transcript chunks with the same underlying exchange

Use:

- reviewer can start from a known skeptical question row
- similarity search stays attached to exact row ids and source locators

## Interpretation Guidance

Use these results as:

- navigation aid
- inspection aid
- provenance-preserving follow-up layer

Do not use them as:

- proof that an interpretation is correct
- a substitute for transcript-backed review
- a confidence claim about what management “really meant”

Nearest-neighbor similarity is not adjudication. The transcript-backed artifact remains the review target.
