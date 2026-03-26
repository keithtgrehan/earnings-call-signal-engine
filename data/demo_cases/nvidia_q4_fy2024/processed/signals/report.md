# Earnings Call Sentiment Report

## Summary
- Chunks scored: 78
- Sentiment mean: 0.620742
- Sentiment std: 0.74515

## Guidance
- Guidance rows: 40
- Mean guidance strength: 0.46626

| start | end | guidance_strength | text |
| --- | --- | --- | --- |
| 127.69 | 175.77 | 0.9477 | Thanks, Simona. Q4 was another record quarter. Revenue of $22.1 billion was up 22% sequentially and up to 265% year-o... |
| 958.84 | 1014.61 | 0.9423 | There were several automotive customer announcements this quarter, Li Auto, Great Wall Motor, ZEEKR, the premium EV s... |
| 696.54 | 755.77 | 0.9292 | We also made great progress with our software and services offerings, which reached an annualized revenue run rate of... |
| 175.77 | 222.69 | 0.9279 | At the same time, companies have started to build the next generation of modern data centers, what we refer to as AI ... |
| 860.38 | 909.23 | 0.9091 | Revenue of $463 million was up 11% sequentially and up 105% year on year. Fiscal year revenue of $1.55 billion was up... |

## Guidance Revisions (vs prior)
- Prior guidance: None
- Matched: 0
- Raised: 0
- Lowered: 0
- Reaffirmed: 0
- Unclear: 0
- Mixed: 0

_none_

## Tone & Behavioral Signals
- uncertainty: high
- reassurance: medium
- analyst skepticism: medium

### Uncertainty evidence
- [modal uncertainty] strength=1: As Moore's Law slows while computing demand continues to skyrocket, companies may accelerate every workload possible to drive future impr...
- [modal uncertainty] strength=1: But also, often we are procuring capacity that we may need.

### Management reassurance evidence
- [demand remains strong] strength=2: Demand is strong as H200 nearly doubles the inference performance of H100.

### Analyst skepticism evidence
- [help us understand why] strength=2: I wanted to talk about, a little bit about your software business and it's pleasing to hear that it's over a $1 billion but I was hoping ...

## Q&A Shift
- prepared remarks vs Q&A: weaker
- analyst skepticism: medium
- management answers vs prepared remarks uncertainty: more uncertain
- early vs late Q&A: weaker

### Q&A examples
- delta=-1.9093 | Q: Great. Thank you. I wanted to follow up on the 40% of revenues coming from inference. That's a bigger number than I e... | A: I'll go backwards. The estimate is probably understated. And -- but we estimated it. And let me tell you why. Wheneve...
- delta=+1.7796 | Q: Hi, guys. Thanks for taking my question. I wanted Colette -- I wanted to touch on your comment that you expected the ... | A: Yeah. The first thing is overall, our supply is improving, overall. Our supply chain is just doing an incredible job ...

## Outputs
- guidance.csv
- guidance_revision.csv
- uncertainty_signals.csv
- reassurance_signals.csv
- analyst_skepticism.csv
- behavioral_summary.json
- qa_shift_segments.csv
- qa_shift_summary.json
- metrics.json
- report.md
