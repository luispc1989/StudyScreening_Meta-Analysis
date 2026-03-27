
from __future__ import annotations

import re
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import requests

from tools.pdf_fetcher.core.config import CONNECT_TIMEOUT, HEADERS, READ_TIMEOUT
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.session_factory import build_session
from tools.pdf_fetcher.core.utils import deduplicate_urls, make_doi_url, normalize_doi, now_str, save_pdf_bytes


def response_looks_like_pdf(resp: requests.Response) -> bool:
    """
    Check whether the response looks like a PDF.
    """
    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "application/pdf" in content_type:
        return True

    try:
        return resp.content[:5] == b"%PDF-"
    except Exception:
        return False


def extract_pdf_url_from_html(base_url: str, html: str) -> Optional[str]:
    """
    Try to extract a PDF URL from the returned HTML.
    """
    if not html:
        return None

    patterns = [
        r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
        r'href=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
        r'src=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if match:
            return urljoin(base_url, match.group(1))

    return None


def classify_html_failure(status_code: Optional[int], html: str) -> str:
    """
    Classify a non-PDF HTML response into a status label.
    """
    text = (html or "").lower()

    if status_code == 403:
        return "paywalled"

    paywall_markers = [
        "purchase pdf",
        "buy article",
        "access through your institution",
        "institutional access",
        "subscribe to journal",
        "get access",
        "login via institution",
        "rent this article",
    ]
    if any(marker in text for marker in paywall_markers):
        return "paywalled"

    metadata_markers = [
        "abstract",
        "references",
        "metrics",
        "article info",
    ]
    if any(marker in text for marker in metadata_markers):
        return "metadata_only"

    if status_code == 404:
        return "not_found"

    if status_code is not None and status_code >= 500:
        return "broken_link"

    return "manual_check"


def make_result(
    record: Record,
    downloaded: int,
    status: str,
    source_url: str = "",
    local_path: str = "",
    http_status: Optional[int] = None,
) -> DownloadResult:
    """
    Build a DownloadResult object.
    """
    return DownloadResult(
        pdf_downloaded=downloaded,
        pdf_download_status=status,
        pdf_file_name=record.file_name,
        pdf_source_url=source_url,
        pdf_local_path=local_path,
        pdf_http_status=http_status,
        pdf_checked_at=now_str(),
    )


def try_download_from_url(
    url: str,
    session: requests.Session,
) -> Tuple[bool, str, Optional[int], Optional[bytes], str]:
    """
    Try to download a PDF starting from a candidate URL.
    Returns:
        (success, status_label, http_status, pdf_bytes, final_url)
    """
    try:
        resp = session.get(
            url,
            headers=HEADERS,
            timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            allow_redirects=True,
        )
        http_status = resp.status_code
        final_url = resp.url

        if http_status >= 400:
            if http_status == 403:
                return False, "paywalled", http_status, None, final_url
            if http_status == 404:
                return False, "not_found", http_status, None, final_url
            return False, "broken_link", http_status, None, final_url

        if response_looks_like_pdf(resp):
            return True, "downloaded", http_status, resp.content, final_url

        html = resp.text or ""
        pdf_url = extract_pdf_url_from_html(final_url, html)

        if pdf_url:
            pdf_resp = session.get(
                pdf_url,
                headers=HEADERS,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=True,
            )
            pdf_http_status = pdf_resp.status_code
            pdf_final_url = pdf_resp.url

            if pdf_http_status >= 400:
                if pdf_http_status == 403:
                    return False, "paywalled", pdf_http_status, None, pdf_final_url
                if pdf_http_status == 404:
                    return False, "not_found", pdf_http_status, None, pdf_final_url
                return False, "broken_link", pdf_http_status, None, pdf_final_url

            if response_looks_like_pdf(pdf_resp):
                return True, "downloaded", pdf_http_status, pdf_resp.content, pdf_final_url

            return False, "manual_check", pdf_http_status, None, pdf_final_url

        return False, classify_html_failure(http_status, html), http_status, None, final_url

    except requests.Timeout:
        return False, "broken_link", None, None, url
    except requests.RequestException:
        return False, "broken_link", None, None, url


def build_candidate_urls(record: Record) -> List[str]:
    """
    Build the ordered list of candidate URLs to test for a record.
    """
    urls: List[str] = []

    doi_link = str(record.doi_link_raw or "").strip()
    doi = normalize_doi(record.doi_raw)

    if doi_link:
        urls.append(doi_link)

    if doi:
        urls.append(make_doi_url(doi))

    return deduplicate_urls(urls)


def try_base_download(record: Record, session: requests.Session) -> DownloadResult:
    """
    Main phase-1 download logic for one record.
    """
    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            local_path=record.relative_path,
        )

    candidate_urls = build_candidate_urls(record)

    if not candidate_urls:
        return make_result(
            record=record,
            downloaded=0,
            status="invalid_doi",
        )

    final_status = "not_found"
    final_http_status: Optional[int] = None
    final_source_url = ""

    for url in candidate_urls:
        success, status_label, http_status, pdf_bytes, final_url = try_download_from_url(url, session)

        final_status = status_label
        final_http_status = http_status
        final_source_url = final_url or url

        if success and pdf_bytes:
            saved = save_pdf_bytes(record.pdf_path, pdf_bytes)
            if saved:
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded",
                    source_url=final_source_url,
                    local_path=record.relative_path,
                    http_status=http_status,
                )

            final_status = "manual_check"
            final_http_status = http_status
            final_source_url = final_url or url

    return make_result(
        record=record,
        downloaded=0,
        status=final_status,
        source_url=final_source_url,
        http_status=final_http_status,
    )


def process_record_phase1(record: Record) -> Tuple[Record, DownloadResult]:
    """
    Wrapper used by the executor in phase 1.
    """
    session = build_session()
    try:
        result = try_base_download(record, session)
        return record, result
    finally:
        session.close()
