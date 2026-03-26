from __future__ import annotations

import json
from pathlib import Path

from earnings_call_sentiment.model_sidecars.io import write_embedding_outputs
from earnings_call_sentiment.model_sidecars.models.base import EmbeddingOutput, TextUnit


def test_write_embedding_outputs_preserves_vector_shape(tmp_path: Path) -> None:
    output_root = tmp_path / "outputs" / "synthetic_case" / "model_sidecars"
    rows = {
        "chunks": [
            EmbeddingOutput(
                unit=TextUnit(
                    case_id="synthetic_case",
                    unit_type="chunks",
                    source_id="chunk-1",
                    text="Demand remains stable.",
                ),
                vector=[0.1, 0.2, 0.3],
            )
        ]
    }

    artifacts = write_embedding_outputs(
        case_id="synthetic_case",
        model_name="mpnet_embeddings",
        model_id="sentence-transformers/all-mpnet-base-v2",
        output_root=output_root,
        outputs_by_unit=rows,
        similarity_by_unit={},
        runtime_s=0.5,
    )

    line = (artifacts["chunks"]).read_text(encoding="utf-8").strip().splitlines()[0]
    payload = json.loads(line)
    assert payload["vector_dimension"] == 3
    assert len(payload["embedding"]) == 3
