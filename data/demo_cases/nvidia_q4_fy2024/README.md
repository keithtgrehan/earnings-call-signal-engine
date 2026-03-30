# NVIDIA Q4 FY24 Fixed Demo Case

This folder holds a fixed, transcript-first NVIDIA Q4 FY24 demo package.

Included raw inputs:
- correct-quarter earnings call transcript PDF when available locally
- official NVIDIA investor-relations press release snapshot
- local Q4 FY24 video asset for optional supporting audio hooks
- supporting-only retrieval bundle for lexical / semantic navigation over bounded case rows

Processing boundary:
- the transcript and official press release are the source of truth
- deterministic transcript-backed review artifacts are primary
- audio/video remain supporting layers only
- retrieval is a supporting-only navigation layer over bounded deterministic artifacts
- this is not a trading or predictive validation package

Key retrieval artifacts:

- `demo/retrieval/nvidia_retrieval_rows.jsonl`
- `demo/retrieval/nvidia_retrieval_manifest.json`
- `demo/retrieval/nvidia_retrieval_embeddings.npy`
- `demo/retrieval/README.md`

Rebuild from the saved raw assets:

```bash
PYTHONPATH=src python3 scripts/build_nvidia_demo_case.py
```
