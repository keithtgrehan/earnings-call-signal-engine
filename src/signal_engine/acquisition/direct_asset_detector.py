from __future__ import annotations

from typing import Callable
from urllib.request import Request, urlopen

from .asset_resolver import block_reason_for_url, infer_asset_type, make_candidate

TRANSCRIPT_MARKERS = (
    "operator:",
    "corporate participants",
    "conference call participants",
    "prepared remarks",
    "question-and-answer",
    "question and answer",
    "analyst:",
)


def default_binary_fetcher(url: str) -> tuple[int, str, bytes]:
    request = Request(
        url,
        headers={
            "User-Agent": "SignalEngine/2.0 direct asset detector (project assessment; contact: keithtgrehan)",
            "Accept": "text/html,text/plain,application/pdf,audio/*,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - guarded public HTTP fetch.
        return int(getattr(response, "status", 200)), response.headers.get("content-type", ""), response.read(2_000_000)


def transcript_marker_count(text: str) -> int:
    lower = text.lower()
    return sum(1 for marker in TRANSCRIPT_MARKERS if marker in lower)


def detect_direct_asset(row: dict[str, str], *, fetcher: Callable[[str], tuple[int, str, bytes]] = default_binary_fetcher) -> dict[str, str]:
    url = row.get("resolved_asset_url") or row.get("source_url") or ""
    block_reason = block_reason_for_url(url, row.get("source_type", ""))
    if block_reason:
        return make_candidate(
            row,
            asset_type="blocked",
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=0.0,
            confidence_reason="blocked URL class",
            rights_status="blocked",
            blocked_reason=block_reason,
            next_action="skip",
        )
    try:
        status_code, content_type, body = fetcher(url)
    except Exception as exc:  # pragma: no cover - live network defensive path.
        return make_candidate(
            row,
            asset_type="blocked",
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=0.0,
            confidence_reason=f"fetch failed: {type(exc).__name__}",
            rights_status="metadata_only",
            blocked_reason="fetch_failed",
            next_action="manual_review",
        )
    asset_type, reason, confidence = infer_asset_type(url, content_type=content_type)
    if asset_type.startswith("audio_"):
        return make_candidate(
            row,
            asset_type=asset_type,
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=max(confidence, 0.9),
            confidence_reason=reason,
            rights_status="user_authorized_public_direct",
            download_allowed=True,
            next_action="download",
            content_type_hint=content_type,
        )
    if status_code >= 400:
        return make_candidate(
            row,
            asset_type="blocked",
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=0.0,
            confidence_reason=f"HTTP {status_code}",
            rights_status="metadata_only",
            blocked_reason=f"http_{status_code}",
            next_action="manual_review",
            content_type_hint=content_type,
        )
    if "pdf" in content_type.lower() or url.lower().split("?")[0].endswith(".pdf"):
        return make_candidate(
            row,
            asset_type="transcript_pdf" if "transcript" in url.lower() else "slides_metadata",
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=0.8,
            confidence_reason="PDF direct asset",
            rights_status="user_authorized_public_direct" if "transcript" in url.lower() else "metadata_only",
            download_allowed="transcript" in url.lower(),
            next_action="download" if "transcript" in url.lower() else "metadata_review",
            content_type_hint=content_type,
        )
    text = body.decode("utf-8", errors="replace")
    markers = transcript_marker_count(text)
    if content_type.lower().startswith(("text/plain", "text/html")) and markers >= 2:
        transcript_type = "transcript_html" if "html" in content_type.lower() else "transcript_text"
        return make_candidate(
            row,
            asset_type=transcript_type,
            source_type=row.get("source_type", "direct_asset"),
            source_url=row.get("source_url", url),
            resolved_asset_url=url,
            confidence=0.82 + min(markers, 5) * 0.03,
            confidence_reason=f"transcript markers found: {markers}",
            rights_status="user_authorized_public_direct",
            download_allowed=True,
            next_action="download",
            content_type_hint=content_type,
        )
    return make_candidate(
        row,
        asset_type="blocked",
        source_type=row.get("source_type", "direct_asset"),
        source_url=row.get("source_url", url),
        resolved_asset_url=url,
        confidence=0.0,
        confidence_reason="content did not confirm transcript/audio asset",
        rights_status="metadata_only",
        blocked_reason="generic_landing_page_no_direct_asset",
        next_action="manual_review",
        content_type_hint=content_type,
    )
