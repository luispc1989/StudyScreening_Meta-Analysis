
from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from tools.pdf_fetcher.core.config import (
    ENABLE_FRONTIERS_RESOLVER,
    FRONTIERS_ALLOWED_DOMAIN_PATTERN,
    FRONTIERS_BROWSER_MODE,
    FRONTIERS_DOWNLOAD_TIMEOUT_MS,
    FRONTIERS_HEADLESS,
    FRONTIERS_NAVIGATION_TIMEOUT_MS,
    FRONTIERS_NETWORKIDLE_TIMEOUT_MS,
    FRONTIERS_POST_LOAD_WAIT_MS,
)
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.utils import format_checked_at, make_doi_url, normalize_doi, save_pdf_bytes, url_matches_domain_pattern


def looks_like_pdf_url(href: str) -> bool:
    href_l = str(href or "").lower()
    return (
        "/pdf" in href_l
        or href_l.endswith(".pdf")
        or "download-a-pdf" in href_l
    )


def should_use_source_url_as_page(source_url: str) -> bool:
    url = str(source_url or "").strip().lower()
    if not url:
        return False
    if looks_like_pdf_url(url):
        return False
    if "public-pages-files-" in url:
        return False
    return True


def is_pdf_bytes_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def make_result(
    record: Record,
    downloaded: int,
    status: str,
    source_url: str = "",
    local_path: str = "",
    http_status: Optional[int] = None,
    detail: str = "",
) -> DownloadResult:
    return DownloadResult(
        pdf_downloaded=downloaded,
        pdf_download_status=status,
        pdf_file_name=record.file_name,
        pdf_source_url=source_url,
        pdf_local_path=local_path,
        pdf_http_status=http_status,
        pdf_checked_at=format_checked_at(detail),
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


def build_attempt_sequence(browser_mode: str, default_headless: bool) -> list[bool]:
    mode = str(browser_mode or "").strip().lower()
    if mode == "headless":
        return [True]
    if mode == "headed":
        return [False]
    if mode == "auto":
        return [True, False]
    return [default_headless]


def is_retryable_frontiers_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_frontiers",
        "download_failed_frontiers",
    }


def wait_for_article_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=FRONTIERS_NETWORKIDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        # Some publisher pages keep background requests alive; continue with the DOM we already have.
        pass
    page.wait_for_timeout(FRONTIERS_POST_LOAD_WAIT_MS)


def _run_frontiers_attempt(record: Record, start_url: str, doi_url: str, headless: bool) -> DownloadResult:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        try:
            last_detail = ""
            page.goto(
                start_url,
                wait_until="domcontentloaded",
                timeout=FRONTIERS_NAVIGATION_TIMEOUT_MS,
            )
            wait_for_article_page(page)

            final_page_url = page.url

            if not url_matches_domain_pattern(final_page_url, FRONTIERS_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_frontiers",
                    source_url=final_page_url,
                    detail=f"final_url_not_frontiers: {final_page_url}",
                )

            pdf_href = find_frontiers_pdf_href(page)
            extract_doi_from_page(page, fallback_url=final_page_url)

            if not pdf_href:
                return make_result(
                    record=record,
                    downloaded=0,
                    status="pdf_link_not_found_frontiers",
                    source_url=final_page_url,
                    detail=f"no_pdf_link_found_on_page: {final_page_url}",
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
                    last_detail = f"session_request_not_pdf: {pdf_url}"
                else:
                    last_detail = f"session_request_http_{response.status}: {pdf_url}"
            except Exception:
                last_detail = f"session_request_exception: {pdf_url}"

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
                    last_detail = f"browser_download_timeout: {selector}"
                    continue
                except Exception:
                    last_detail = f"browser_download_exception: {selector}"
                    continue

            return make_result(
                record=record,
                downloaded=0,
                status="download_failed_frontiers",
                source_url=final_page_url,
                detail=last_detail or f"all_download_attempts_failed: {final_page_url}",
            )

        finally:
            browser.close()


def try_frontiers_resolver(record: Record, source_url: str = "") -> DownloadResult:
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
    # Keep the active resolver as close as possible to the validated prototype:
    # always start from the DOI URL and let the publisher redirect to the article page.
    start_url = doi_url

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=start_url,
            local_path=record.relative_path,
        )

    attempts = build_attempt_sequence(FRONTIERS_BROWSER_MODE, FRONTIERS_HEADLESS)
    last_result: DownloadResult | None = None

    for idx, headless in enumerate(attempts):
        result = _run_frontiers_attempt(
            record,
            start_url=start_url,
            doi_url=doi_url,
            headless=headless,
        )
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_frontiers_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_frontiers", source_url=start_url)
