# Retrieval Provider Enablement Playbook

Status: scaffold-only provider enablement guidance. Do not commit real provider configs, provider outputs, embeddings, vector stores, or provider response payloads.

## Safe Enablement Steps

1. Copy `configs/retrieval_providers.example.yml` to an untracked local path outside the repo or under a gitignored local workspace.
2. Enable one provider slot at a time.
3. Set only the required environment variable for that provider, such as `OPENAI_API_KEY`, `VOYAGE_API_KEY`, `COHERE_API_KEY`, or `JINA_API_KEY`.
4. Use an output root outside committed repo paths, for example `/tmp/signal-engine-retrieval-bakeoffs/<bakeoff_id>/`.
5. Run manifest validation before any provider execution is considered.
6. Run one provider, inspect metadata-only outputs, then clean local artifacts before preparing a commit.

## Required Gates Before Real Provider Runs

- reviewed retrieval eval query set with concrete evidence IDs
- no placeholder evidence IDs
- reviewer approval recorded outside committed scaffold examples
- non-committed provider config
- safe output root outside committed repo paths
- no raw transcript, ASR/audio, chunk, provider response, label, adjudication, training, or promotion payloads
- artifact scans before commit

## Cleanup

Use a local-only output root so cleanup is explicit and isolated:

```bash
rm -rf /tmp/signal-engine-retrieval-bakeoffs/<bakeoff_id>
```

Then rerun:

```bash
scripts/check_restricted_artifacts.py --dry-run
tools/check_no_transcript_text_staged.py
```

## Comparison Boundary

Provider comparisons must be made one provider at a time against the same reviewed query set and retrieval object metadata. Do not rank providers, report performance, or interpret metric changes until the bakeoff manifest, reviewed query gate, artifact gate, provenance gate, citation gate, and abstention gate all pass.
