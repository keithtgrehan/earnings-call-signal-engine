# Netflix Retrieval Demo

## Boundary First

This demo adds a supporting-only retrieval layer over the existing Netflix case pack.

What remains canonical:

- transcript-backed chunks
- deterministic guidance / QA / shareholder-letter artifacts
- explicit source locators and spans

What retrieval adds:

- faster navigation to bounded evidence rows
- hybrid retrieval as the recommended reviewer mode
- lexical and semantic follow-up search without dropping provenance
- row-to-row similarity without dropping provenance

What retrieval does **not** do:

- it does not adjudicate truth
- it does not replace transcript review
- it does not make predictive or statistical claims

## Reviewer Mode

Use `--mode hybrid` for reviewer workflows.

- semantic alone can be noisy
- lexical alone can be too literal
- hybrid is the best bounded default for navigation and inspection

If embeddings are unavailable, lexical still works as the fallback. Either way, the transcript-backed artifact remains the canonical review target.

## Example 1: Find guidance pressure moments

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  --query "guidance pressure moments" \
  --case netflix_q1_2022 \
  --mode hybrid \
  --top-k 5
```

Representative hits:

- `guidance_span_001`: Q1 miss versus the prior 2.5M paid-net-add guide
- `guidance_span_042`: tactical clarification around churn and Q1 performance
- `guidance_span_008`: slower revenue growth and the need to manage through it
- `guidance_span_006`: competition, penetration, and lower acquisition pressure

Use:

- surfaces pressure-oriented guidance rows quickly
- keeps the reviewer on transcript-backed spans rather than vague summaries
- avoids low-information guidance joke/meta rows in the top hits

## Example 2: Find ad-supported strategy moments

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  --query "ad supported option" \
  --case netflix_q1_2022 \
  --mode hybrid \
  --top-k 5
```

Representative hits:

- `qa_pair_012_answer`: management answer that Netflix expects a lower-price ad-tolerant plan layer to work
- `qa_pair_011_answer`: management answer describing ads as a gradual, not short-term, path
- `qa_pair_011_question`: analyst question on a lower-priced ad-supported tier

Use:

- helps a reviewer jump straight to the most relevant question/answer span pair
- keeps structured Q&A rows ahead of weaker duplicate chunk matches when scores are close

## Example 3: Find growth slowdown / competition discussion

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  --query "growth slowdown competition discussion" \
  --case netflix_q1_2022 \
  --mode hybrid \
  --top-k 5
```

Representative hits:

- `shareholder_letter_paragraph_002`: direct shareholder-letter framing of competitive and macro headwinds
- `qa_pair_001_answer`: lower acquisition, account sharing, and competition framing
- `qa_pair_002_answer`: Q1 miss explanation with churn, macro strain, and softer seasonality
- `shareholder_letter_paragraph_001`: slowed growth and monetization framing from the letter

Use:

- links the transcript discussion with the management-authored document context
- keeps both results pinned to explicit bounded artifacts
- prefers richer structured rows over broad guidance-only matches when reviewer intent is about slowdown and competition

## Example 4: Find semantically similar spans to a skeptical analyst question

Command:

```bash
PYTHONPATH=src python3 scripts/search_case_retrieval.py \
  --case netflix_q1_2022 \
  --mode hybrid \
  --top-k 5 \
  --like-row-id qa_pair_001_question
```

Representative hits:

- `qa_pair_001_answer`: the direct management response to the seeded skeptical question
- `qa_pair_002_answer`: another management answer on miss drivers, churn, and macro pressure
- `shareholder_letter_paragraph_002`: document-backed headwinds framing that echoes the same concerns

Use:

- reviewer can start from a known skeptical question row
- similarity search stays attached to exact row ids and source locators
- the returned rows still need transcript-backed inspection; nearest neighbors are not adjudication

## Interpretation Guidance

Use these results as:

- navigation aid
- inspection aid
- provenance-preserving follow-up layer

Do not use them as:

- proof that an interpretation is correct
- a substitute for transcript-backed review
- a confidence claim about what management “really meant”

Nearest-neighbor similarity is not adjudication. Semantic-only retrieval can be noisy, and lexical-only retrieval can be too literal. Hybrid is the recommended reviewer mode, but the transcript-backed artifact remains the review target.
