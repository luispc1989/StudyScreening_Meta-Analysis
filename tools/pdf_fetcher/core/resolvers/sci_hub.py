from __future__ import annotations

import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from tools.pdf_fetcher.core.config import (
    ENABLE_SCI_HUB_RESOLVER,
    SCI_HUB_ATTEMPT_TIMEOUT_MS,
    SCI_HUB_BROWSER_MODE,
    SCI_HUB_DOMAINS,
    SCI_HUB_DOWNLOAD_TIMEOUT_MS,
    SCI_HUB_HEADLESS,
    SCI_HUB_NAVIGATION_TIMEOUT_MS,
    SCI_HUB_NETWORKIDLE_TIMEOUT_MS,
    SCI_HUB_POST_LOAD_WAIT_MS,
)
from tools.pdf_fetcher.core.models import DownloadResult, Record
from tools.pdf_fetcher.core.utils import format_checked_at, normalize_doi, save_pdf_bytes


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


def build_sci_hub_url(doi: str) -> str:
    if not doi:
        raise ValueError("DOI is required.")
    base = SCI_HUB_DOMAINS[0].rstrip("/")
    return f"{base}/{doi}"


def build_sci_hub_urls(doi: str) -> list[str]:
    if not doi:
        raise ValueError("DOI is required.")

    urls: list[str] = []
    seen: set[str] = set()
    for domain in SCI_HUB_DOMAINS:
        base = str(domain or "").strip().rstrip("/")
        if not base:
            continue
        url = f"{base}/{doi}"
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def extract_pdf_url(page) -> Optional[str]:
    selectors = [
        "iframe[src*='.pdf']",
        "embed[src*='.pdf']",
        "a[href*='.pdf']",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                element = page.locator(selector).nth(idx)
                href = element.get_attribute("src") or element.get_attribute("href")
                if href and ".pdf" in href.lower():
                    return href
        except Exception:
            continue

    try:
        html = page.content()
        match = re.search(r'"([^"\']+\.pdf(?:\?[^"\']*)?)"', html, flags=re.I)
        if match:
            return match.group(1)
    except Exception:
        pass

    return None


def try_session_request_download(context, pdf_url: str, referer_url: str, output_path) -> tuple[bool, Optional[int], str]:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer_url},
        timeout=SCI_HUB_DOWNLOAD_TIMEOUT_MS,
    )

    if response.status != 200:
        return False, response.status, f"session_request_http_{response.status}: {pdf_url}"

    data = response.body()
    if not data.startswith(b"%PDF"):
        return False, response.status, f"session_request_not_pdf: {pdf_url}"

    saved = save_pdf_bytes(output_path, data)
    if not saved:
        return False, response.status, f"session_request_save_failed: {pdf_url}"

    return True, response.status, pdf_url


def try_browser_download(page, output_path) -> bool:
    selectors = [
        "a[href*='.pdf']",
        "button:has-text('Download')",
        "button:has-text('PDF')",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                locator = page.locator(selector).nth(idx)
                with page.expect_download(timeout=SCI_HUB_DOWNLOAD_TIMEOUT_MS) as download_info:
                    locator.click()
                download = download_info.value
                download.save_as(str(output_path))
                return output_path.exists() and output_path.stat().st_size > 0
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue

    return False


def wait_for_page_ready(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=SCI_HUB_NETWORKIDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(SCI_HUB_POST_LOAD_WAIT_MS)


def wait_for_pdf_surface(page) -> None:
    selectors = [
        "iframe[src*='.pdf']",
        "embed[src*='.pdf']",
        "a[href*='.pdf']",
        "textarea#request",
        "input[name='request']",
    ]

    for _ in range(20):
        if detect_missing_in_sci_hub_database(page):
            return

        for selector in selectors:
            try:
                if page.locator(selector).count() > 0 and page.locator(selector).first.is_visible():
                    return
            except Exception:
                continue

        page.wait_for_timeout(250)


def open_sci_hub_page(page, doi: str, timeout_ms: int = SCI_HUB_NAVIGATION_TIMEOUT_MS) -> str:
    attempt_errors: list[str] = []
    for candidate_url in build_sci_hub_urls(doi):
        try:
            page.goto(candidate_url, wait_until="domcontentloaded", timeout=timeout_ms)
            wait_for_page_ready(page)
            wait_for_pdf_surface(page)
            return candidate_url
        except Exception as exc:
            attempt_errors.append(f"{candidate_url} -> {type(exc).__name__}: {exc}")
            continue

    detail = " | ".join(attempt_errors) if attempt_errors else "no_domains_configured"
    raise RuntimeError(f"all_sci_hub_domains_failed: {detail}")


def fill_sci_hub_search(page, doi: str, timeout_ms: int = SCI_HUB_NAVIGATION_TIMEOUT_MS) -> bool:
    seen: set[str] = set()
    for domain in SCI_HUB_DOMAINS:
        base_url = str(domain or "").strip().rstrip("/") + "/"
        if base_url == "/" or base_url in seen:
            continue
        seen.add(base_url)

        try:
            page.goto(base_url, wait_until="domcontentloaded", timeout=timeout_ms)
            wait_for_page_ready(page)
        except Exception:
            continue

        try:
            if page.locator("textarea#request").count() > 0:
                page.fill("textarea#request", doi)
            elif page.locator("input[name='request']").count() > 0:
                page.fill("input[name='request']", doi)
            else:
                continue

            if page.locator("button[type='submit']").count() > 0:
                page.click("button[type='submit']")
            else:
                page.keyboard.press("Enter")

            wait_for_page_ready(page)
            wait_for_pdf_surface(page)
            return True
        except Exception:
            continue

    return False


def try_extract_and_download_from_current_page(page, context, record: Record) -> Optional[DownloadResult]:
    if detect_missing_in_sci_hub_database(page):
        return make_result(
            record,
            0,
            "pdf_link_not_found_sci_hub",
            source_url=page.url,
            detail="article_not_available_in_sci_hub_database",
        )

    if page.url.lower().endswith(".pdf"):
        ok, http_status, source_url = try_session_request_download(context, page.url, page.url, record.pdf_path)
        if ok:
            return make_result(record, 1, "downloaded_sci_hub", source_url=source_url, local_path=record.relative_path, http_status=http_status)

    pdf_href = extract_pdf_url(page)
    if pdf_href:
        pdf_url = urljoin(page.url, pdf_href)
        ok, http_status, source_url = try_session_request_download(context, pdf_url, page.url, record.pdf_path)
        if ok:
            return make_result(record, 1, "downloaded_sci_hub", source_url=source_url, local_path=record.relative_path, http_status=http_status)

    if try_browser_download(page, record.pdf_path):
        return make_result(record, 1, "downloaded_sci_hub", source_url=page.url, local_path=record.relative_path)

    return None


def detect_missing_in_sci_hub_database(page) -> bool:
    try:
        content = page.content().lower()
    except Exception:
        return False

    exact_markers = [
        "infelizmente, o seguinte artigo ainda não está disponível no meu banco de dados:",
        "infelizmente, o seguinte artigo ainda nao esta disponivel no meu banco de dados:",
        "não tenho nenhum artigo correspondente à sua solicitação",
        "nao tenho nenhum artigo correspondente a sua solicitacao",
        "não tenho nenhum artigo correspondente à sua solicitação :(",
        "nao tenho nenhum artigo correspondente a sua solicitacao :(",
    ]
    if any(marker in content for marker in exact_markers):
        return True

    phrases = [
        "não está disponível no meu banco de dados",
        "nao esta disponivel no meu banco de dados",
        "not available in my database",
        "article is not available",
        "following article is not available",
    ]
    return any(phrase in content for phrase in phrases)


def build_attempt_sequence(browser_mode: str, default_headless: bool) -> list[bool]:
    mode = str(browser_mode or "").strip().lower()
    if mode == "headless":
        return [True]
    if mode == "headed":
        return [False]
    if mode == "auto":
        return [True, False]
    return [default_headless]


def is_retryable_sci_hub_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_sci_hub",
        "download_failed_sci_hub",
    }


def _run_sci_hub_attempt(record: Record, doi: str, headless: bool) -> DownloadResult:
    with sync_playwright() as playwright:
        deadline = time.monotonic() + (SCI_HUB_ATTEMPT_TIMEOUT_MS / 1000.0)
        browser = playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(min(SCI_HUB_ATTEMPT_TIMEOUT_MS, SCI_HUB_DOWNLOAD_TIMEOUT_MS))
        page.set_default_navigation_timeout(min(SCI_HUB_ATTEMPT_TIMEOUT_MS, SCI_HUB_NAVIGATION_TIMEOUT_MS))

        try:
            start_url = ""
            if time.monotonic() >= deadline:
                return make_result(
                    record,
                    0,
                    "download_failed_sci_hub",
                    source_url="",
                    detail="attempt_timeout_before_start",
                )

            start_url = open_sci_hub_page(page, doi, timeout_ms=_remaining_timeout_ms(deadline, SCI_HUB_NAVIGATION_TIMEOUT_MS))
            result = try_extract_and_download_from_current_page(page, context, record)
            if result:
                return result

            if time.monotonic() >= deadline:
                return make_result(
                    record,
                    0,
                    "download_failed_sci_hub",
                    source_url=page.url or start_url,
                    detail="attempt_timeout_after_direct_open",
                )

            searched = fill_sci_hub_search(page, doi, timeout_ms=_remaining_timeout_ms(deadline, SCI_HUB_NAVIGATION_TIMEOUT_MS))
            if searched:
                result = try_extract_and_download_from_current_page(page, context, record)
                if result:
                    return result

            return make_result(
                record,
                0,
                "pdf_link_not_found_sci_hub",
                source_url=page.url or start_url,
                detail="no_pdf_link_found_after_search_and_direct_flows",
            )
        except RuntimeError as exc:
            return make_result(
                record,
                0,
                "download_failed_sci_hub",
                source_url="",
                detail=str(exc).strip(),
            )
        finally:
            browser.close()


def try_sci_hub_resolver(record: Record, source_url: str = "") -> DownloadResult:
    if not ENABLE_SCI_HUB_RESOLVER:
        return make_result(record, 0, "sci_hub_resolver_disabled")

    doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw)
    if not doi:
        return make_result(record, 0, "invalid_doi")

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=build_sci_hub_url(doi),
            local_path=record.relative_path,
        )

    attempts = build_attempt_sequence(SCI_HUB_BROWSER_MODE, SCI_HUB_HEADLESS)
    last_result: Optional[DownloadResult] = None

    for idx, headless in enumerate(attempts):
        result = _run_sci_hub_attempt(record, doi, headless)
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_sci_hub_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_sci_hub", source_url=build_sci_hub_url(doi))
