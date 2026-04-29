from __future__ import annotations

from dataclasses import dataclass

from .domains import get_domain_profile
from .schemas import ConversationRecord, TranscriptSegment
from .text_features import safe_ratio, token_count_by_segments


@dataclass(frozen=True)
class ResponsePair:
    prompt: TranscriptSegment
    response: TranscriptSegment | None


def segments_for_group(record: ConversationRecord, group: str) -> list[TranscriptSegment]:
    profile = get_domain_profile(record.domain)
    roles = profile.role_groups.get(group, frozenset())
    return [segment for segment in record.transcript_segments if segment.role in roles]


def build_response_pairs(record: ConversationRecord) -> list[ResponsePair]:
    profile = get_domain_profile(record.domain)
    prompt_roles = profile.role_groups.get(profile.prompt_group, frozenset())
    response_roles = profile.role_groups.get(profile.response_group, frozenset())

    pairs: list[ResponsePair] = []
    pending_prompt: TranscriptSegment | None = None
    for segment in record.transcript_segments:
        if segment.role in prompt_roles:
            if pending_prompt is not None:
                pairs.append(ResponsePair(prompt=pending_prompt, response=None))
            pending_prompt = segment
            continue
        if pending_prompt is not None and segment.role in response_roles:
            pairs.append(ResponsePair(prompt=pending_prompt, response=segment))
            pending_prompt = None
    if pending_prompt is not None:
        pairs.append(ResponsePair(prompt=pending_prompt, response=None))
    return pairs


def unanswered_prompt_count(record: ConversationRecord) -> int:
    return sum(1 for pair in build_response_pairs(record) if pair.response is None)


def token_share(record: ConversationRecord, group: str) -> float:
    group_segments = segments_for_group(record, group)
    group_tokens = token_count_by_segments(group_segments)
    total_tokens = token_count_by_segments(record.transcript_segments)
    return round(safe_ratio(group_tokens, total_tokens), 4)


def internal_token_share(record: ConversationRecord) -> float:
    profile = get_domain_profile(record.domain)
    return token_share(record, profile.response_group)
