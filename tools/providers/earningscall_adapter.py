from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .base import DESKTOP_WORKSPACE, ProviderAdapter, is_desktop_only_path, load_license_config, validate_raw_pull


USER_AGENT = "SignalEngineEarningsCallProvider/1.0 (metadata-safe; contact: project owner)"


class EarningsCallAdapter(ProviderAdapter):
    provider_id = "earningscall"

    def _sdk_available(self) -> bool:
        return importlib.util.find_spec("earningscall") is not None

    def _api_key(self) -> str:
        return os.environ.get(self.config.api_key_env, "") if self.config.api_key_env else ""

    def _license(self) -> dict[str, Any]:
        return load_license_config(self.config.license_config_ref)

    def provider_status(self) -> dict[str, Any]:
        base = super().provider_status()
        sdk_available = self._sdk_available()
        license_config = self._license()
        if base["status"] == "NOT_CONFIGURED":
            status = "NOT_CONFIGURED"
        elif self.config.raw_download_allowed and not self.config.license_config_ref:
            status = "LICENSE_MISSING"
        elif self.config.raw_download_allowed:
            status = "RAW_ALLOWED" if license_config else "LICENSE_MISSING"
        elif self.config.metadata_discovery_allowed:
            status = "METADATA_ONLY"
        else:
            status = "BLOCKED"
        return {
            **base,
            "status": status,
            "sdk_status": "available" if sdk_available else "sdk_missing",
            "rest_fallback_configured": bool(license_config.get("metadata_url_template") or license_config.get("transcript_url_template") or license_config.get("audio_url_template")),
            "raw_storage_root": self.config.raw_storage_root,
            "raw_storage_desktop_only": bool(self.config.raw_storage_root and is_desktop_only_path(Path(self.config.raw_storage_root), DESKTOP_WORKSPACE)),
        }

    def list_events(self, ticker: str, start_year: int, end_year: int) -> list[dict[str, Any]]:
        status = self.provider_status()
        if status["status"] == "NOT_CONFIGURED":
            return [{"ticker": ticker, "status": "NOT_CONFIGURED", "event_id": "", "notes": "Missing EARNINGSCALL_API_KEY"}]
        if status["sdk_status"] == "sdk_missing" and not status["rest_fallback_configured"]:
            return [{"ticker": ticker, "status": "SDK_MISSING", "event_id": "", "notes": "Install optional earningscall SDK or configure REST endpoint templates in reviewed license config."}]
        return [{"ticker": ticker, "status": "METADATA_ONLY", "event_id": "", "notes": "Live provider event resolution is gated by adapter-specific SDK/REST configuration."}]

    def resolve_event(self, ticker: str, fiscal_period: str) -> dict[str, Any]:
        events = self.list_events(ticker, 2021, 2030)
        if events and events[0].get("status") in {"NOT_CONFIGURED", "SDK_MISSING"}:
            return {**events[0], "fiscal_period": fiscal_period}
        return {"ticker": ticker, "fiscal_period": fiscal_period, "event_id": "", "status": "NO_EVENT_FOUND", "notes": "No configured live EarningsCall event resolver."}

    def _metadata(self, case: dict[str, str], asset_type: str) -> dict[str, Any]:
        status = self.provider_status()
        fiscal_period = f"{case.get('fiscal_year', '')} {case.get('fiscal_quarter', '')}".strip()
        if status["status"] == "NOT_CONFIGURED":
            asset_status = "NOT_CONFIGURED"
            notes = "Missing EARNINGSCALL_API_KEY; no provider API call attempted."
        elif status["sdk_status"] == "sdk_missing" and not status["rest_fallback_configured"]:
            asset_status = "SDK_MISSING"
            notes = "Optional earningscall SDK missing and no reviewed REST endpoint template configured."
        elif asset_type == "audio" and not self.config.supports_audio:
            asset_status = "NO_AUDIO_FOUND"
            notes = "Provider registry does not mark audio support for this provider."
        else:
            asset_status = "METADATA_ONLY" if not self.can_download(asset_type) else "RAW_ALLOWED"
            notes = "Provider metadata candidate only; raw pull requires license and Desktop-only guardrails."
        return {
            "provider": self.provider_id,
            "case_id": case.get("case_id", ""),
            "ticker": case.get("ticker", ""),
            "fiscal_year": case.get("fiscal_year", ""),
            "fiscal_quarter": case.get("fiscal_quarter", ""),
            "fiscal_period": fiscal_period,
            "asset_type": asset_type,
            "asset_id": "",
            "metadata_status": asset_status,
            "download_status": "BLOCKED" if asset_status in {"NOT_CONFIGURED", "SDK_MISSING"} else asset_status,
            "raw_download_allowed": self.can_download(asset_type),
            "license_config_ref": self.config.license_config_ref,
            "training_allowed": self.config.training_allowed,
            "provider_url": "",
            "raw_storage_root": self.config.raw_storage_root,
            "notes": notes,
        }

    def get_transcript_metadata(self, event_id: str = "", **case: str) -> dict[str, Any]:
        return self._metadata(case, "transcript")

    def get_audio_metadata(self, event_id: str = "", **case: str) -> dict[str, Any]:
        return self._metadata(case, "audio")

    def discover_metadata(self, case: dict[str, str]) -> dict[str, Any]:
        transcript = self.get_transcript_metadata(**case)
        audio = self.get_audio_metadata(**case)
        status = transcript.get("metadata_status") if transcript.get("metadata_status") != "RAW_ALLOWED" else "METADATA_ONLY"
        return {
            "provider": self.provider_id,
            "case_id": case.get("case_id", ""),
            "ticker": case.get("ticker", ""),
            "asset_type": "transcript_or_audio_metadata",
            "status": status,
            "raw_download_allowed": self.config.raw_download_allowed,
            "license_config_ref": self.config.license_config_ref,
            "training_allowed": self.config.training_allowed,
            "transcript_status": transcript.get("metadata_status", ""),
            "audio_status": audio.get("metadata_status", ""),
        }

    def can_download(self, asset_type: str) -> bool:
        if not self.config.raw_allowed_for_asset(asset_type):
            return False
        target = Path(self.config.raw_storage_root or DESKTOP_WORKSPACE / "provider_raw" / "earningscall") / "_probe"
        return validate_raw_pull(self.config, target, asset_type=asset_type) == []

    def _download_url(self, url: str, target: Path) -> tuple[str, int]:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {self._api_key()}"})
        with urlopen(request, timeout=90) as response:
            payload = response.read()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        return str(target), len(payload)

    def download_transcript_if_allowed(self, case: dict[str, str], *, url: str = "", output_path: Path | None = None) -> dict[str, Any]:
        target = output_path or Path(self.config.raw_storage_root or "") / case.get("case_id", "unknown") / "transcript.txt"
        errors = validate_raw_pull(self.config, target, asset_type="transcript")
        if errors:
            return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "transcript", "status": "BLOCKED", "errors": errors, "raw_written": False}
        if not url:
            return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "transcript", "status": "NO_TRANSCRIPT_FOUND", "errors": ["provider_transcript_url_missing"], "raw_written": False}
        path, byte_count = self._download_url(url, target)
        return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "transcript", "status": "DOWNLOADED_DESKTOP_ONLY", "local_path": path, "bytes": byte_count, "raw_written": True}

    def download_audio_if_allowed(self, case: dict[str, str], *, url: str = "", output_path: Path | None = None) -> dict[str, Any]:
        target = output_path or Path(self.config.raw_storage_root or "") / case.get("case_id", "unknown") / "audio.mp3"
        errors = validate_raw_pull(self.config, target, asset_type="audio")
        if errors:
            return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "audio", "status": "BLOCKED", "errors": errors, "raw_written": False}
        if not url:
            return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "audio", "status": "NO_AUDIO_FOUND", "errors": ["provider_audio_url_missing"], "raw_written": False}
        path, byte_count = self._download_url(url, target)
        return {"provider": self.provider_id, "case_id": case.get("case_id", ""), "asset_type": "audio", "status": "DOWNLOADED_DESKTOP_ONLY", "local_path": path, "bytes": byte_count, "raw_written": True}

    def write_manifest_rows(self, rows: list[dict[str, Any]], out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""), encoding="utf-8")
