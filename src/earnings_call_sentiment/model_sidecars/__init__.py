"""Optional model-sidecar benchmark helpers.

These utilities are additive only. They do not replace the repo's existing
deterministic transcript-first outputs.
"""

from .config import load_zero_shot_label_groups
from .runner import run_model_sidecars

__all__ = [
    "load_zero_shot_label_groups",
    "run_model_sidecars",
]
