# NVIDIA Q4 FY24 Fixed Demo Case

This folder holds a fixed, transcript-first NVIDIA Q4 FY24 demo package.

Included raw inputs:
- correct-quarter earnings call transcript snapshot
- official NVIDIA investor-relations press release snapshot
- local Q4 FY24 video asset for optional supporting audio hooks

Processing boundary:
- the transcript and official press release are the source of truth
- deterministic transcript-backed review artifacts are primary
- audio/video remain supporting layers only
- this is not a trading or predictive validation package

Rebuild from the saved raw assets:

```bash
PYTHONPATH=src python3 scripts/build_nvidia_demo_case.py
```
