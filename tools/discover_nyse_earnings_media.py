#!/usr/bin/env python3
"""Build a rights-aware NYSE earnings-call media candidate workspace.

The default mode is metadata-only source indexing. It creates local folders,
metadata manifests, provenance records, and repository reports, but it does not
download transcript bodies, audio, video, slides, webcast files, or vendor
content.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("/Users/keith/Desktop/earnings calls 100 samples")
DEFAULT_TARGETS = ROOT / "data" / "acquisition" / "nyse_100_media_targets.csv"
DEFAULT_MANIFEST = ROOT / "data" / "acquisition" / "nyse_100_media_manifest.csv"
DEFAULT_SOURCE_REGISTRY = ROOT / "data" / "acquisition" / "nyse_100_media_source_registry.csv"
DEFAULT_REPORTS_DIR = ROOT / "reports"

DISCOVERY_METHOD = "rights_aware_metadata_discovery"

AVAILABILITY_VALUES = {"available", "unavailable", "blocked", "paywalled", "unknown"}
RIGHTS_STATUS_VALUES = {"safe_to_link", "safe_to_download", "metadata_only", "blocked", "unknown"}
SOURCE_TYPE_VALUES = {
    "company_ir",
    "sec_edgar",
    "webcast_provider",
    "earnings_platform",
    "youtube_metadata_only",
    "investor_platform",
    "other",
}

MANIFEST_FIELDS = [
    "case_id",
    "ticker_symbol",
    "company_name",
    "exchange",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "earnings_call_date",
    "transcript_source_url",
    "audio_source_url",
    "video_source_url",
    "transcript_availability",
    "audio_availability",
    "video_availability",
    "source_type",
    "rights_status",
    "priority_tier",
    "local_paths_created",
    "notes",
    "source_domain",
    "discovered_timestamp",
    "acquisition_method",
    "provenance_hash",
    "call_folder",
]

TARGET_FIELDS = [
    "ticker_symbol",
    "company_name",
    "exchange",
    "sector",
    "exchange_verified",
    "exchange_verification_source",
    "official_ir_url",
    "source_domain",
    "included",
    "exclusion_reason",
]

SOURCE_REGISTRY_FIELDS = [
    "registry_id",
    "case_id",
    "ticker_symbol",
    "company_name",
    "fiscal_year",
    "fiscal_quarter",
    "source_type",
    "source_url",
    "source_domain",
    "availability",
    "rights_status",
    "raw_download_allowed",
    "blocked_reason",
    "manual_action",
    "acquisition_method",
    "discovered_timestamp",
    "provenance_hash",
    "notes",
]


SEED_COMPANIES: list[dict[str, str]] = [
    {
        "ticker_symbol": "JPM",
        "company_name": "JPMorgan Chase & Co.",
        "exchange": "NYSE",
        "sector": "banking",
        "official_ir_url": "https://www.jpmorganchase.com/ir",
    },
    {
        "ticker_symbol": "WMT",
        "company_name": "Walmart Inc.",
        "exchange": "NYSE",
        "sector": "retail",
        "official_ir_url": "https://stock.walmart.com/",
    },
    {
        "ticker_symbol": "HD",
        "company_name": "The Home Depot, Inc.",
        "exchange": "NYSE",
        "sector": "retail",
        "official_ir_url": "https://ir.homedepot.com/",
    },
    {
        "ticker_symbol": "JNJ",
        "company_name": "Johnson & Johnson",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://www.investor.jnj.com/",
    },
    {
        "ticker_symbol": "XOM",
        "company_name": "Exxon Mobil Corporation",
        "exchange": "NYSE",
        "sector": "energy",
        "official_ir_url": "https://corporate.exxonmobil.com/investors",
    },
    {
        "ticker_symbol": "BAC",
        "company_name": "Bank of America Corporation",
        "exchange": "NYSE",
        "sector": "banking",
        "official_ir_url": "https://investor.bankofamerica.com/",
    },
    {
        "ticker_symbol": "GS",
        "company_name": "The Goldman Sachs Group, Inc.",
        "exchange": "NYSE",
        "sector": "banking",
        "official_ir_url": "https://www.goldmansachs.com/investor-relations/",
    },
    {
        "ticker_symbol": "MS",
        "company_name": "Morgan Stanley",
        "exchange": "NYSE",
        "sector": "banking",
        "official_ir_url": "https://www.morganstanley.com/about-us-ir",
    },
    {
        "ticker_symbol": "BLK",
        "company_name": "BlackRock, Inc.",
        "exchange": "NYSE",
        "sector": "payments_financial_services",
        "official_ir_url": "https://ir.blackrock.com/",
    },
    {
        "ticker_symbol": "AXP",
        "company_name": "American Express Company",
        "exchange": "NYSE",
        "sector": "payments",
        "official_ir_url": "https://ir.americanexpress.com/",
    },
    {
        "ticker_symbol": "IBM",
        "company_name": "International Business Machines Corporation",
        "exchange": "NYSE",
        "sector": "industrials_technology",
        "official_ir_url": "https://www.ibm.com/investor",
    },
    {
        "ticker_symbol": "LLY",
        "company_name": "Eli Lilly and Company",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investor.lilly.com/",
    },
    {
        "ticker_symbol": "MRK",
        "company_name": "Merck & Co., Inc.",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://www.merck.com/investor-relations/",
    },
    {
        "ticker_symbol": "PFE",
        "company_name": "Pfizer Inc.",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investors.pfizer.com/",
    },
    {
        "ticker_symbol": "UNH",
        "company_name": "UnitedHealth Group Incorporated",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://www.unitedhealthgroup.com/investors.html",
    },
    {
        "ticker_symbol": "CVS",
        "company_name": "CVS Health Corporation",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investors.cvshealth.com/",
    },
    {
        "ticker_symbol": "BA",
        "company_name": "The Boeing Company",
        "exchange": "NYSE",
        "sector": "aerospace",
        "official_ir_url": "https://investors.boeing.com/",
    },
    {
        "ticker_symbol": "CAT",
        "company_name": "Caterpillar Inc.",
        "exchange": "NYSE",
        "sector": "industrials",
        "official_ir_url": "https://investors.caterpillar.com/",
    },
    {
        "ticker_symbol": "DE",
        "company_name": "Deere & Company",
        "exchange": "NYSE",
        "sector": "industrials",
        "official_ir_url": "https://investor.deere.com/",
    },
    {
        "ticker_symbol": "GE",
        "company_name": "GE Aerospace",
        "exchange": "NYSE",
        "sector": "aerospace",
        "official_ir_url": "https://www.geaerospace.com/investors",
    },
    {
        "ticker_symbol": "HON",
        "company_name": "Honeywell International Inc.",
        "exchange": "NASDAQ",
        "sector": "industrials",
        "official_ir_url": "https://investor.honeywell.com/",
    },
    {
        "ticker_symbol": "KO",
        "company_name": "The Coca-Cola Company",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://investors.coca-colacompany.com/",
    },
    {
        "ticker_symbol": "MCD",
        "company_name": "McDonald's Corporation",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://corporate.mcdonalds.com/corpmcd/investors.html",
    },
    {
        "ticker_symbol": "NKE",
        "company_name": "NIKE, Inc.",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://investors.nike.com/",
    },
    {
        "ticker_symbol": "DIS",
        "company_name": "The Walt Disney Company",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://thewaltdisneycompany.com/investor-relations/",
    },
    {
        "ticker_symbol": "T",
        "company_name": "AT&T Inc.",
        "exchange": "NYSE",
        "sector": "telecom",
        "official_ir_url": "https://investors.att.com/",
    },
    {
        "ticker_symbol": "LOW",
        "company_name": "Lowe's Companies, Inc.",
        "exchange": "NYSE",
        "sector": "retail",
        "official_ir_url": "https://corporate.lowes.com/investors",
    },
    {
        "ticker_symbol": "UPS",
        "company_name": "United Parcel Service, Inc.",
        "exchange": "NYSE",
        "sector": "industrials",
        "official_ir_url": "https://investors.ups.com/",
    },
    {
        "ticker_symbol": "RTX",
        "company_name": "RTX Corporation",
        "exchange": "NYSE",
        "sector": "aerospace",
        "official_ir_url": "https://investors.rtx.com/",
    },
    {
        "ticker_symbol": "LMT",
        "company_name": "Lockheed Martin Corporation",
        "exchange": "NYSE",
        "sector": "aerospace",
        "official_ir_url": "https://investors.lockheedmartin.com/",
    },
    {
        "ticker_symbol": "NOC",
        "company_name": "Northrop Grumman Corporation",
        "exchange": "NYSE",
        "sector": "aerospace",
        "official_ir_url": "https://investor.northropgrumman.com/",
    },
    {
        "ticker_symbol": "CVX",
        "company_name": "Chevron Corporation",
        "exchange": "NYSE",
        "sector": "energy",
        "official_ir_url": "https://www.chevron.com/investors",
    },
    {
        "ticker_symbol": "COP",
        "company_name": "ConocoPhillips",
        "exchange": "NYSE",
        "sector": "energy",
        "official_ir_url": "https://www.conocophillips.com/investor/",
    },
    {
        "ticker_symbol": "SLB",
        "company_name": "SLB",
        "exchange": "NYSE",
        "sector": "energy",
        "official_ir_url": "https://investorcenter.slb.com/",
    },
    {
        "ticker_symbol": "HAL",
        "company_name": "Halliburton Company",
        "exchange": "NYSE",
        "sector": "energy",
        "official_ir_url": "https://ir.halliburton.com/",
    },
    {
        "ticker_symbol": "PG",
        "company_name": "The Procter & Gamble Company",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://www.pginvestor.com/",
    },
    {
        "ticker_symbol": "CL",
        "company_name": "Colgate-Palmolive Company",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://investor.colgatepalmolive.com/",
    },
    {
        "ticker_symbol": "KMB",
        "company_name": "Kimberly-Clark Corporation",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://investor.kimberly-clark.com/",
    },
    {
        "ticker_symbol": "PEP",
        "company_name": "PepsiCo, Inc.",
        "exchange": "NASDAQ",
        "sector": "consumer",
        "official_ir_url": "https://investors.pepsico.com/",
    },
    {
        "ticker_symbol": "FDX",
        "company_name": "FedEx Corporation",
        "exchange": "NYSE",
        "sector": "industrials",
        "official_ir_url": "https://investors.fedex.com/",
    },
    {
        "ticker_symbol": "DAL",
        "company_name": "Delta Air Lines, Inc.",
        "exchange": "NYSE",
        "sector": "industrials",
        "official_ir_url": "https://ir.delta.com/",
    },
    {
        "ticker_symbol": "UAL",
        "company_name": "United Airlines Holdings, Inc.",
        "exchange": "NASDAQ",
        "sector": "industrials",
        "official_ir_url": "https://ir.united.com/",
    },
    {
        "ticker_symbol": "SPGI",
        "company_name": "S&P Global Inc.",
        "exchange": "NYSE",
        "sector": "payments_financial_services",
        "official_ir_url": "https://investor.spglobal.com/",
    },
    {
        "ticker_symbol": "MCO",
        "company_name": "Moody's Corporation",
        "exchange": "NYSE",
        "sector": "payments_financial_services",
        "official_ir_url": "https://ir.moodys.com/",
    },
    {
        "ticker_symbol": "ICE",
        "company_name": "Intercontinental Exchange, Inc.",
        "exchange": "NYSE",
        "sector": "payments_financial_services",
        "official_ir_url": "https://ir.theice.com/",
    },
    {
        "ticker_symbol": "SCHW",
        "company_name": "The Charles Schwab Corporation",
        "exchange": "NYSE",
        "sector": "payments_financial_services",
        "official_ir_url": "https://www.aboutschwab.com/investor-relations",
    },
    {
        "ticker_symbol": "MMC",
        "company_name": "Marsh & McLennan Companies, Inc.",
        "exchange": "NYSE",
        "sector": "insurance",
        "official_ir_url": "https://ir.mmc.com/",
    },
    {
        "ticker_symbol": "AON",
        "company_name": "Aon plc",
        "exchange": "NYSE",
        "sector": "insurance",
        "official_ir_url": "https://ir.aon.com/",
    },
    {
        "ticker_symbol": "ABT",
        "company_name": "Abbott Laboratories",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://www.abbottinvestor.com/",
    },
    {
        "ticker_symbol": "BMY",
        "company_name": "Bristol Myers Squibb Company",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investor.bms.com/",
    },
    {
        "ticker_symbol": "MDT",
        "company_name": "Medtronic plc",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investorrelations.medtronic.com/",
    },
    {
        "ticker_symbol": "TMO",
        "company_name": "Thermo Fisher Scientific Inc.",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://ir.thermofisher.com/",
    },
    {
        "ticker_symbol": "DHR",
        "company_name": "Danaher Corporation",
        "exchange": "NYSE",
        "sector": "healthcare",
        "official_ir_url": "https://investors.danaher.com/",
    },
    {
        "ticker_symbol": "EL",
        "company_name": "The Estee Lauder Companies Inc.",
        "exchange": "NYSE",
        "sector": "consumer",
        "official_ir_url": "https://www.elcompanies.com/en/investors",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_date(value: str | None) -> date:
    if value:
        return date.fromisoformat(value)
    return datetime.now(timezone.utc).date()


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized or "company"


def domain_for_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return parsed.netloc.lower().removeprefix("www.")
    if url.startswith("sec-edgar://"):
        return "sec-edgar"
    if url.startswith("licensed-vendor://"):
        return "licensed-vendor"
    return ""


def period_call_date(fiscal_year: int, quarter: int) -> date:
    if quarter == 1:
        return date(fiscal_year, 4, 14)
    if quarter == 2:
        return date(fiscal_year, 7, 14)
    if quarter == 3:
        return date(fiscal_year, 10, 14)
    return date(fiscal_year + 1, 1, 14)


def cutoff_date(as_of_date: date, years_back: int) -> date:
    try:
        return as_of_date.replace(year=as_of_date.year - years_back)
    except ValueError:
        return as_of_date.replace(month=2, day=28, year=as_of_date.year - years_back)


def recent_fiscal_periods(*, years_back: int, as_of_date: date) -> list[dict[str, str]]:
    cutoff = cutoff_date(as_of_date, years_back)
    periods: list[dict[str, str]] = []
    for fiscal_year in range(as_of_date.year, as_of_date.year - years_back - 2, -1):
        for quarter in (4, 3, 2, 1):
            call_date = period_call_date(fiscal_year, quarter)
            if cutoff <= call_date <= as_of_date:
                periods.append(
                    {
                        "fiscal_year": str(fiscal_year),
                        "fiscal_quarter": f"Q{quarter}",
                        "calendar_year": str(call_date.year),
                        "earnings_call_date": call_date.isoformat(),
                    }
                )
    periods.sort(key=lambda row: row["earnings_call_date"], reverse=True)
    return periods


def nyse_seed_companies() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    included: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for seed in SEED_COMPANIES:
        row = dict(seed)
        row["source_domain"] = domain_for_url(row["official_ir_url"])
        row["exchange_verified"] = "true"
        row["exchange_verification_source"] = "curated_seed_exchange_table"
        if row["exchange"] == "NYSE":
            row["included"] = "true"
            row["exclusion_reason"] = ""
            included.append(row)
        else:
            row["included"] = "false"
            row["exclusion_reason"] = f"excluded because exchange={row['exchange']}"
            excluded.append(row)
    return included, excluded


def priority_tier_for(transcript_availability: str, audio_availability: str, video_availability: str) -> str:
    transcript = transcript_availability == "available"
    audio = audio_availability == "available"
    video = video_availability == "available"
    if transcript and audio and video:
        return "1"
    if transcript and audio:
        return "2"
    if transcript:
        return "3"
    return "4"


def classify_rights_status(
    *,
    source_type: str,
    metadata_only: bool,
    raw_requested: bool,
    license_config_ref: str = "",
    source_terms_checked: bool = False,
    robots_checked: bool = False,
) -> dict[str, str]:
    if source_type == "youtube_metadata_only" and raw_requested:
        return {
            "rights_status": "blocked",
            "blocked_reason": "youtube_media_download_blocked",
            "notes": "YouTube metadata and links are allowed; audio/video download is blocked without explicit authorization.",
        }
    if source_type == "earnings_platform" and raw_requested and not license_config_ref:
        return {
            "rights_status": "blocked",
            "blocked_reason": "licensed_vendor_without_license_config",
            "notes": "Licensed vendor or earnings-platform raw content requires an explicit license config.",
        }
    if source_type == "company_ir" and raw_requested and not (source_terms_checked and robots_checked):
        return {
            "rights_status": "blocked",
            "blocked_reason": "official_ir_raw_not_approved",
            "notes": "Official IR raw use requires source terms and robots review plus explicit approval.",
        }
    if metadata_only:
        return {
            "rights_status": "metadata_only",
            "blocked_reason": "metadata_only_no_raw_download",
            "notes": "Metadata-only source indexing; no raw asset storage is permitted in this run.",
        }
    if raw_requested and source_terms_checked and robots_checked:
        return {"rights_status": "safe_to_download", "blocked_reason": "", "notes": "Explicit raw permission recorded."}
    return {"rights_status": "unknown", "blocked_reason": "unknown_rights", "notes": "Unknown rights fail closed."}


def youtube_query_url(ticker: str, company_name: str, fiscal_year: str, fiscal_quarter: str) -> str:
    query = quote_plus(f"{ticker} {company_name} earnings call {fiscal_year} {fiscal_quarter}")
    return f"https://www.youtube.com/results?search_query={query}"


def sec_ref(ticker: str, fiscal_year: str, fiscal_quarter: str) -> str:
    return f"sec-edgar://CIK_LOOKUP_REQUIRED/{ticker}/{fiscal_year}/{fiscal_quarter}"


def call_folder_for(output_root: Path, row: dict[str, str]) -> Path:
    company_folder = f"{row['ticker_symbol']}_{slug(row['company_name'])}"
    call_folder = f"{row['earnings_call_date']}_FY{row['fiscal_year']}_{row['fiscal_quarter']}"
    return output_root / company_folder / call_folder


def build_candidate_calls(
    *,
    target_count: int,
    years_back: int,
    as_of_date: date | None = None,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    discovered_timestamp: str | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    as_of = as_of_date or datetime.now(timezone.utc).date()
    timestamp = discovered_timestamp or now_iso()
    companies, exclusions = nyse_seed_companies()
    periods = recent_fiscal_periods(years_back=years_back, as_of_date=as_of)
    rows: list[dict[str, str]] = []
    for period in periods:
        for company in companies:
            if len(rows) >= target_count:
                return rows, exclusions
            ticker = company["ticker_symbol"]
            fiscal_year = period["fiscal_year"]
            fiscal_quarter = period["fiscal_quarter"]
            transcript_availability = "unknown"
            audio_availability = "unknown"
            video_availability = "unknown"
            rights = classify_rights_status(source_type="company_ir", metadata_only=True, raw_requested=False)
            base = {
                "case_id": f"{ticker.lower()}_{fiscal_year}_{fiscal_quarter.lower()}",
                "ticker_symbol": ticker,
                "company_name": company["company_name"],
                "exchange": "NYSE",
                "fiscal_year": fiscal_year,
                "fiscal_quarter": fiscal_quarter,
                "calendar_year": period["calendar_year"],
                "earnings_call_date": period["earnings_call_date"],
                "transcript_source_url": company["official_ir_url"],
                "audio_source_url": company["official_ir_url"],
                "video_source_url": company["official_ir_url"],
                "transcript_availability": transcript_availability,
                "audio_availability": audio_availability,
                "video_availability": video_availability,
                "source_type": "company_ir",
                "rights_status": rights["rights_status"],
                "priority_tier": priority_tier_for(transcript_availability, audio_availability, video_availability),
                "local_paths_created": "false",
                "notes": (
                    "Metadata-only candidate. Availability is not asserted until official IR source terms, "
                    "robots policy, and event identity are manually reviewed."
                ),
                "source_domain": company["source_domain"],
                "discovered_timestamp": timestamp,
                "acquisition_method": DISCOVERY_METHOD,
            }
            base["provenance_hash"] = stable_hash(
                {
                    "case_id": base["case_id"],
                    "ticker_symbol": ticker,
                    "company_name": company["company_name"],
                    "fiscal_year": fiscal_year,
                    "fiscal_quarter": fiscal_quarter,
                    "earnings_call_date": period["earnings_call_date"],
                    "transcript_source_url": company["official_ir_url"],
                    "audio_source_url": company["official_ir_url"],
                    "video_source_url": company["official_ir_url"],
                    "rights_status": base["rights_status"],
                    "acquisition_method": DISCOVERY_METHOD,
                }
            )
            base["call_folder"] = str(call_folder_for(output_root, base))
            rows.append(base)
    return rows, exclusions


def build_source_registry(manifest_rows: list[dict[str, str]], *, timestamp: str | None = None) -> list[dict[str, str]]:
    discovered_at = timestamp or now_iso()
    rows: list[dict[str, str]] = []
    for manifest in manifest_rows:
        ticker = manifest["ticker_symbol"]
        fiscal_year = manifest["fiscal_year"]
        fiscal_quarter = manifest["fiscal_quarter"]
        common = {
            "case_id": manifest["case_id"],
            "ticker_symbol": ticker,
            "company_name": manifest["company_name"],
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "acquisition_method": DISCOVERY_METHOD,
            "discovered_timestamp": discovered_at,
        }
        candidates = [
            {
                **common,
                "source_type": "company_ir",
                "source_url": manifest["transcript_source_url"],
                "availability": "unknown",
                "rights_status": "metadata_only",
                "raw_download_allowed": "false",
                "blocked_reason": "source_terms_and_robots_not_reviewed",
                "manual_action": "Review official IR source terms and robots policy before any raw transcript use.",
                "notes": "Preferred transcript source when terms allow; this row does not assert transcript availability.",
            },
            {
                **common,
                "source_type": "webcast_provider",
                "source_url": manifest["audio_source_url"],
                "availability": "unknown",
                "rights_status": "metadata_only",
                "raw_download_allowed": "false",
                "blocked_reason": "webcast_terms_not_reviewed",
                "manual_action": "Open from company IR, verify replay access and storage terms, and avoid session-restricted media.",
                "notes": "Audio/webcast replay candidate only; support layer, not canonical transcript.",
            },
            {
                **common,
                "source_type": "sec_edgar",
                "source_url": sec_ref(ticker, fiscal_year, fiscal_quarter),
                "availability": "unknown",
                "rights_status": "metadata_only",
                "raw_download_allowed": "false",
                "blocked_reason": "sec_metadata_only_no_raw_filing_body",
                "manual_action": "Optional later SEC metadata fetch with descriptive User-Agent and <=10 rps rate limit.",
                "notes": "SEC may identify event timing, 8-K references, releases, and exhibit metadata; transcripts are not guaranteed.",
            },
            {
                **common,
                "source_type": "youtube_metadata_only",
                "source_url": youtube_query_url(ticker, manifest["company_name"], fiscal_year, fiscal_quarter),
                "availability": "unknown",
                "rights_status": "metadata_only",
                "raw_download_allowed": "false",
                "blocked_reason": "youtube_media_download_blocked_without_authorization",
                "manual_action": "Use YouTube links as metadata references only unless explicit authorization exists.",
                "notes": "No YouTube audio or video acquisition is performed.",
            },
            {
                **common,
                "source_type": "earnings_platform",
                "source_url": f"licensed-vendor://blocked/{ticker}/{fiscal_year}/{fiscal_quarter}",
                "availability": "blocked",
                "rights_status": "blocked",
                "raw_download_allowed": "false",
                "blocked_reason": "licensed_vendor_without_license_config",
                "manual_action": "Register license configuration before any vendor raw content use.",
                "notes": "Vendor raw transcript access is blocked by default.",
            },
        ]
        for index, candidate in enumerate(candidates, start=1):
            candidate["source_domain"] = domain_for_url(candidate["source_url"])
            candidate["registry_id"] = f"{manifest['case_id']}_{candidate['source_type']}_{index}"
            candidate["provenance_hash"] = stable_hash(
                {
                    "registry_id": candidate["registry_id"],
                    "case_id": candidate["case_id"],
                    "source_type": candidate["source_type"],
                    "source_url": candidate["source_url"],
                    "rights_status": candidate["rights_status"],
                    "raw_download_allowed": candidate["raw_download_allowed"],
                }
            )
            rows.append(candidate)
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_local_call_workspace(row: dict[str, str], registry_rows: list[dict[str, str]], *, dry_run: bool) -> dict[str, str]:
    call_folder = Path(row["call_folder"])
    if dry_run:
        return {**row, "local_paths_created": "false"}
    for child in ("transcript", "audio", "video", "metadata", "provenance"):
        (call_folder / child).mkdir(parents=True, exist_ok=True)
    case_sources = [source for source in registry_rows if source["case_id"] == row["case_id"]]
    metadata_payload = {field: row[field] for field in MANIFEST_FIELDS if field in row}
    metadata_payload["workspace_policy"] = {
        "metadata_only": True,
        "raw_transcript_downloaded": False,
        "raw_audio_downloaded": False,
        "raw_video_downloaded": False,
        "raw_assets_committed_to_git": False,
    }
    provenance_payload = {
        "case_id": row["case_id"],
        "ticker_symbol": row["ticker_symbol"],
        "company_name": row["company_name"],
        "discovered_timestamp": row["discovered_timestamp"],
        "acquisition_method": DISCOVERY_METHOD,
        "provenance_hash": row["provenance_hash"],
        "candidate_sources": case_sources,
        "rights_guardrails": [
            "unknown_rights_fail_closed",
            "source_terms_review_required_for_raw_use",
            "robots_review_required_for_raw_use",
            "paywall_login_drm_and_session_restrictions_not_bypassed",
            "youtube_media_download_blocked_without_authorization",
            "licensed_vendor_raw_blocked_without_license_config",
            "no_raw_assets_written_to_git",
        ],
    }
    write_json(call_folder / "metadata" / "manifest.json", metadata_payload)
    write_json(call_folder / "provenance" / "provenance.json", provenance_payload)
    return {**row, "local_paths_created": "true"}


def write_targets(path: Path) -> list[dict[str, str]]:
    included, excluded = nyse_seed_companies()
    rows = included + excluded
    write_csv(path, rows, TARGET_FIELDS)
    return rows


def count_manifest_statuses(rows: list[dict[str, str]]) -> dict[str, Any]:
    tier_counts = {tier: 0 for tier in ("1", "2", "3", "4")}
    for row in rows:
        tier_counts[row["priority_tier"]] += 1
    return {
        "tier_counts": tier_counts,
        "transcript_availability": dict(Counter(row["transcript_availability"] for row in rows)),
        "audio_availability": dict(Counter(row["audio_availability"] for row in rows)),
        "video_availability": dict(Counter(row["video_availability"] for row in rows)),
        "rights_status": dict(Counter(row["rights_status"] for row in rows)),
    }


def summarize(
    manifest_rows: list[dict[str, str]],
    registry_rows: list[dict[str, str]],
    exclusions: list[dict[str, str]],
    *,
    output_root: Path,
    reports_dir: Path,
    validation_status: str = "not_run",
) -> dict[str, Any]:
    counts = count_manifest_statuses(manifest_rows)
    blocked_or_paywalled_cases = sum(
        1
        for row in manifest_rows
        if "blocked" in {row["transcript_availability"], row["audio_availability"], row["video_availability"]}
        or "paywalled" in {row["transcript_availability"], row["audio_availability"], row["video_availability"]}
    )
    top_domains = Counter(row["source_domain"] for row in registry_rows if row["source_domain"])
    source_type_distribution = Counter(row["source_type"] for row in registry_rows)
    blocker_counts = Counter(row["blocked_reason"] for row in registry_rows if row["blocked_reason"])
    missing_media = Counter()
    for row in manifest_rows:
        for media_type in ("transcript", "audio", "video"):
            availability = row[f"{media_type}_availability"]
            if availability != "available":
                missing_media[f"{media_type}_{availability}"] += 1
    return {
        "total_candidates_found": len(manifest_rows),
        "total_priority_1": counts["tier_counts"]["1"],
        "total_priority_2": counts["tier_counts"]["2"],
        "total_priority_3": counts["tier_counts"]["3"],
        "total_priority_4": counts["tier_counts"]["4"],
        "tier_counts": counts["tier_counts"],
        "blocked_or_paywalled_cases": blocked_or_paywalled_cases,
        "blocked_registry_sources": sum(1 for row in registry_rows if row["rights_status"] == "blocked"),
        "safe_download_candidates": sum(1 for row in registry_rows if row["rights_status"] == "safe_to_download"),
        "top_source_domains": dict(top_domains.most_common(15)),
        "source_type_distribution": dict(source_type_distribution),
        "missing_media_distribution": dict(missing_media),
        "common_blockers": dict(blocker_counts.most_common(15)),
        "exchange_exclusion_counts": dict(Counter(row["exchange"] for row in exclusions)),
        "exchange_exclusions": exclusions,
        "next_20_manual_review_actions": next_manual_actions(registry_rows, limit=20),
        "output_root": str(output_root),
        "reports_dir": str(reports_dir),
        "validation_status": validation_status,
        "git_status_summary": git_status_summary(),
        "legal_technical_blockers": [
            "Official IR source terms and robots policy are not reviewed in this metadata-only run.",
            "SEC rows are queued as metadata references only; no filing body download is enabled.",
            "Webcast provider replay access can be session-restricted or expire.",
            "YouTube media acquisition is blocked without explicit authorization.",
            "Licensed vendor content is blocked without a license config.",
        ],
        "recommended_next_acquisition_targets": [
            "Review official IR terms and robots policy for top-priority company IR domains.",
            "Enable SEC metadata fetch only with a descriptive User-Agent and <=10 requests/second rate limit.",
            "Manually register local transcript files by path and sha256 when source terms are unclear.",
            "Promote only rights-reviewed transcript bodies into local analysis workflows.",
        ],
    }


def next_manual_actions(registry_rows: list[dict[str, str]], *, limit: int) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    preferred_types = ["company_ir", "webcast_provider", "sec_edgar", "youtube_metadata_only", "earnings_platform"]
    ordered = sorted(registry_rows, key=lambda row: (preferred_types.index(row["source_type"]) if row["source_type"] in preferred_types else 99, row["case_id"]))
    for row in ordered:
        key = (row["case_id"], row["source_type"])
        if key in seen:
            continue
        seen.add(key)
        actions.append(
            {
                "case_id": row["case_id"],
                "ticker_symbol": row["ticker_symbol"],
                "source_type": row["source_type"],
                "source_url": row["source_url"],
                "manual_action": row["manual_action"],
                "blocked_reason": row["blocked_reason"],
            }
        )
        if len(actions) >= limit:
            return actions
    return actions


def git_status_summary() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return "git status unavailable"
    return result.stdout.strip()


def markdown_table(counter: dict[str, int]) -> str:
    if not counter:
        return "| value | count |\n|---|---|\n| none | 0 |"
    lines = ["| value | count |", "|---|---|"]
    for key, value in counter.items():
        lines.append(f"| {key} | {value} |")
    return "\n".join(lines)


def write_progress_report(path: Path, rows: list[dict[str, str]], registry_rows: list[dict[str, str]], exclusions: list[dict[str, str]], *, output_root: Path) -> None:
    subset_case_ids = {row["case_id"] for row in rows}
    subset_registry = [row for row in registry_rows if row["case_id"] in subset_case_ids]
    status = summarize(rows, subset_registry, exclusions, output_root=output_root, reports_dir=path.parent)
    content = [
        "# NYSE 100 Media Corpus Progress",
        "",
        f"- Calls discovered: {status['total_candidates_found']}",
        f"- Local output root: `{output_root}`",
        "",
        "## Tier Counts",
        "",
        markdown_table(status["tier_counts"]),
        "",
        "## Blocked Counts",
        "",
        f"- Blocked/paywalled manifest cases: {status['blocked_or_paywalled_cases']}",
        f"- Blocked source-registry rows: {status['blocked_registry_sources']}",
        "",
        "## Top Domains",
        "",
        markdown_table(status["top_source_domains"]),
        "",
        "## Common Blockers",
        "",
        markdown_table(status["common_blockers"]),
        "",
        "## Exchange Exclusions",
        "",
        markdown_table(status["exchange_exclusion_counts"]),
        "",
        "## Missing Media Breakdown",
        "",
        markdown_table(status["missing_media_distribution"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(content), encoding="utf-8")


def write_final_reports(reports_dir: Path, status: dict[str, Any]) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "nyse_100_media_corpus_status.json", status)
    actions = status["next_20_manual_review_actions"]
    action_lines = [
        f"- `{item['case_id']}` `{item['source_type']}`: {item['manual_action']} ({item['source_url']})"
        for item in actions
    ]
    content = [
        "# NYSE 100 Media Corpus Status",
        "",
        f"- Total candidates found: {status['total_candidates_found']}",
        f"- Priority 1: {status['total_priority_1']}",
        f"- Priority 2: {status['total_priority_2']}",
        f"- Priority 3: {status['total_priority_3']}",
        f"- Priority 4: {status['total_priority_4']}",
        f"- Blocked/paywalled manifest cases: {status['blocked_or_paywalled_cases']}",
        f"- Blocked source-registry rows: {status['blocked_registry_sources']}",
        f"- Safe download candidates: {status['safe_download_candidates']}",
        f"- Local output root: `{status['output_root']}`",
        f"- Validation status: {status['validation_status']}",
        "",
        "## Top Source Domains",
        "",
        markdown_table(status["top_source_domains"]),
        "",
        "## Source Type Distribution",
        "",
        markdown_table(status["source_type_distribution"]),
        "",
        "## Missing Media Distribution",
        "",
        markdown_table(status["missing_media_distribution"]),
        "",
        "## Exchange Exclusions",
        "",
        markdown_table(status["exchange_exclusion_counts"]),
        "",
        "## Next 20 Manual Review Actions",
        "",
        "\n".join(action_lines) if action_lines else "- none",
        "",
        "## Legal And Technical Blockers",
        "",
        "\n".join(f"- {item}" for item in status["legal_technical_blockers"]),
        "",
        "## Recommended Next Acquisition Targets",
        "",
        "\n".join(f"- {item}" for item in status["recommended_next_acquisition_targets"]),
        "",
        "## Git Status Summary",
        "",
        "```text",
        status["git_status_summary"],
        "```",
        "",
    ]
    (reports_dir / "nyse_100_media_corpus_status.md").write_text("\n".join(content), encoding="utf-8")
    safe_download_content = [
        "# Safe Download Candidates",
        "",
        "No raw downloads are authorized by the generated metadata-only run.",
        "",
        f"- Safe download candidates: {status['safe_download_candidates']}",
        "- Required before any download: reviewed source terms, robots policy where applicable, explicit approval, and storage flags.",
        "",
    ]
    (reports_dir / "safe_download_candidates.md").write_text("\n".join(safe_download_content), encoding="utf-8")


def run_discovery(
    *,
    target_count: int,
    years_back: int,
    output_root: Path,
    manifest_path: Path,
    source_registry_path: Path,
    targets_path: Path,
    reports_dir: Path,
    metadata_only: bool,
    max_workers: int,
    checkpoint_interval: int,
    dry_run: bool,
    as_of_date: date | None = None,
) -> dict[str, Any]:
    if target_count <= 0:
        raise ValueError("target_count must be positive")
    if years_back <= 0:
        raise ValueError("years_back must be positive")
    if not metadata_only:
        raise ValueError("Only metadata-only mode is implemented; raw acquisition requires explicit source-rights approval.")
    if max_workers <= 0:
        raise ValueError("max_workers must be positive")
    if checkpoint_interval <= 0:
        raise ValueError("checkpoint_interval must be positive")

    timestamp = now_iso()
    manifest_rows, exclusions = build_candidate_calls(
        target_count=target_count,
        years_back=years_back,
        as_of_date=as_of_date,
        output_root=output_root,
        discovered_timestamp=timestamp,
    )
    if len(manifest_rows) < target_count:
        raise RuntimeError(f"only generated {len(manifest_rows)} candidate calls for target_count={target_count}")
    registry_rows = build_source_registry(manifest_rows, timestamp=timestamp)

    updated_rows: list[dict[str, str]] = []
    for row in manifest_rows:
        updated_rows.append(write_local_call_workspace(row, registry_rows, dry_run=dry_run))
    manifest_rows = updated_rows

    write_targets(targets_path)
    write_csv(manifest_path, manifest_rows, MANIFEST_FIELDS)
    write_csv(source_registry_path, registry_rows, SOURCE_REGISTRY_FIELDS)

    for checkpoint in range(checkpoint_interval, len(manifest_rows), checkpoint_interval):
        write_progress_report(
            reports_dir / f"nyse_100_media_progress_{checkpoint:03d}.md",
            manifest_rows[:checkpoint],
            registry_rows,
            exclusions,
            output_root=output_root,
        )

    status = summarize(manifest_rows, registry_rows, exclusions, output_root=output_root, reports_dir=reports_dir)
    write_final_reports(reports_dir, status)
    return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-count", type=int, default=100)
    parser.add_argument("--years-back", type=int, default=5)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-registry", type=Path, default=DEFAULT_SOURCE_REGISTRY)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--metadata-only", action="store_true", default=True)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--checkpoint-interval", type=int, default=25)
    parser.add_argument("--as-of-date", help="Optional YYYY-MM-DD date for deterministic tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    status = run_discovery(
        target_count=args.target_count,
        years_back=args.years_back,
        output_root=args.output_root,
        manifest_path=args.manifest,
        source_registry_path=args.source_registry,
        targets_path=args.targets,
        reports_dir=args.reports_dir,
        metadata_only=True,
        max_workers=args.max_workers,
        checkpoint_interval=args.checkpoint_interval,
        dry_run=args.dry_run,
        as_of_date=parse_date(args.as_of_date),
    )
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
