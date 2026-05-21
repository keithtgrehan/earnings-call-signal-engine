"""Metadata-first data source scaffolds for Signal Engine corpus readiness."""

from .base import BlockedCase, DataSourceAdapter, ProvenanceRecord, SourceDiscoveryRecord
from .company_ir import CompanyIRAdapter
from .licensed_vendor import LicensedVendorAdapter
from .macro_fred import MacroFredAdapter
from .manual_local import ManualLocalAdapter
from .sec_edgar import SecEdgarAdapter
from .youtube_metadata import YouTubeMetadataAdapter

__all__ = [
    "BlockedCase",
    "CompanyIRAdapter",
    "DataSourceAdapter",
    "LicensedVendorAdapter",
    "MacroFredAdapter",
    "ManualLocalAdapter",
    "ProvenanceRecord",
    "SecEdgarAdapter",
    "SourceDiscoveryRecord",
    "YouTubeMetadataAdapter",
]
