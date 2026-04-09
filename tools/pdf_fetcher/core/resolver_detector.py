
from __future__ import annotations

from typing import Optional

from tools.pdf_fetcher.core.config import (
    ENABLE_ELSEVIER_RESOLVER,
    ENABLE_FRONTIERS_RESOLVER,
    ENABLE_MDPI_RESOLVER,
    ENABLE_SCI_HUB_RESOLVER,
    ENABLE_SPRINGER_RESOLVER,
    ENABLE_WILEY_RESOLVER,
)
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.utils import normalize_doi


DEFAULT_RESOLVER_ORDER = ("mdpi", "frontiers", "springer", "wiley", "elsevier", "sci_hub")


def _source_url_points_to_other_known_publisher(source_url: str, target: str) -> bool:
    source_lower = str(source_url or "").strip().lower()
    if not source_lower:
        return False

    known_publishers = {
        "frontiers": ("frontiersin.org",),
        "mdpi": ("mdpi.com",),
        "springer": ("springer.com", "link.springer.com", "springernature.com"),
        "wiley": ("onlinelibrary.wiley.com", "wiley.com", "esj-journals.onlinelibrary.wiley.com"),
        "elsevier": ("sciencedirect.com", "linkinghub.elsevier.com", "elsevier.com"),
        "tandf": ("tandfonline.com",),
        "oup": ("academic.oup.com", "oup.com"),
        "nature": ("nature.com",),
        "cambridge": ("cambridge.org",),
        "plos": ("journals.plos.org", "plos.org"),
        "akjournals": ("akjournals.com",),
    }

    target_hosts = known_publishers.get(target, ())
    if any(host in source_lower for host in target_hosts):
        return False

    for publisher, hosts in known_publishers.items():
        if publisher == target:
            continue
        if any(host in source_lower for host in hosts):
            return True

    return False


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
    source_lower = str(source_url or "").strip().lower()

    if source_lower:
        if "frontiersin.org" in source_lower:
            return True
        if _source_url_points_to_other_known_publisher(source_lower, "frontiers"):
            return False

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


def is_mdpi_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
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
    source_lower = str(source_url or "").strip().lower()

    if source_lower:
        if "mdpi.com" in source_lower:
            return True
        if _source_url_points_to_other_known_publisher(source_lower, "mdpi"):
            return False

    for value in lowered:
        if "mdpi.com" in value:
            return True
        if value.startswith("10.3390/"):
            return True
        if "/10.3390/" in value:
            return True
    return False


def is_springer_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
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
    source_lower = str(source_url or "").strip().lower()

    if source_lower:
        if "springer.com" in source_lower or "link.springer.com" in source_lower or "springernature.com" in source_lower:
            return True
        if _source_url_points_to_other_known_publisher(source_lower, "springer"):
            return False

    for value in lowered:
        if "springer.com" in value or "link.springer.com" in value or "springernature.com" in value:
            return True
        if value.startswith("10.1007/"):
            return True
        if "/10.1007/" in value:
            return True
    return False


def is_elsevier_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
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
    source_lower = str(source_url or "").strip().lower()

    if source_lower:
        if "sciencedirect.com" in source_lower or "elsevier.com" in source_lower or "linkinghub.elsevier.com" in source_lower:
            return True
        if _source_url_points_to_other_known_publisher(source_lower, "elsevier"):
            return False

    for value in lowered:
        if "sciencedirect.com" in value or "elsevier.com" in value or "linkinghub.elsevier.com" in value:
            return True
        if value.startswith("10.1016/"):
            return True
        if "/10.1016/" in value:
            return True
    return False


def is_wiley_candidate_from_values(
    doi_raw: str,
    doi_link_raw: str,
    source_url: str = "",
) -> bool:
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
    source_lower = str(source_url or "").strip().lower()

    if source_lower:
        if (
            "onlinelibrary.wiley.com" in source_lower
            or "wiley.com" in source_lower
        ):
            return True
        if _source_url_points_to_other_known_publisher(source_lower, "wiley"):
            return False

    for value in lowered:
        if (
            "onlinelibrary.wiley.com" in value
            or "wiley.com" in value
        ):
            return True
        if value.startswith("10.1111/"):
            return True
        if "/10.1111/" in value:
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

    if ENABLE_MDPI_RESOLVER and is_mdpi_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "mdpi"

    if ENABLE_SPRINGER_RESOLVER and is_springer_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "springer"

    if ENABLE_WILEY_RESOLVER and is_wiley_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "wiley"

    if ENABLE_ELSEVIER_RESOLVER and is_elsevier_candidate_from_values(
        doi_raw=record.doi_raw,
        doi_link_raw=record.doi_link_raw,
        source_url=phase1_result.pdf_source_url,
    ):
        return "elsevier"

    return None


def get_ordered_resolver_names(
    record: Record,
    phase1_result: DownloadResult,
) -> list[str]:
    primary = detect_specialized_resolver_name(record, phase1_result)
    if primary:
        return [primary]

    return []


def should_retry_in_phase2(result: DownloadResult) -> bool:
    """
    Decide whether a phase 1 result should be retried in phase 2.
    """
    status = str(result.pdf_download_status or "").strip().lower()
    if not status:
        return False

    if status in {
        "downloaded",
        "duplicate_pdf",
        "downloaded_frontiers",
        "downloaded_mdpi",
        "downloaded_springer",
        "downloaded_wiley",
        "downloaded_sci_hub",
    }:
        return False

    return True
