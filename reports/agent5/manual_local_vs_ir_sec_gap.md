# Manual-Local vs IR/SEC Discovery Gap

## What Method 1 / Manual-Local Gives

- actual transcript body already in local control
- sha256 hash provenance
- explicit operator-supplied path
- easier repeatable parsing
- no live source volatility
- no robots/source-term ambiguity at runtime
- no reliance on candidate URLs
- human-confirmed event identity
- direct linkage to reviewed labels

## What IR/SEC Discovery Adds

- source candidates at scale
- event identity metadata
- 8-K/press release/filing context
- official IR availability indicators
- asset availability map
- blocked/manual-action queue
- 500-call universe status

## Practical Conclusion

Official IR and SEC/EDGAR metadata discovery is useful for coverage planning and provenance triage. It cannot guarantee transcript bodies, transcript quality, or reuse permission. When source terms are unclear, manual-local registration remains the fastest fully controlled path because files are represented by operator path plus sha256 hash only.
