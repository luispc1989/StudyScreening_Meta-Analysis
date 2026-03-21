
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from app.config import (
    ENABLE_FRONTIERS_RESOLVER,
    FRONTIERS_ALLOWED_DOMAIN_PATTERN,
    FRONTIERS_DOWNLOAD_TIMEOUT_MS,
    FRONTIERS_HEADLESS,
    FRONTIERS_NAVIGATION_TIMEOUT_MS,
    FRONTIERS_POST_LOAD_WAIT_MS,
)
from app.models import DownloadResult, Record
from app.utils import make_doi_url, normalize_doi, now_str, save_pdf_bytes, url_matches_domain_pattern


def looks_like_pdf_url(href: str) -> bool:
    href_l = str(href or "").lower()
    return (
        "/pdf" in href_l
        or href_l.endswith(".pdf")
        or "download-a-pdf" in href_l
    )


def is_pdf_bytes_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def make_result(
    record: Record,
    downloaded: int,
    status: str,
    source_url: str = "",
    local_path: str = "",
    http_status: Optional[int] = None,
) -> DownloadResult:
    return DownloadResult(
        pdf_downloaded=downloaded,
        pdf_download_status=status,
        pdf_file_name=record.file_name,
        pdf_source_url=source_url,
        pdf_local_path=local_path,
        pdf_http_status=http_status,
        pdf_checked_at=now_str(),
    )


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
    """
    Try to extract a DOI from page metadata or HTML.
    """
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.Identifier']",
        "meta[name='DC.Identifier']",
        "meta[name='dc.identifier']",
        "meta[name='DC.identifier']",
        "meta[name='prism.doi']",
        "meta[property='og:doi']",
    ]

    for selector in meta_selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                content = locator.get_attribute("content")
                if content:
                    match = re.search(r"(10\.\d{4,9}/\S+)", content.strip(), re.I)
                    if match:
                        return match.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    doi_link_selectors = [
        "a[href*='doi.org/']",
        "a[href*='dx.doi.org/']",
    ]

    for selector in doi_link_selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if not href:
                    continue
                match = re.search(r"doi\.org/(10\.\d{4,9}/\S+)", href, re.I)
                if match:
                    return match.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    try:
        html = page.content()
        match = re.search(r"(10\.\d{4,9}/[^\s\"<>&]+)", html, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")
    except Exception:
        pass

    if fallback_url:
        match = re.search(r"(10\.\d{4,9}/\S+)", fallback_url, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")

    raise RuntimeError("Could not detect DOI from Frontiers page.")


def find_frontiers_pdf_href(page) -> Optional[str]:
    """
    Try to find a usable PDF href on the Frontiers page.
    """
    selectors = [
        "a[data-event='download-a-pdf']",
        "a.DownloadArticleButton_action",
        "a[href*='/pdf']",
        "a[href$='.pdf']",
        "li.ToolbarDownload a",
        "a.ToolbarDownload_action",
        "nav.Toolbar a[data-event='download-a-pdf']",
        "a:has-text('PDF')",
        "a:has-text('Download')",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if href and looks_like_pdf_url(href):
                    return href
        except Exception:
            pass

    return None


def try_frontiers_resolver(record: Record) -> DownloadResult:
    """
    Specialized resolver for Frontiers.
    """
    if not ENABLE_FRONTIERS_RESOLVER:
        return make_result(
            record=record,
            downloaded=0,
            status="frontiers_resolver_disabled",
        )

    doi = normalize_doi(record.doi_raw)
    if not doi:
        doi = normalize_doi(record.doi_link_raw)

    if not doi:
        return make_result(
            record=record,
            downloaded=0,
            status="invalid_doi",
        )

    doi_url = make_doi_url(doi)

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=doi_url,
            local_path=record.relative_path,
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=FRONTIERS_HEADLESS,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            page.goto(
                doi_url,
                wait_until="domcontentloaded",
                timeout=FRONTIERS_NAVIGATION_TIMEOUT_MS,
            )
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(FRONTIERS_POST_LOAD_WAIT_MS)

            final_page_url = page.url

            if not url_matches_domain_pattern(final_page_url, FRONTIERS_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_frontiers",
                    source_url=final_page_url,
                )

            pdf_href = find_frontiers_pdf_href(page)
            _detected_doi = extract_doi_from_page(page, fallback_url=final_page_url)

            if not pdf_href:
                return make_result(
                    record=record,
                    downloaded=0,
                    status="pdf_link_not_found_frontiers",
                    source_url=final_page_url,
                )

            pdf_url = urljoin(final_page_url, pdf_href)

            try:
                response = context.request.get(
                    pdf_url,
                    headers={"Referer": final_page_url},
                    timeout=FRONTIERS_DOWNLOAD_TIMEOUT_MS,
                )

                if response.status == 200:
                    data = response.body()
                    if is_pdf_bytes_bytes(data):
                        if save_pdf_bytes(record.pdf_path, data):
                            return make_result(
                                record=record,
                                downloaded=1,
                                status="downloaded_frontiers",
                                source_url=pdf_url,
                                local_path=record.relative_path,
                                http_status=response.status,
                            )
            except Exception:
                pass

            selectors = [
                "a[data-event='download-a-pdf']",
                "a.DownloadArticleButton_action",
                "a[href*='/pdf']",
                "a[href$='.pdf']",
                "li.ToolbarDownload a",
                "a.ToolbarDownload_action",
                "nav.Toolbar a[data-event='download-a-pdf']",
                "a:has-text('PDF')",
                "a:has-text('Download')",
            ]

            for selector in selectors:
                try:
                    count = page.locator(selector).count()
                    for idx in range(count):
                        locator = page.locator(selector).nth(idx)
                        href = locator.get_attribute("href")
                        if not href or not looks_like_pdf_url(href):
                            continue

                        with page.expect_download(timeout=FRONTIERS_DOWNLOAD_TIMEOUT_MS) as download_info:
                            locator.click()

                        download = download_info.value
                        download.save_as(str(record.pdf_path))

                        if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
                            return make_result(
                                record=record,
                                downloaded=1,
                                status="downloaded_frontiers",
                                source_url=pdf_url,
                                local_path=record.relative_path,
                            )
                except PlaywrightTimeoutError:
                    continue
                except Exception:
                    continue

            return make_result(
                record=record,
                downloaded=0,
                status="download_failed_frontiers",
                source_url=final_page_url,
            )

        finally:
            browser.close()