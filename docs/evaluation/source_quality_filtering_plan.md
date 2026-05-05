# Source Quality Filtering Plan

The current gold label set is useful because it turns the repo into a measurable evaluation loop, but it is not yet a clean single-provenance benchmark. The 57 canonical labels were recovered from existing human-reviewed signal labels and guidance-call labels that were conservatively mapped into the four-label Signal Engine taxonomy.

That mixed provenance should be visible in every future evaluation. Otherwise, a baseline score can look more stable than it really is, especially when fixture-like examples, guidance-specific labels, and directly reviewed conversational labels are evaluated together.

## Recommended Metadata Fields

- `label_source`: where the canonical label came from, such as `normalized_import`, `manual_review`, or `second_review`.
- `source_file`: original file path used for import or review.
- `import_method`: the importer or workflow that created the canonical row.
- `provenance_quality`: recommended values are `high`, `medium`, and `needs_review`.
- `requires_manual_review`: boolean flag for labels that should not be used in higher-confidence benchmark subsets until reviewed again.

## Recommended Evaluation Subsets

- `all_labels`: every valid canonical row in `data/gold/gold_labels.jsonl`.
- `human_reviewed_only`: labels whose source was directly human-reviewed in the Signal Engine taxonomy.
- `guidance_mapped_only`: guidance-change labels mapped into the four-label taxonomy for directional diagnostics.
- `fixture_excluded`: excludes rows whose notes or case IDs identify them as sample, seed, or fixture-derived examples.

## Future Command Shape

```bash
make eval-loop FILTER=human_reviewed_only
```

The first implementation can stay narrow: filter rows before metrics are computed, write the selected subset name into `reports/evaluation_readiness.json`, and preserve the full `all_labels` baseline as the default.

## Near-Term Recommendation

Keep the current 57-label baseline as the proof-state baseline, then add source-quality metadata in a small follow-up before making stronger claims from any single score. The next useful comparison is `all_labels` versus `human_reviewed_only`, because that will show how much guidance mapping and fixture-like examples affect precision and recall.
