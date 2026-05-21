from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class SourceDiscoveryRecord:
    source_id: str
    source_name: str
    source_url_or_path: str
    source_type: str
    acquisition_method: str
    metadata_only: bool = True
    retrieval_timestamp: str = ""
    blocked_reason: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProvenanceRecord:
    source_id: str
    source_name: str
    source_url_or_path: str
    source_type: str
    rights_tier: str
    license_or_terms_summary: str
    allowed_storage: str
    allowed_commit: bool
    commit_allowed: bool
    allowed_training_use: str
    training_allowed: str
    allowed_eval_use: str
    eval_allowed: str
    raw_body_allowed: bool
    metadata_only: bool
    acquisition_method: str
    robots_or_terms_checked: bool
    source_terms_checked: bool
    paywall_or_login_status: str
    robots_status: str
    provenance_hash: str
    last_checked_at: str
    retrieval_timestamp: str
    reviewer_or_operator: str
    blocked_reason: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlockedCase:
    source_id: str
    source_url_or_path: str
    blocked_reason: str
    metadata_only: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DataSourceAdapter:
    source_type = "unknown"
    default_rights_tier = "unknown"
    default_license_summary = "Terms not checked."

    def __init__(
        self,
        *,
        source_id: str,
        source_name: str,
        source_url_or_path: str,
        reviewer_or_operator: str = "unknown",
        raw_body_allowed: bool = False,
        terms_checked: bool = False,
        commit_allowed: bool = False,
        training_allowed: str = "no",
        eval_allowed: str = "benchmark_only",
        paywall_or_login_status: str = "unknown",
        robots_status: str = "unknown",
    ) -> None:
        self.source_id = source_id
        self.source_name = source_name
        self.source_url_or_path = source_url_or_path
        self.reviewer_or_operator = reviewer_or_operator
        self.raw_body_allowed = raw_body_allowed
        self.terms_checked = terms_checked
        self.commit_allowed = commit_allowed
        self.training_allowed = training_allowed
        self.eval_allowed = eval_allowed
        self.paywall_or_login_status = paywall_or_login_status
        self.robots_status = robots_status

    def discover(self) -> list[SourceDiscoveryRecord]:
        return [
            SourceDiscoveryRecord(
                source_id=self.source_id,
                source_name=self.source_name,
                source_url_or_path=self.source_url_or_path,
                source_type=self.source_type,
                acquisition_method="metadata_scaffold_no_download",
                retrieval_timestamp=datetime.now(UTC).isoformat(),
                blocked_reason="" if self.terms_checked else "Terms not checked; raw use blocked.",
                notes="Discovery scaffold only; no network call performed.",
            )
        ]

    def validate_terms(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "terms_checked": self.terms_checked,
            "source_terms_checked": self.terms_checked,
            "raw_body_allowed": self.raw_body_allowed and self.terms_checked,
            "license_or_terms_summary": self.default_license_summary,
            "paywall_or_login_status": self.paywall_or_login_status,
            "robots_status": self.robots_status,
        }

    def fetch_metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url_or_path": self.source_url_or_path,
            "source_type": self.source_type,
            "metadata_only": True,
            "network_access_performed": False,
            "retrieval_timestamp": datetime.now(UTC).isoformat(),
            "blocked_reason": "" if self.terms_checked else "Terms not checked; raw use blocked.",
        }

    def fetch_raw_if_allowed(self) -> dict[str, Any]:
        if not (self.raw_body_allowed and self.terms_checked):
            return self.emit_blocked_case("Raw body fetch blocked until rights status permits storage.")
        return {
            "source_id": self.source_id,
            "raw_body": None,
            "status": "not_downloaded",
            "notes": "Adapter scaffold permits raw fetch, but default implementation performs no live download.",
        }

    def classify_rights(self) -> str:
        if not self.terms_checked:
            return "unknown"
        return self.default_rights_tier

    def build_provenance_record(self) -> ProvenanceRecord:
        rights_tier = self.classify_rights()
        raw_allowed = self.raw_body_allowed and self.terms_checked
        allowed_storage = "raw_allowed_local_only" if raw_allowed else "metadata_only"
        blocked_reason = "" if raw_allowed or rights_tier != "unknown" else "Terms not checked; raw storage blocked."
        last_checked_at = datetime.now(UTC).date().isoformat()
        retrieval_timestamp = datetime.now(UTC).isoformat()
        base = {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "source_url_or_path": self.source_url_or_path,
            "source_type": self.source_type,
            "rights_tier": rights_tier,
            "license_or_terms_summary": self.default_license_summary,
            "last_checked_at": last_checked_at,
        }
        provenance_hash = "sha256:" + hashlib.sha256(json.dumps(base, sort_keys=True).encode("utf-8")).hexdigest()
        return ProvenanceRecord(
            source_id=self.source_id,
            source_name=self.source_name,
            source_url_or_path=self.source_url_or_path,
            source_type=self.source_type,
            rights_tier=rights_tier,
            license_or_terms_summary=self.default_license_summary,
            allowed_storage=allowed_storage,
            allowed_commit=self.commit_allowed,
            commit_allowed=self.commit_allowed,
            allowed_training_use=self.training_allowed if raw_allowed else "no",
            training_allowed=self.training_allowed if raw_allowed else "no",
            allowed_eval_use=self.eval_allowed,
            eval_allowed=self.eval_allowed,
            raw_body_allowed=raw_allowed,
            metadata_only=not raw_allowed,
            acquisition_method="metadata_scaffold_no_download",
            robots_or_terms_checked=self.terms_checked,
            source_terms_checked=self.terms_checked,
            paywall_or_login_status=self.paywall_or_login_status,
            robots_status=self.robots_status,
            provenance_hash=provenance_hash,
            last_checked_at=last_checked_at,
            retrieval_timestamp=retrieval_timestamp,
            reviewer_or_operator=self.reviewer_or_operator,
            blocked_reason=blocked_reason,
            notes="No live download performed by default.",
        )

    def emit_blocked_case(self, reason: str) -> dict[str, Any]:
        return BlockedCase(
            source_id=self.source_id,
            source_url_or_path=self.source_url_or_path,
            blocked_reason=reason,
        ).to_dict()
