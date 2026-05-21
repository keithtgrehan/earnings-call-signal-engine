from __future__ import annotations

from .base import DataSourceAdapter


class YouTubeMetadataAdapter(DataSourceAdapter):
    source_type = "youtube_metadata"
    default_rights_tier = "publicly_available"
    default_license_summary = (
        "YouTube/webcast metadata reference only; raw audio/video download is blocked unless explicit authorization is configured."
    )

    def fetch_metadata(self) -> dict[str, object]:
        payload = super().fetch_metadata()
        payload["raw_audio_default"] = "blocked"
        payload["raw_video_default"] = "blocked"
        payload["platform_terms_apply"] = True
        return payload

    def fetch_raw_if_allowed(self) -> dict[str, object]:
        return self.emit_blocked_case("YouTube raw audio/video download is blocked by default.")
