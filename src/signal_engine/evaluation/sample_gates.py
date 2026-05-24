from __future__ import annotations


def evaluate_sample_gates(*, valid_gold_count: int, call_count: int) -> dict[str, dict[str, object]]:
    return {
        "pilot_30_call": {
            "status": "PIPELINE_READY_ONLY" if call_count >= 30 else "NOT_ENOUGH_DATA",
            "required_calls": 30,
            "call_count": call_count,
        },
        "signal_eval": {
            "status": "READY" if valid_gold_count >= 100 else "NOT_ENOUGH_DATA",
            "required_valid_gold": 100,
            "valid_gold_count": valid_gold_count,
        },
        "retrieval_benchmark": {
            "status": "READY" if 100 <= call_count <= 150 and valid_gold_count >= 100 else "NOT_ENOUGH_DATA",
            "required_calls": "100-150",
            "call_count": call_count,
        },
        "metadata_500_universe": {
            "status": "METADATA_READY_MAP_ONLY" if call_count >= 500 else "NOT_ENOUGH_DATA",
            "required_calls": 500,
            "call_count": call_count,
        },
    }
