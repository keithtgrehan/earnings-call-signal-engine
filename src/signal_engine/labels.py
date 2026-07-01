from __future__ import annotations

from enum import Enum


class LabelState(str, Enum):
    WEAK_CANDIDATE = "weak_candidate"
    REVIEW_PACKET_CANDIDATE = "review_packet_candidate"
    ACCEPTED_GOLD = "accepted_gold"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


ACCEPTED_GOLD_STATES = {LabelState.ACCEPTED_GOLD.value}
LEGACY_GOLD_MARKERS = {"legacy_migrated", "explicit_legacy_gold"}


def valid_label_states() -> set[str]:
    return {state.value for state in LabelState}
