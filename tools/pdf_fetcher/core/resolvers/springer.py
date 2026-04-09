from __future__ import annotations

import re
import time
from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from tools.pdf_fetcher.core.config import (
    ENABLE_SPRINGER_RESOLVER,
    SPRINGER_ALLOWED_DOMAIN_PATTERN,
    SPRINGER_ATTEMPT_TIMEOUT_MS,
    SPRINGER_BROWSER_MODE,
    SPRINGER_DOWNLOAD_TIMEOUT_MS,
    SPRINGER_HEADLESS,
    SPRINGER_NAVIGATION_TIMEOUT_MS,
    SPRINGER_NETWORKIDLE_TIMEOUT_MS,
    SPRINGER_POST_LOAD_WAIT_MS,
)
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.utils import format_checked_at, make_doi_url, normalize_doi, save_pdf_bytes, url_matches_domain_pattern


def _remaining_timeout_ms(deadline: float, fallback_ms: int) -> int:
    remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
    return min(fallback_ms, remaining_ms)


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
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.Identifier']",
        "meta[name='DC.Identifier']",
        "meta[name='dc.identifier']",
        "meta[name='DC.identifier']",
        "meta[name='prism.doi']",
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
            continue

    for selector in ["a[href*='doi.org/']", "a[href*='dx.doi.org/']"]:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            href = locator.get_attribute("href")
            if not href:
                continue
            match = re.search(r"doi\.org/(10\.\d{4,9}/\S+)", href, re.I)
            if match:
                return match.group(1).rstrip(" .;,:)")
        except Exception:
            continue

    try:
        html = page.content()
        match = re.search(r"(10\.\d{4,9}/[^\s\"<>&]+)", html, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")
    except Exception:
        pass

    if fallback_url and "/article/" in fallback_url:
        return fallback_url.split("/article/", 1)[1].strip()

    raise RuntimeError("Could not detect DOI from the Springer page.")


def find_springer_pdf_href(page) -> Optional[str]:
    selectors = [
        "a[data-test='pdf-link']",
        "a[data-article-pdf='true']",
        "a.c-pdf-download__link",
        "a[href*='/content/pdf/']",
        "a:has-text('Download PDF')",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            href = locator.get_attribute("href")
            if href:
                return href
        except Exception:
            continue
    return None


def looks_like_springer_pdf_url(url: str) -> bool:
    value = str(url or "").strip().lower()
    return (
        "/content/pdf/" in value
        or value.endswith(".pdf")
        or ".pdf?" in value
    )


def should_use_source_url_as_page(source_url: str) -> bool:
    url = str(source_url or "").strip().lower()
    if not url:
        return False
    if looks_like_springer_pdf_url(url):
        return False
    return True


def build_attempt_sequence(browser_mode: str, default_headless: bool) -> list[bool]:
    mode = str(browser_mode or "").strip().lower()
    if mode == "headless":
        return [True]
    if mode == "headed":
        return [False]
    if mode == "auto":
        return [True, False]
    return [default_headless]


def is_retryable_springer_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_springer",
        "download_failed_springer",
    }


def wait_for_article_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=SPRINGER_NETWORKIDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(SPRINGER_POST_LOAD_WAIT_MS)


def _run_springer_attempt(record: Record, start_url: str, headless: bool) -> DownloadResult:
    with sync_playwright() as playwright:
        deadline = time.monotonic() + (SPRINGER_ATTEMPT_TIMEOUT_MS / 1000.0)
        browser = playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(min(SPRINGER_ATTEMPT_TIMEOUT_MS, SPRINGER_DOWNLOAD_TIMEOUT_MS))
        page.set_default_navigation_timeout(min(SPRINGER_ATTEMPT_TIMEOUT_MS, SPRINGER_NAVIGATION_TIMEOUT_MS))

        try:
            last_detail = ""
            page.goto(
                start_url,
                wait_until="domcontentloaded",
                timeout=_remaining_timeout_ms(deadline, SPRINGER_NAVIGATION_TIMEOUT_MS),
            )
            wait_for_article_page(page)

            final_page_url = page.url
            if not url_matches_domain_pattern(final_page_url, SPRINGER_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_springer",
                    source_url=final_page_url,
                    detail=f"final_url_not_springer: {final_page_url}",
                )

            extract_doi_from_page(page, fallback_url=final_page_url)
            pdf_href = find_springer_pdf_href(page)
            if not pdf_href:
                return make_result(
                    record=record,
                    downloaded=0,
                    status="pdf_link_not_found_springer",
                    source_url=final_page_url,
                    detail=f"no_pdf_link_found_on_page: {final_page_url}",
                )

            pdf_url = urljoin(final_page_url, pdf_href)

            try:
                response = context.request.get(
                    pdf_url,
                    headers={"Referer": final_page_url},
                    timeout=_remaining_timeout_ms(deadline, SPRINGER_DOWNLOAD_TIMEOUT_MS),
                )
                if response.status == 200:
                    data = response.body()
                    if data.startswith(b"%PDF") and save_pdf_bytes(record.pdf_path, data):
                        return make_result(
                            record=record,
                            downloaded=1,
                            status="downloaded_springer",
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
                "a[data-test='pdf-link']",
                "a[data-article-pdf='true']",
                "a.c-pdf-download__link",
                "a[href*='/content/pdf/']",
                "a:has-text('Download PDF')",
            ]
            for selector in selectors:
                if time.monotonic() >= deadline:
                    last_detail = f"attempt_timeout_before_browser_download: {final_page_url}"
                    break
                try:
                    locator = page.locator(selector).first
                    if locator.count() == 0:
                        continue
                    with page.expect_download(timeout=_remaining_timeout_ms(deadline, SPRINGER_DOWNLOAD_TIMEOUT_MS)) as download_info:
                        locator.click()
                    download = download_info.value
                    download.save_as(str(record.pdf_path))
                    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
                        return make_result(
                            record=record,
                            downloaded=1,
                            status="downloaded_springer",
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
                status="download_failed_springer",
                source_url=final_page_url,
                detail=last_detail or f"all_download_attempts_failed: {final_page_url}",
            )
        finally:
            browser.close()


def try_springer_resolver(record: Record, source_url: str = "") -> DownloadResult:
    if not ENABLE_SPRINGER_RESOLVER:
        return make_result(record, 0, "springer_resolver_disabled")

    doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw)
    if not doi:
        return make_result(record, 0, "invalid_doi")

    doi_url = make_doi_url(doi)
    # Keep the active resolver aligned with the validated prototype:
    # start from the DOI URL and let Springer resolve to the article page.
    start_url = doi_url

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=start_url,
            local_path=record.relative_path,
        )

    attempts = build_attempt_sequence(SPRINGER_BROWSER_MODE, SPRINGER_HEADLESS)
    last_result: DownloadResult | None = None

    for idx, headless in enumerate(attempts):
        result = _run_springer_attempt(record, start_url=start_url, headless=headless)
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_springer_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_springer", source_url=start_url)
