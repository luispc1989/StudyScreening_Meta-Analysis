from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from tools.pdf_fetcher.core.config import (
    ENABLE_MDPI_RESOLVER,
    MDPI_ALLOWED_DOMAIN_PATTERN,
    MDPI_BROWSER_MODE,
    MDPI_DOWNLOAD_TIMEOUT_MS,
    MDPI_HEADLESS,
    MDPI_NAVIGATION_TIMEOUT_MS,
    MDPI_NETWORKIDLE_TIMEOUT_MS,
    MDPI_POST_LOAD_WAIT_MS,
)
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.utils import format_checked_at, make_doi_url, normalize_doi, save_pdf_bytes, url_matches_domain_pattern


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


def looks_like_pdf_href(href: str) -> bool:
    href_l = str(href or "").lower()
    return ".pdf" in href_l or "/pdf" in href_l or "download pdf" in href_l


def open_download_menu_if_present(page) -> None:
    selectors = [
        "div.download a.button--drop-down",
        "a.button--drop-down",
        "button:has-text('Download')",
        "a:has-text('Download')",
        "text=Download",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            locator.click(timeout=3000)
            page.wait_for_timeout(1200)
            return
        except Exception:
            continue


def find_mdpi_pdf_locator(page):
    selectors = [
        "a.UD_ArticlePDF",
        "a[data-name*='Download PDF']",
        "a[href*='/pdf?version=']",
        "a[href$='/pdf']",
        "a:has-text('Download PDF')",
        "a:has-text('PDF')",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0:
                return locator
        except Exception:
            continue
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


def is_retryable_mdpi_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_mdpi",
        "download_failed_mdpi",
    }


def wait_for_article_page(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=MDPI_NETWORKIDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(MDPI_POST_LOAD_WAIT_MS)


def _run_mdpi_attempt(record: Record, start_url: str, headless: bool) -> DownloadResult:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
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
                timeout=MDPI_NAVIGATION_TIMEOUT_MS,
            )
            wait_for_article_page(page)

            final_page_url = page.url
            if not url_matches_domain_pattern(final_page_url, MDPI_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_mdpi",
                    source_url=final_page_url,
                    detail=f"final_url_not_mdpi: {final_page_url}",
                )

            open_download_menu_if_present(page)
            pdf_locator = find_mdpi_pdf_locator(page)
            if pdf_locator is None:
                return make_result(
                    record=record,
                    downloaded=0,
                    status="pdf_link_not_found_mdpi",
                    source_url=final_page_url,
                    detail=f"no_pdf_link_found_on_page: {final_page_url}",
                )

            try:
                href = pdf_locator.get_attribute("href")
            except Exception:
                href = None

            if href:
                pdf_url = urljoin(final_page_url, href)
                try:
                    response = context.request.get(
                        pdf_url,
                        headers={"Referer": final_page_url},
                        timeout=MDPI_DOWNLOAD_TIMEOUT_MS,
                    )
                    if response.status == 200:
                        data = response.body()
                        if data.startswith(b"%PDF") and save_pdf_bytes(record.pdf_path, data):
                            return make_result(
                                record=record,
                                downloaded=1,
                                status="downloaded_mdpi",
                                source_url=pdf_url,
                                local_path=record.relative_path,
                                http_status=response.status,
                            )
                        last_detail = f"session_request_not_pdf: {pdf_url}"
                    else:
                        last_detail = f"session_request_http_{response.status}: {pdf_url}"
                except Exception:
                    last_detail = f"session_request_exception: {pdf_url}"

            try:
                with page.expect_download(timeout=MDPI_DOWNLOAD_TIMEOUT_MS) as download_info:
                    pdf_locator.click()
                download = download_info.value
                download.save_as(str(record.pdf_path))
                if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_mdpi",
                        source_url=final_page_url,
                        local_path=record.relative_path,
                    )
            except PlaywrightTimeoutError:
                last_detail = "browser_download_timeout"
            except Exception:
                last_detail = "browser_download_exception"

            return make_result(
                record=record,
                downloaded=0,
                status="download_failed_mdpi",
                source_url=final_page_url,
                detail=last_detail or f"all_download_attempts_failed: {final_page_url}",
            )
        finally:
            browser.close()


def try_mdpi_resolver(record: Record, source_url: str = "") -> DownloadResult:
    if not ENABLE_MDPI_RESOLVER:
        return make_result(record, 0, "mdpi_resolver_disabled")

    doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw)
    if not doi:
        return make_result(record, 0, "invalid_doi")

    doi_url = make_doi_url(doi)
    start_url = source_url or doi_url

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=doi_url,
            local_path=record.relative_path,
        )

    attempts = build_attempt_sequence(MDPI_BROWSER_MODE, MDPI_HEADLESS)
    last_result: DownloadResult | None = None

    for idx, headless in enumerate(attempts):
        result = _run_mdpi_attempt(record, start_url=start_url, headless=headless)
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_mdpi_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_mdpi", source_url=start_url)
