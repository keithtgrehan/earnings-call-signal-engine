"""Text signal, sentiment, emotion, and weak-label engine."""

from .pipeline import score_text_segments
from .weak_supervision import weak_label_segment

__all__ = ["score_text_segments", "weak_label_segment"]
