from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from signal_engine.acquisition.rights import decide_rights

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WORKSPACE = Path("/Users/keith/Desktop/earnings calls 100 samples")
DISCOVERED_TIMESTAMP = "2026-05-24T00:00:00+00:00"
ACQUISITION_METHOD = "metadata-first discovery"

COMPANY_FIELDS = ["rank", "ticker", "company_name", "exchange", "sector", "industry", "selection_reason", "exchange_status", "notes"]
TARGET_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "exchange",
    "sector",
    "target_year",
    "fiscal_year",
    "fiscal_quarter",
    "calendar_year",
    "event_date",
    "event_identity_status",
    "source_status",
    "notes",
]
AUDIT_FIELDS = [
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
    "transcript_local_path",
    "audio_local_path",
    "video_local_path",
    "blocked_reason",
    "next_action",
]
RIGHTS_DECISION_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "source_type",
    "asset_type",
    "source_url",
    "source_domain",
    "rights_status",
    "blocked_reason",
    "download_allowed",
    "commit_allowed",
    "training_allowed",
    "eval_allowed",
    "license_config_ref",
    "authorization_ref",
    "provenance_hash",
    "notes",
]
BLOCKED_SOURCE_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "source_type",
    "asset_type",
    "source_url",
    "source_domain",
    "rights_status",
    "blocked_reason",
    "next_action",
    "provenance_hash",
]
PERMITTED_DOWNLOAD_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "asset_type",
    "source_type",
    "source_url",
    "rights_status",
    "license_config_ref",
    "authorization_ref",
    "provenance_hash",
]
MANUAL_REGISTRY_FIELDS = [
    "case_id",
    "ticker",
    "company_name",
    "fiscal_period",
    "asset_type",
    "local_path",
    "sha256",
    "rights_status",
    "eval_allowed",
    "commit_allowed",
    "training_allowed",
    "raw_file_copied_into_repo",
    "registered_timestamp",
    "notes",
]
CHUNK_FIELDS = [
    "chunk_id",
    "case_id",
    "ticker",
    "asset_id",
    "asset_type",
    "chunk_type",
    "section",
    "speaker_role",
    "source_sha256",
    "text_sha256",
    "local_chunk_path",
    "start_char",
    "end_char",
    "start_time_sec",
    "end_time_sec",
    "rights_status",
    "rag_eligible",
    "raw_text_committed",
]

LEGACY_CHUNK_FIELDS = [
    "chunk_id",
    "case_id",
    "ticker",
    "source_sha256",
    "chunk_type",
    "section",
    "speaker_role",
    "start_hint",
    "end_hint",
    "text_sha256",
    "local_chunk_path",
    "rights_status",
    "raw_text_committed",
]


# The exchange status for this list was checked against SEC company_tickers_exchange
# metadata on 2026-05-24. Names are normalized for human-readable reports.
COMPANY_SEED: list[dict[str, str]] = [
    {"ticker": "JPM", "company_name": "JPMorgan Chase & Co.", "sector": "banking", "industry": "money-center banking", "ir_url": "https://www.jpmorganchase.com/ir"},
    {"ticker": "BAC", "company_name": "Bank of America Corporation", "sector": "banking", "industry": "money-center banking", "ir_url": "https://investor.bankofamerica.com/"},
    {"ticker": "C", "company_name": "Citigroup Inc.", "sector": "banking", "industry": "money-center banking", "ir_url": "https://www.citigroup.com/global/investors"},
    {"ticker": "WFC", "company_name": "Wells Fargo & Company", "sector": "banking", "industry": "diversified banking", "ir_url": "https://www.wellsfargo.com/about/investor-relations/"},
    {"ticker": "GS", "company_name": "The Goldman Sachs Group, Inc.", "sector": "banking", "industry": "investment banking", "ir_url": "https://www.goldmansachs.com/investor-relations/"},
    {"ticker": "MS", "company_name": "Morgan Stanley", "sector": "banking", "industry": "investment banking", "ir_url": "https://www.morganstanley.com/about-us-ir"},
    {"ticker": "BK", "company_name": "The Bank of New York Mellon Corporation", "sector": "banking", "industry": "custody banking", "ir_url": "https://www.bny.com/corporate/global/en/investor-relations.html"},
    {"ticker": "STT", "company_name": "State Street Corporation", "sector": "banking", "industry": "custody banking", "ir_url": "https://investors.statestreet.com/"},
    {"ticker": "USB", "company_name": "U.S. Bancorp", "sector": "banking", "industry": "regional banking", "ir_url": "https://ir.usbank.com/"},
    {"ticker": "PNC", "company_name": "The PNC Financial Services Group, Inc.", "sector": "banking", "industry": "regional banking", "ir_url": "https://investor.pnc.com/"},
    {"ticker": "TFC", "company_name": "Truist Financial Corporation", "sector": "banking", "industry": "regional banking", "ir_url": "https://ir.truist.com/"},
    {"ticker": "COF", "company_name": "Capital One Financial Corporation", "sector": "banking", "industry": "consumer finance", "ir_url": "https://investor.capitalone.com/"},
    {"ticker": "AXP", "company_name": "American Express Company", "sector": "payments", "industry": "card network and consumer finance", "ir_url": "https://ir.americanexpress.com/"},
    {"ticker": "V", "company_name": "Visa Inc.", "sector": "payments", "industry": "payments network", "ir_url": "https://investor.visa.com/"},
    {"ticker": "MA", "company_name": "Mastercard Incorporated", "sector": "payments", "industry": "payments network", "ir_url": "https://investor.mastercard.com/"},
    {"ticker": "FIS", "company_name": "Fidelity National Information Services, Inc.", "sector": "payments", "industry": "financial technology payments", "ir_url": "https://investor.fisglobal.com/"},
    {"ticker": "GPN", "company_name": "Global Payments Inc.", "sector": "payments", "industry": "merchant acquiring payments", "ir_url": "https://investors.globalpayments.com/"},
    {"ticker": "BLK", "company_name": "BlackRock, Inc.", "sector": "financial_infrastructure", "industry": "asset management", "ir_url": "https://ir.blackrock.com/"},
    {"ticker": "BX", "company_name": "Blackstone Inc.", "sector": "financial_infrastructure", "industry": "alternative asset management", "ir_url": "https://ir.blackstone.com/"},
    {"ticker": "SCHW", "company_name": "The Charles Schwab Corporation", "sector": "financial_infrastructure", "industry": "brokerage and wealth platform", "ir_url": "https://www.aboutschwab.com/investor-relations"},
    {"ticker": "ICE", "company_name": "Intercontinental Exchange, Inc.", "sector": "financial_infrastructure", "industry": "exchange and clearing infrastructure", "ir_url": "https://ir.theice.com/"},
    {"ticker": "SPGI", "company_name": "S&P Global Inc.", "sector": "financial_infrastructure", "industry": "rating agencies and market data", "ir_url": "https://investor.spglobal.com/"},
    {"ticker": "MCO", "company_name": "Moody's Corporation", "sector": "financial_infrastructure", "industry": "rating agencies and analytics", "ir_url": "https://ir.moodys.com/"},
    {"ticker": "AON", "company_name": "Aon plc", "sector": "insurance", "industry": "insurance brokerage", "ir_url": "https://investors.aon.com/"},
    {"ticker": "AIG", "company_name": "American International Group, Inc.", "sector": "insurance", "industry": "property and casualty insurance", "ir_url": "https://www.aig.com/investor-relations"},
    {"ticker": "MET", "company_name": "MetLife, Inc.", "sector": "insurance", "industry": "life insurance", "ir_url": "https://investor.metlife.com/"},
    {"ticker": "PRU", "company_name": "Prudential Financial, Inc.", "sector": "insurance", "industry": "life insurance and retirement", "ir_url": "https://www.investor.prudential.com/"},
    {"ticker": "TRV", "company_name": "The Travelers Companies, Inc.", "sector": "insurance", "industry": "property and casualty insurance", "ir_url": "https://investor.travelers.com/"},
    {"ticker": "CB", "company_name": "Chubb Limited", "sector": "insurance", "industry": "property and casualty insurance", "ir_url": "https://investors.chubb.com/"},
    {"ticker": "JNJ", "company_name": "Johnson & Johnson", "sector": "healthcare", "industry": "pharmaceuticals and medtech", "ir_url": "https://www.investor.jnj.com/"},
    {"ticker": "LLY", "company_name": "Eli Lilly and Company", "sector": "healthcare", "industry": "pharmaceuticals", "ir_url": "https://investor.lilly.com/"},
    {"ticker": "MRK", "company_name": "Merck & Co., Inc.", "sector": "healthcare", "industry": "pharmaceuticals", "ir_url": "https://www.merck.com/investor-relations/"},
    {"ticker": "PFE", "company_name": "Pfizer Inc.", "sector": "healthcare", "industry": "pharmaceuticals", "ir_url": "https://investors.pfizer.com/"},
    {"ticker": "UNH", "company_name": "UnitedHealth Group Incorporated", "sector": "healthcare", "industry": "managed care", "ir_url": "https://www.unitedhealthgroup.com/investors.html"},
    {"ticker": "CVS", "company_name": "CVS Health Corporation", "sector": "healthcare", "industry": "healthcare services and pharmacy", "ir_url": "https://investors.cvshealth.com/"},
    {"ticker": "ABT", "company_name": "Abbott Laboratories", "sector": "healthcare", "industry": "medical devices and diagnostics", "ir_url": "https://www.abbottinvestor.com/"},
    {"ticker": "BMY", "company_name": "Bristol Myers Squibb Company", "sector": "healthcare", "industry": "pharmaceuticals", "ir_url": "https://investors.bms.com/"},
    {"ticker": "MDT", "company_name": "Medtronic plc", "sector": "healthcare", "industry": "medical devices", "ir_url": "https://investorrelations.medtronic.com/"},
    {"ticker": "TMO", "company_name": "Thermo Fisher Scientific Inc.", "sector": "healthcare", "industry": "life sciences tools", "ir_url": "https://ir.thermofisher.com/"},
    {"ticker": "DHR", "company_name": "Danaher Corporation", "sector": "healthcare", "industry": "life sciences tools", "ir_url": "https://investors.danaher.com/"},
    {"ticker": "BDX", "company_name": "Becton, Dickinson and Company", "sector": "healthcare", "industry": "medical devices", "ir_url": "https://investors.bd.com/"},
    {"ticker": "CI", "company_name": "The Cigna Group", "sector": "healthcare", "industry": "managed care", "ir_url": "https://investors.thecignagroup.com/"},
    {"ticker": "HCA", "company_name": "HCA Healthcare, Inc.", "sector": "healthcare", "industry": "hospitals", "ir_url": "https://investor.hcahealthcare.com/"},
    {"ticker": "SYK", "company_name": "Stryker Corporation", "sector": "healthcare", "industry": "medical devices", "ir_url": "https://investors.stryker.com/"},
    {"ticker": "XOM", "company_name": "Exxon Mobil Corporation", "sector": "energy", "industry": "integrated oil and gas", "ir_url": "https://corporate.exxonmobil.com/investors"},
    {"ticker": "CVX", "company_name": "Chevron Corporation", "sector": "energy", "industry": "integrated oil and gas", "ir_url": "https://www.chevron.com/investors"},
    {"ticker": "COP", "company_name": "ConocoPhillips", "sector": "energy", "industry": "exploration and production", "ir_url": "https://www.conocophillips.com/investor-relations/"},
    {"ticker": "SLB", "company_name": "SLB", "sector": "energy", "industry": "oilfield services", "ir_url": "https://investorcenter.slb.com/"},
    {"ticker": "HAL", "company_name": "Halliburton Company", "sector": "energy", "industry": "oilfield services", "ir_url": "https://ir.halliburton.com/"},
    {"ticker": "EOG", "company_name": "EOG Resources, Inc.", "sector": "energy", "industry": "exploration and production", "ir_url": "https://investors.eogresources.com/"},
    {"ticker": "OXY", "company_name": "Occidental Petroleum Corporation", "sector": "energy", "industry": "exploration and production", "ir_url": "https://www.oxy.com/investors/"},
    {"ticker": "MPC", "company_name": "Marathon Petroleum Corporation", "sector": "energy", "industry": "refining and marketing", "ir_url": "https://www.marathonpetroleum.com/Investors/"},
    {"ticker": "PSX", "company_name": "Phillips 66", "sector": "energy", "industry": "refining and marketing", "ir_url": "https://investor.phillips66.com/"},
    {"ticker": "VLO", "company_name": "Valero Energy Corporation", "sector": "energy", "industry": "refining and marketing", "ir_url": "https://investorvalero.com/"},
    {"ticker": "BA", "company_name": "The Boeing Company", "sector": "aerospace", "industry": "commercial aerospace", "ir_url": "https://investors.boeing.com/"},
    {"ticker": "RTX", "company_name": "RTX Corporation", "sector": "aerospace", "industry": "aerospace and defense", "ir_url": "https://www.rtx.com/investors"},
    {"ticker": "LMT", "company_name": "Lockheed Martin Corporation", "sector": "aerospace", "industry": "defense aerospace", "ir_url": "https://investors.lockheedmartin.com/"},
    {"ticker": "NOC", "company_name": "Northrop Grumman Corporation", "sector": "aerospace", "industry": "defense aerospace", "ir_url": "https://investor.northropgrumman.com/"},
    {"ticker": "GD", "company_name": "General Dynamics Corporation", "sector": "aerospace", "industry": "defense aerospace", "ir_url": "https://investorrelations.gd.com/"},
    {"ticker": "CAT", "company_name": "Caterpillar Inc.", "sector": "industrials", "industry": "construction machinery", "ir_url": "https://investors.caterpillar.com/"},
    {"ticker": "DE", "company_name": "Deere & Company", "sector": "industrials", "industry": "agricultural machinery", "ir_url": "https://investor.deere.com/"},
    {"ticker": "GE", "company_name": "GE Aerospace", "sector": "industrials", "industry": "aerospace engines", "ir_url": "https://www.geaerospace.com/investors"},
    {"ticker": "ETN", "company_name": "Eaton Corporation plc", "sector": "industrials", "industry": "electrical equipment", "ir_url": "https://www.eaton.com/us/en-us/company/investor-relations.html"},
    {"ticker": "EMR", "company_name": "Emerson Electric Co.", "sector": "industrials", "industry": "industrial automation", "ir_url": "https://www.emerson.com/en-us/investors"},
    {"ticker": "MMM", "company_name": "3M Company", "sector": "industrials", "industry": "industrial conglomerate", "ir_url": "https://investors.3m.com/"},
    {"ticker": "ITW", "company_name": "Illinois Tool Works Inc.", "sector": "industrials", "industry": "industrial products", "ir_url": "https://investor.itw.com/"},
    {"ticker": "PH", "company_name": "Parker-Hannifin Corporation", "sector": "industrials", "industry": "motion and control", "ir_url": "https://investors.parker.com/"},
    {"ticker": "CARR", "company_name": "Carrier Global Corporation", "sector": "industrials", "industry": "building systems", "ir_url": "https://ir.carrier.com/"},
    {"ticker": "OTIS", "company_name": "Otis Worldwide Corporation", "sector": "industrials", "industry": "elevators and building systems", "ir_url": "https://www.otis.com/en/us/investors"},
    {"ticker": "UPS", "company_name": "United Parcel Service, Inc.", "sector": "logistics", "industry": "parcel logistics", "ir_url": "https://investors.ups.com/"},
    {"ticker": "FDX", "company_name": "FedEx Corporation", "sector": "logistics", "industry": "parcel logistics", "ir_url": "https://investors.fedex.com/"},
    {"ticker": "DAL", "company_name": "Delta Air Lines, Inc.", "sector": "logistics", "industry": "airline transportation", "ir_url": "https://ir.delta.com/"},
    {"ticker": "UNP", "company_name": "Union Pacific Corporation", "sector": "logistics", "industry": "rail transportation", "ir_url": "https://investor.unionpacific.com/"},
    {"ticker": "NSC", "company_name": "Norfolk Southern Corporation", "sector": "logistics", "industry": "rail transportation", "ir_url": "https://norfolksouthern.investorroom.com/"},
    {"ticker": "HD", "company_name": "The Home Depot, Inc.", "sector": "retail", "industry": "home improvement retail", "ir_url": "https://ir.homedepot.com/"},
    {"ticker": "LOW", "company_name": "Lowe's Companies, Inc.", "sector": "retail", "industry": "home improvement retail", "ir_url": "https://corporate.lowes.com/investors"},
    {"ticker": "TGT", "company_name": "Target Corporation", "sector": "retail", "industry": "general merchandise retail", "ir_url": "https://investors.target.com/"},
    {"ticker": "KR", "company_name": "The Kroger Co.", "sector": "retail", "industry": "grocery retail", "ir_url": "https://ir.kroger.com/"},
    {"ticker": "DG", "company_name": "Dollar General Corporation", "sector": "retail", "industry": "discount retail", "ir_url": "https://investor.dollargeneral.com/"},
    {"ticker": "MCD", "company_name": "McDonald's Corporation", "sector": "consumer", "industry": "restaurants", "ir_url": "https://corporate.mcdonalds.com/corpmcd/investors.html"},
    {"ticker": "YUM", "company_name": "Yum! Brands, Inc.", "sector": "consumer", "industry": "restaurants", "ir_url": "https://investors.yum.com/"},
    {"ticker": "NKE", "company_name": "NIKE, Inc.", "sector": "consumer", "industry": "apparel and footwear", "ir_url": "https://investors.nike.com/"},
    {"ticker": "DIS", "company_name": "The Walt Disney Company", "sector": "consumer", "industry": "media and entertainment", "ir_url": "https://thewaltdisneycompany.com/investor-relations/"},
    {"ticker": "KO", "company_name": "The Coca-Cola Company", "sector": "consumer", "industry": "beverages", "ir_url": "https://investors.coca-colacompany.com/"},
    {"ticker": "PG", "company_name": "The Procter & Gamble Company", "sector": "consumer", "industry": "household products", "ir_url": "https://www.pginvestor.com/"},
    {"ticker": "CL", "company_name": "Colgate-Palmolive Company", "sector": "consumer", "industry": "household products", "ir_url": "https://investor.colgatepalmolive.com/"},
    {"ticker": "EL", "company_name": "The Estee Lauder Companies Inc.", "sector": "consumer", "industry": "beauty products", "ir_url": "https://ir.elcompanies.com/"},
    {"ticker": "GIS", "company_name": "General Mills, Inc.", "sector": "consumer", "industry": "packaged food", "ir_url": "https://investors.generalmills.com/"},
    {"ticker": "HSY", "company_name": "The Hershey Company", "sector": "consumer", "industry": "packaged food", "ir_url": "https://www.thehersheycompany.com/en_us/investors.html"},
    {"ticker": "T", "company_name": "AT&T Inc.", "sector": "telecom", "industry": "telecommunications", "ir_url": "https://investors.att.com/"},
    {"ticker": "VZ", "company_name": "Verizon Communications Inc.", "sector": "telecom", "industry": "telecommunications", "ir_url": "https://www.verizon.com/about/investors"},
    {"ticker": "IBM", "company_name": "International Business Machines Corporation", "sector": "technology", "industry": "enterprise technology", "ir_url": "https://www.ibm.com/investor"},
    {"ticker": "ORCL", "company_name": "Oracle Corporation", "sector": "technology", "industry": "enterprise software", "ir_url": "https://investor.oracle.com/"},
    {"ticker": "CRM", "company_name": "Salesforce, Inc.", "sector": "technology", "industry": "cloud software", "ir_url": "https://investor.salesforce.com/"},
    {"ticker": "NOW", "company_name": "ServiceNow, Inc.", "sector": "technology", "industry": "cloud workflow software", "ir_url": "https://investors.servicenow.com/"},
    {"ticker": "ACN", "company_name": "Accenture plc", "sector": "technology", "industry": "technology consulting", "ir_url": "https://investor.accenture.com/"},
    {"ticker": "DELL", "company_name": "Dell Technologies Inc.", "sector": "technology", "industry": "hardware and infrastructure", "ir_url": "https://investors.delltechnologies.com/"},
    {"ticker": "HPQ", "company_name": "HP Inc.", "sector": "technology", "industry": "hardware", "ir_url": "https://investor.hp.com/"},
    {"ticker": "NET", "company_name": "Cloudflare, Inc.", "sector": "technology", "industry": "edge cloud infrastructure", "ir_url": "https://cloudflare.net/news-and-events/events-and-presentations"},
    {"ticker": "SNOW", "company_name": "Snowflake Inc.", "sector": "technology", "industry": "data cloud software", "ir_url": "https://investors.snowflake.com/"},
    {"ticker": "UBER", "company_name": "Uber Technologies, Inc.", "sector": "technology", "industry": "mobility platform", "ir_url": "https://investor.uber.com/"},
    {"ticker": "FICO", "company_name": "Fair Isaac Corporation", "sector": "technology", "industry": "analytics software", "ir_url": "https://investors.fico.com/"},
]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return text or "unknown"


def domain_for_url(value: str) -> str:
    if not value:
        return ""
    if value.startswith("sec-edgar://"):
        return "sec.gov"
    if value.startswith("licensed-vendor://"):
        return "licensed-vendor"
    if value.startswith("official-ir://"):
        return "official-ir-candidate"
    parsed = urlparse(value)
    return parsed.netloc.lower()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_company_universe() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for rank, company in enumerate(COMPANY_SEED[:100], start=1):
        rows.append(
            {
                "rank": str(rank),
                "ticker": company["ticker"],
                "company_name": company["company_name"],
                "exchange": "NYSE",
                "sector": company["sector"],
                "industry": company["industry"],
                "selection_reason": "NYSE large-cap/strategic coverage across required Signal Engine acquisition sectors",
                "exchange_status": "verified_sec_exchange_metadata_2026-05-24",
                "notes": "Included for rights-gated acquisition; raw assets remain Desktop-only and fail closed unless explicitly approved.",
            }
        )
    return rows


def _company_by_ticker() -> dict[str, dict[str, str]]:
    return {row["ticker"]: row for row in COMPANY_SEED}


def build_call_targets(companies: list[dict[str, str]] | None = None, *, start_year: int = 2025, years_back: int = 5) -> list[dict[str, str]]:
    universe = companies or build_company_universe()
    rows: list[dict[str, str]] = []
    for year in range(start_year, start_year - years_back, -1):
        for company in universe:
            ticker = company["ticker"]
            case_id = f"{ticker.lower()}_{year}_q4"
            rows.append(
                {
                    "case_id": case_id,
                    "ticker": ticker,
                    "company_name": company["company_name"],
                    "exchange": "NYSE",
                    "sector": company["sector"],
                    "target_year": str(year),
                    "fiscal_year": str(year),
                    "fiscal_quarter": "Q4",
                    "calendar_year": str(year),
                    "event_date": f"{year}-12-31",
                    "event_identity_status": "target_placeholder_period_end_date",
                    "source_status": "metadata_discovery_pending",
                    "notes": "Period-end folder date hint only; not a discovered earnings-call date until IR/SEC metadata confirms it.",
                }
            )
    return rows


def official_ir_url(ticker: str) -> str:
    company = _company_by_ticker().get(ticker, {})
    return company.get("ir_url") or f"official-ir://candidate/{ticker}"


def sec_ref(target: dict[str, str]) -> str:
    return f"sec-edgar://metadata-first/{target['ticker']}/{target['fiscal_year']}/{target['fiscal_quarter']}"


def youtube_ref(target: dict[str, str]) -> str:
    return f"https://www.youtube.com/results?search_query={target['ticker']}+{target['fiscal_year']}+{target['fiscal_quarter']}+earnings+call"


def call_folder_for(output_root: Path, target: dict[str, str]) -> Path:
    company_folder = f"{target['ticker']}_{slug(target['company_name'])}"
    call_folder = f"{target['event_date']}_FY{target['fiscal_year']}_{target['fiscal_quarter']}"
    return output_root / company_folder / call_folder


def build_source_candidates(targets: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        common = {
            "case_id": target["case_id"],
            "ticker": target["ticker"],
            "company_name": target["company_name"],
            "exchange": target["exchange"],
            "fiscal_year": target["fiscal_year"],
            "fiscal_quarter": target["fiscal_quarter"],
        }
        candidates = [
            {
                **common,
                "source_type": "official_ir",
                "asset_type": "transcript",
                "source_url": official_ir_url(target["ticker"]),
                "rights_status": "metadata_only",
                "raw_requested": False,
                "blocked_reason": "metadata_only_no_raw_download",
                "next_action": "Review official IR source terms, robots policy, and event identity before permitted acquisition.",
            },
            {
                **common,
                "source_type": "sec_edgar",
                "asset_type": "metadata",
                "source_url": sec_ref(target),
                "rights_status": "metadata_only",
                "raw_requested": False,
                "blocked_reason": "sec_metadata_only",
                "next_action": "Use SEC metadata-first discovery with descriptive User-Agent and <=10 requests/sec.",
            },
            {
                **common,
                "source_type": "youtube",
                "asset_type": "video",
                "source_url": youtube_ref(target),
                "rights_status": "metadata_only",
                "raw_requested": True,
                "blocked_reason": "youtube_media_blocked",
                "next_action": "Keep YouTube as metadata/link reference only unless explicit written authorization exists.",
            },
            {
                **common,
                "source_type": "vendor",
                "asset_type": "transcript",
                "source_url": f"licensed-vendor://blocked/{target['ticker']}/{target['fiscal_year']}/{target['fiscal_quarter']}",
                "rights_status": "license_required",
                "raw_requested": True,
                "blocked_reason": "vendor_license_missing",
                "next_action": "Register license_config_ref before any vendor raw content use.",
            },
        ]
        for candidate in candidates:
            decision = decide_rights(candidate)
            source_domain = domain_for_url(candidate["source_url"])
            row = {
                **candidate,
                "source_domain": source_domain,
                "rights_status": decision["rights_status"],
                "blocked_reason": decision["blocked_reason"] or candidate["blocked_reason"],
                "download_allowed": str(decision["download_allowed"]).lower(),
                "commit_allowed": "false",
                "training_allowed": "false",
                "eval_allowed": str(decision["eval_allowed"]).lower(),
                "license_config_ref": "",
                "authorization_ref": "",
                "notes": candidate["next_action"],
            }
            row["provenance_hash"] = stable_hash(
                {
                    "case_id": row["case_id"],
                    "source_type": row["source_type"],
                    "asset_type": row["asset_type"],
                    "source_url": row["source_url"],
                    "rights_status": row["rights_status"],
                    "blocked_reason": row["blocked_reason"],
                }
            )
            rows.append(row)
    return rows


def build_ir_source_candidates(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for target in targets:
        url = official_ir_url(target["ticker"])
        rows.append(
            {
                "case_id": target["case_id"],
                "ticker": target["ticker"],
                "company_name": target["company_name"],
                "fiscal_year": target["fiscal_year"],
                "fiscal_quarter": target["fiscal_quarter"],
                "official_ir_url": url,
                "source_domain": domain_for_url(url),
                "candidate_type": "known_official_ir_url_or_placeholder",
                "network_fetch_enabled": "false",
                "source_status": "candidate_unverified_event_identity",
                "rights_status": "metadata_only",
                "notes": "Candidate only; no broad crawling and no raw transcript/audio acquisition without explicit rights approval.",
            }
        )
    return rows


def build_sec_event_index(targets: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for target in targets:
        rows.append(
            {
                "case_id": target["case_id"],
                "ticker": target["ticker"],
                "company_name": target["company_name"],
                "fiscal_year": target["fiscal_year"],
                "fiscal_quarter": target["fiscal_quarter"],
                "target_forms": "8-K;10-Q;10-K",
                "sec_company_ref": sec_ref(target),
                "accession_number": "",
                "filing_url": "",
                "item_202_or_exhibit_991": "unknown_metadata_pending",
                "rights_status": "metadata_only",
                "blocked_reason": "sec_metadata_only",
                "notes": "SEC metadata-first target row; filing body and exhibit downloads disabled by default.",
            }
        )
    return rows


def build_source_availability(targets: list[dict[str, str]], rights_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rights_rows:
        grouped.setdefault(str(row["case_id"]), []).append(row)
    rows = []
    for target in targets:
        case_rows = grouped.get(target["case_id"], [])
        blocked = [row for row in case_rows if row["rights_status"] in {"blocked", "license_required"}]
        rows.append(
            {
                "case_id": target["case_id"],
                "ticker": target["ticker"],
                "company_name": target["company_name"],
                "exchange": "NYSE",
                "fiscal_year": target["fiscal_year"],
                "fiscal_quarter": target["fiscal_quarter"],
                "event_identity_status": target["event_identity_status"],
                "official_ir_status": "candidate_metadata_only",
                "sec_status": "metadata_only",
                "transcript_status": "not_collected_metadata_only",
                "audio_status": "not_collected_metadata_only",
                "video_status": "metadata_only_no_download",
                "safe_download_candidates": str(sum(1 for row in case_rows if row["rights_status"] == "safe_to_download")),
                "blocked_source_count": str(len(blocked)),
                "next_action": "Manual review official IR/SEC event identity and rights before permitted acquisition.",
            }
        )
    return rows


def populate_desktop_workspace(
    targets: list[dict[str, str]],
    *,
    output_root: Path = DEFAULT_WORKSPACE,
    checkpoint_interval: int = 25,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    audit_dir = output_root / "_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    rights_rows = build_source_candidates(targets)
    rights_by_case: dict[str, list[dict[str, Any]]] = {}
    for row in rights_rows:
        rights_by_case.setdefault(str(row["case_id"]), []).append(row)

    audit_rows: list[dict[str, str]] = []
    for index, target in enumerate(targets, start=1):
        folder = call_folder_for(output_root, target)
        for child in ("transcript", "audio", "video", "metadata", "provenance", "chunks"):
            (folder / child).mkdir(parents=True, exist_ok=True)
        ir_url = official_ir_url(target["ticker"])
        provenance_hash = stable_hash({"case_id": target["case_id"], "ticker": target["ticker"], "event_date": target["event_date"], "ir_url": ir_url})
        metadata = {
            "ticker_symbol": target["ticker"],
            "company_name": target["company_name"],
            "exchange": "NYSE",
            "fiscal_year": target["fiscal_year"],
            "fiscal_quarter": target["fiscal_quarter"],
            "calendar_year": target["calendar_year"],
            "earnings_call_date": target["event_date"],
            "event_identity_status": target["event_identity_status"],
            "transcript_source_url": ir_url,
            "audio_source_url": ir_url,
            "video_source_url": "",
            "transcript_availability": "unknown",
            "audio_availability": "unknown",
            "video_availability": "metadata_only",
            "source_type": "official_ir",
            "rights_status": "metadata_only",
            "priority_tier": "4",
            "local_paths_created": True,
            "notes": target["notes"],
            "source_domain": domain_for_url(ir_url),
            "discovered_timestamp": DISCOVERED_TIMESTAMP,
            "acquisition_method": ACQUISITION_METHOD,
            "provenance_hash": provenance_hash,
        }
        provenance = {
            "case_id": target["case_id"],
            "provenance_hash": provenance_hash,
            "source_availability_matrix": rights_by_case[target["case_id"]],
            "guardrails": [
                "rights-gated acquisition",
                "permitted acquisition only",
                "metadata-first discovery",
                "manual-local registration by path/hash only",
                "source availability matrix",
                "YouTube media download blocked by default",
                "vendor raw content requires license_config_ref",
            ],
        }
        write_json(folder / "metadata" / "call_metadata.json", metadata)
        write_json(folder / "metadata" / "source_availability.json", {"sources": rights_by_case[target["case_id"]]})
        write_json(folder / "provenance" / "provenance.json", provenance)
        write_json(
            folder / "provenance" / "rights_decision.json",
            {
                "case_id": target["case_id"],
                "rights_status": "metadata_only",
                "blocked_reason": "metadata_only_no_raw_download",
                "download_allowed": False,
                "commit_allowed": False,
                "training_allowed": False,
                "eval_allowed": False,
            },
        )
        audit_rows.append(
            {
                "case_id": target["case_id"],
                "ticker_symbol": target["ticker"],
                "company_name": target["company_name"],
                "exchange": "NYSE",
                "fiscal_year": target["fiscal_year"],
                "fiscal_quarter": target["fiscal_quarter"],
                "calendar_year": target["calendar_year"],
                "earnings_call_date": target["event_date"],
                "transcript_source_url": ir_url,
                "audio_source_url": ir_url,
                "video_source_url": "",
                "transcript_availability": "unknown",
                "audio_availability": "unknown",
                "video_availability": "metadata_only",
                "source_type": "official_ir",
                "rights_status": "metadata_only",
                "priority_tier": "4",
                "local_paths_created": "true",
                "notes": target["notes"],
                "source_domain": domain_for_url(ir_url),
                "discovered_timestamp": DISCOVERED_TIMESTAMP,
                "acquisition_method": ACQUISITION_METHOD,
                "provenance_hash": provenance_hash,
                "transcript_local_path": str(folder / "transcript"),
                "audio_local_path": str(folder / "audio"),
                "video_local_path": str(folder / "video"),
                "blocked_reason": "metadata_only_no_raw_download",
                "next_action": "Manual review official IR/SEC event identity and source rights before raw acquisition.",
            }
        )
        if checkpoint_interval > 0 and index % checkpoint_interval == 0:
            write_json(audit_dir / f"checkpoint_{index:04d}.json", {"rows_processed": index, "timestamp": now_iso()})

    blocked_rows = [
        {
            "case_id": row["case_id"],
            "ticker": row["ticker"],
            "company_name": row["company_name"],
            "source_type": row["source_type"],
            "asset_type": row["asset_type"],
            "source_url": row["source_url"],
            "source_domain": row["source_domain"],
            "rights_status": row["rights_status"],
            "blocked_reason": row["blocked_reason"],
            "next_action": row["next_action"],
            "provenance_hash": row["provenance_hash"],
        }
        for row in rights_rows
        if row["rights_status"] in {"blocked", "license_required"} or row["blocked_reason"] in {"youtube_media_blocked", "vendor_license_missing"}
    ]
    permitted_rows = [
        {field: str(row.get(field, "")) for field in PERMITTED_DOWNLOAD_FIELDS}
        for row in rights_rows
        if row["rights_status"] == "safe_to_download"
    ]
    write_csv(audit_dir / "nyse_100_company_list.csv", build_company_universe(), COMPANY_FIELDS)
    write_csv(audit_dir / "nyse_earnings_call_audit.csv", audit_rows, AUDIT_FIELDS)
    write_csv(audit_dir / "rights_decisions.csv", rights_rows, RIGHTS_DECISION_FIELDS)
    write_csv(audit_dir / "blocked_sources.csv", blocked_rows, BLOCKED_SOURCE_FIELDS)
    write_csv(audit_dir / "permitted_downloads.csv", permitted_rows, PERMITTED_DOWNLOAD_FIELDS)
    write_csv(audit_dir / "rag_chunk_index.csv", [], CHUNK_FIELDS)
    summary = build_acquisition_summary(audit_rows, rights_rows, blocked_rows, permitted_rows, output_root=output_root)
    write_json(audit_dir / "acquisition_summary.json", summary)
    (audit_dir / "acquisition_summary.md").write_text(summary_markdown(summary), encoding="utf-8")
    return summary


def build_acquisition_summary(
    audit_rows: list[dict[str, str]],
    rights_rows: list[dict[str, Any]],
    blocked_rows: list[dict[str, str]],
    permitted_rows: list[dict[str, str]],
    *,
    output_root: Path,
) -> dict[str, Any]:
    companies = {row["ticker_symbol"] for row in audit_rows}
    domains = Counter(row.get("source_domain", "") for row in audit_rows if row.get("source_domain"))
    blockers = Counter(row.get("blocked_reason", "") for row in blocked_rows if row.get("blocked_reason"))
    return {
        "total_companies_selected": len(companies),
        "total_call_folders_created": len(audit_rows),
        "total_transcript_files_downloaded": 0,
        "total_audio_files_downloaded": 0,
        "total_metadata_only_calls": sum(1 for row in audit_rows if row["rights_status"] == "metadata_only"),
        "total_blocked_sources": len(blocked_rows),
        "total_registered_transcripts": 0,
        "total_chunks": 0,
        "total_rag_ready_calls": 0,
        "safe_download_candidates": len(permitted_rows),
        "top_source_domains": dict(domains.most_common(10)),
        "top_blockers": dict(blockers.most_common(10)),
        "desktop_workspace": str(output_root),
        "next_manual_actions": [
            "Review official IR event pages and source terms for priority companies.",
            "Confirm SEC 8-K Item 2.02 or Exhibit 99.1 metadata where available.",
            "Register manually supplied rights-cleared transcript files by path and sha256 only.",
            "Add license_config_ref before any vendor transcript/audio use.",
        ],
    }


def summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# NYSE 100 Rights-Gated Acquisition Summary",
        "",
        f"- Desktop workspace: `{summary['desktop_workspace']}`",
        f"- Total companies selected: {summary['total_companies_selected']}",
        f"- Total call folders created: {summary['total_call_folders_created']}",
        f"- Transcript files downloaded: {summary['total_transcript_files_downloaded']}",
        f"- Audio files downloaded: {summary['total_audio_files_downloaded']}",
        f"- Metadata-only calls: {summary['total_metadata_only_calls']}",
        f"- Blocked sources: {summary['total_blocked_sources']}",
        f"- Registered transcripts: {summary['total_registered_transcripts']}",
        f"- Chunks: {summary['total_chunks']}",
        f"- BM25 smoke-ready calls: {summary['total_rag_ready_calls']}",
        "",
        "## Top Source Domains",
        "",
    ]
    if summary["top_source_domains"]:
        lines.extend(f"- {domain}: {count}" for domain, count in summary["top_source_domains"].items())
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Top Blockers",
            "",
        ]
    )
    if summary["top_blockers"]:
        lines.extend(f"- {reason}: {count}" for reason, count in summary["top_blockers"].items())
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Next Manual Actions",
        ]
    )
    lines.extend(f"- {item}" for item in summary["next_manual_actions"])
    lines.append("")
    return "\n".join(lines)


def register_manual_local_transcripts(workspace: Path, *, out_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for transcript in sorted(workspace.glob("*/*/transcript/*.txt")):
        if "_audit" in transcript.parts:
            continue
        call_folder = transcript.parent.parent
        metadata = _read_json_optional(call_folder / "metadata" / "call_metadata.json")
        rights = _read_json_optional(call_folder / "provenance" / "rights_decision.json")
        rights_status = str(rights.get("rights_status", "unknown_fail_closed"))
        eval_allowed = rights_status in {"safe_to_download", "manual_local_review_only"} and bool(rights.get("eval_allowed", False))
        row = {
            "case_id": str(metadata.get("case_id") or _case_id_from_folder(call_folder)),
            "ticker": str(metadata.get("ticker_symbol") or call_folder.parent.name.split("_", 1)[0]),
            "company_name": str(metadata.get("company_name") or ""),
            "fiscal_period": f"FY{metadata.get('fiscal_year', '')}_{metadata.get('fiscal_quarter', '')}".strip("_"),
            "asset_type": "transcript",
            "local_path": str(transcript),
            "sha256": file_sha256(transcript),
            "rights_status": rights_status,
            "eval_allowed": str(eval_allowed).lower(),
            "commit_allowed": "false",
            "training_allowed": "false",
            "raw_file_copied_into_repo": "false",
            "registered_timestamp": now_iso(),
            "notes": "manual-local registration stores path and sha256 only; raw text is not copied into git",
        }
        rows.append(row)
    write_csv(out_path, rows, MANUAL_REGISTRY_FIELDS)
    return rows


def _read_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _case_id_from_folder(call_folder: Path) -> str:
    ticker = call_folder.parent.name.split("_", 1)[0].lower()
    parts = call_folder.name.split("_")
    year = parts[1].replace("FY", "").lower() if len(parts) > 1 else "unknown"
    quarter = parts[2].lower() if len(parts) > 2 else "unknown"
    return f"{ticker}_{year}_{quarter}"


def build_desktop_chunks(workspace: Path, *, registry_path: Path, chunk_chars: int = 800, overlap_chars: int = 100) -> list[dict[str, str]]:
    registry_rows = read_csv(registry_path)
    chunk_rows: list[dict[str, str]] = []
    for row in registry_rows:
        if row.get("eval_allowed") != "true":
            continue
        if row.get("rights_status") not in {"safe_to_download", "manual_local_review_only"}:
            continue
        source = Path(row["local_path"])
        if not source.exists() or workspace not in source.resolve().parents:
            continue
        text = source.read_text(encoding="utf-8")
        call_folder = source.parent.parent
        chunks_dir = call_folder / "chunks"
        chunks_dir.mkdir(parents=True, exist_ok=True)
        start = 0
        ordinal = 1
        while start < len(text):
            end = min(len(text), start + chunk_chars)
            chunk_text = text[start:end]
            chunk_id = f"{row['case_id']}_chunk_{ordinal:04d}"
            chunk_path = chunks_dir / f"{chunk_id}.txt"
            chunk_path.write_text(chunk_text, encoding="utf-8")
            chunk_rows.append(
                {
                    "chunk_id": chunk_id,
                    "case_id": row["case_id"],
                    "ticker": row["ticker"],
                    "asset_id": f"{row['case_id']}_transcript",
                    "asset_type": "transcript",
                    "chunk_type": "transcript_text",
                    "section": "unknown",
                    "speaker_role": "unknown",
                    "source_sha256": row["sha256"],
                    "text_sha256": "sha256:" + hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                    "local_chunk_path": str(chunk_path),
                    "start_char": str(start),
                    "end_char": str(end),
                    "start_time_sec": "",
                    "end_time_sec": "",
                    "rights_status": row["rights_status"],
                    "rag_eligible": "true",
                    "raw_text_committed": "false",
                }
            )
            if end == len(text):
                break
            start = max(0, end - overlap_chars)
            ordinal += 1
        write_csv(chunks_dir / "chunk_manifest.csv", [chunk for chunk in chunk_rows if Path(chunk["local_chunk_path"]).parent == chunks_dir], CHUNK_FIELDS)
    write_csv(workspace / "_audit" / "rag_chunk_index.csv", chunk_rows, CHUNK_FIELDS)
    return chunk_rows


def build_rag_index_manifest(workspace: Path, *, out_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for manifest in sorted(workspace.glob("*/*/chunks/chunk_manifest.csv")):
        rows.extend(normalize_chunk_rows(read_csv(manifest)))
    write_csv(out_path, rows, CHUNK_FIELDS)
    write_csv(workspace / "_audit" / "rag_chunk_index.csv", rows, CHUNK_FIELDS)
    return rows


def normalize_chunk_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        start_char = row.get("start_char", row.get("start_hint", ""))
        end_char = row.get("end_char", row.get("end_hint", ""))
        chunk_type = row.get("chunk_type") or "transcript_text"
        if chunk_type == "semantic_chunk":
            chunk_type = "transcript_text"
        normalized.append(
            {
                "chunk_id": row.get("chunk_id", ""),
                "case_id": row.get("case_id", ""),
                "ticker": row.get("ticker", ""),
                "asset_id": row.get("asset_id") or f"{row.get('case_id', 'unknown')}_transcript",
                "asset_type": row.get("asset_type") or "transcript",
                "chunk_type": chunk_type,
                "section": row.get("section", ""),
                "speaker_role": row.get("speaker_role", ""),
                "source_sha256": row.get("source_sha256", ""),
                "text_sha256": row.get("text_sha256", ""),
                "local_chunk_path": row.get("local_chunk_path", ""),
                "start_char": start_char,
                "end_char": end_char,
                "start_time_sec": row.get("start_time_sec", ""),
                "end_time_sec": row.get("end_time_sec", ""),
                "rights_status": row.get("rights_status", ""),
                "rag_eligible": row.get("rag_eligible") or "true",
                "raw_text_committed": row.get("raw_text_committed", "false"),
            }
        )
    return normalized


def copy_file_url_to_workspace(source_url: str, destination: Path) -> None:
    parsed = urlparse(source_url)
    if parsed.scheme != "file":
        raise ValueError("only file:// URLs are supported by the local safe download helper")
    source = Path(parsed.path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
