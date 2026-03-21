
from __future__ import annotations

from typing import Optional

from app.config import ENABLE_FRONTIERS_RESOLVER
from app.models import DownloadResult, Record
from app.utils import normalize_doi


def is_frontiers_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
    """
    Return True if the values suggest the record belongs to Frontiers.
    """
    values = [
        str(doi_raw or "").strip(),
        str(doi_link_raw or "").strip(),
        str(source_url or "").strip(),
    ]

    normalized_doi = normalize_doi(doi_raw)
    normalized_doi_link = normalize_doi(doi_link_raw)

    if normalized_doi:
        values.append(normalized_doi)

    if normalized_doi_link:
        values.append(normalized_doi_link)

    lowered = [v.lower() for v in values if v]

    for value in lowered:
        if "frontiersin.org" in value:
            return True
        if "frontiers" in value:
            return True
        if value.startswith("10.3389/"):
            return True
        if "/10.3389/" in value:
            return True

    return False


def detect_specialized_resolver_name(
    record: Record,
    phase1_result: DownloadResult,
) -> Optional[str]:
    """
    Return the resolver name for phase 2, or None when no specialized
    resolver should be used.
    """
    if ENABLE_FRONTIERS_RESOLVER and is_frontiers_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "frontiers"

    return None


def should_retry_in_phase2(result: DownloadResult) -> bool:
    """
    Decide whether a phase 1 result should be retried in phase 2.
    """
    return result.pdf_download_status != "downloaded"