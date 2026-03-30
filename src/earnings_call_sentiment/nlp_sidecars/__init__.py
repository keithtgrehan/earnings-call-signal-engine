"""Optional NLP sidecar evaluation pack.

This package is additive only:
- transcript-backed deterministic outputs remain canonical
- sidecar models write separate artifacts
- no benchmark or predictive claims are implied by these helpers
"""

from .base import SUPPORTED_UNIT_TYPES, TextUnit
from .config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MODELS,
    DEFAULT_ZERO_SHOT_LABEL_CONFIG,
    resolve_cache_dir,
)
from .evaluate import write_case_evaluation_summary
from .io import build_artifact_inputs, load_text_units, write_model_outputs
from .models import AVAILABLE_MODEL_NAMES, build_model
from .runner import run_sidecar_models

__all__ = [
    "AVAILABLE_MODEL_NAMES",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_MAX_LENGTH",
    "DEFAULT_MODELS",
    "DEFAULT_ZERO_SHOT_LABEL_CONFIG",
    "SUPPORTED_UNIT_TYPES",
    "TextUnit",
    "build_artifact_inputs",
    "build_model",
    "load_text_units",
    "resolve_cache_dir",
    "run_sidecar_models",
    "write_case_evaluation_summary",
    "write_model_outputs",
]
