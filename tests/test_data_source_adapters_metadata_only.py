from __future__ import annotations

from signal_engine.data_sources import (
    CompanyIRAdapter,
    LicensedVendorAdapter,
    MacroFredAdapter,
    ManualLocalAdapter,
    SecEdgarAdapter,
    YouTubeMetadataAdapter,
)


def test_data_source_adapters_default_to_metadata_only() -> None:
    adapters = [
        SecEdgarAdapter(source_id="sec", source_name="SEC", source_url_or_path="https://data.sec.gov/", terms_checked=True),
        CompanyIRAdapter(source_id="ir", source_name="IR", source_url_or_path="https://investor.example.com"),
        MacroFredAdapter(source_id="fred", source_name="FRED", source_url_or_path="https://fred.stlouisfed.org/series/UNRATE"),
        ManualLocalAdapter(source_id="manual", source_name="Manual", source_url_or_path="/tmp/transcript.txt"),
        YouTubeMetadataAdapter(source_id="yt", source_name="YouTube", source_url_or_path="https://www.youtube.com/watch?v=test"),
        LicensedVendorAdapter(source_id="vendor", source_name="Vendor", source_url_or_path="vendor://call"),
    ]

    for adapter in adapters:
        metadata = adapter.fetch_metadata()
        blocked = adapter.fetch_raw_if_allowed()
        provenance = adapter.build_provenance_record().to_dict()
        assert metadata["metadata_only"] is True
        assert metadata["network_access_performed"] is False
        assert blocked["metadata_only"] is True
        assert "blocked" in blocked["blocked_reason"].lower()
        assert provenance["raw_body_allowed"] is False


def test_sec_adapter_records_public_domain_fair_access_note() -> None:
    adapter = SecEdgarAdapter(source_id="sec", source_name="SEC", source_url_or_path="https://data.sec.gov/", terms_checked=True)
    provenance = adapter.build_provenance_record().to_dict()
    assert provenance["rights_tier"] == "public_domain"
    assert "fair-access" in provenance["license_or_terms_summary"]


def test_youtube_raw_download_blocked_by_default() -> None:
    adapter = YouTubeMetadataAdapter(source_id="yt", source_name="YouTube", source_url_or_path="https://www.youtube.com/watch?v=test")
    blocked = adapter.fetch_raw_if_allowed()
    assert "blocked" in blocked["blocked_reason"].lower()
    assert adapter.fetch_metadata()["raw_audio_default"] == "blocked"


def test_licensed_vendor_raw_ingest_blocked_without_license_config() -> None:
    adapter = LicensedVendorAdapter(source_id="vendor", source_name="Vendor", source_url_or_path="vendor://call")
    blocked = adapter.fetch_raw_if_allowed()
    assert "license config" in blocked["blocked_reason"]
