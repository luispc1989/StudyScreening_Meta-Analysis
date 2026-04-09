from __future__ import annotations

import random
import re
import time
from typing import Optional
from urllib.parse import urljoin

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

try:
    import cloudscraper  # type: ignore
except Exception:
    cloudscraper = None

try:
    import pyautogui  # type: ignore
except Exception:
    pyautogui = None

from tools.pdf_fetcher.core.config import (
    ELSEVIER_ALLOWED_DOMAIN_PATTERN,
    ELSEVIER_ATTEMPT_TIMEOUT_MS,
    ELSEVIER_BROWSER_MODE,
    ELSEVIER_DOWNLOAD_TIMEOUT_MS,
    ELSEVIER_HEADLESS,
    ELSEVIER_NAVIGATION_TIMEOUT_MS,
    ELSEVIER_NETWORKIDLE_TIMEOUT_MS,
    ELSEVIER_POST_LOAD_WAIT_MS,
    ENABLE_ELSEVIER_RESOLVER,
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


def looks_like_pdf_url(url: str) -> bool:
    value = str(url or "").strip().lower()
    return (
        value.endswith(".pdf")
        or ".pdf?" in value
        or "/pdfft" in value
        or "pdf.sciencedirectassets.com" in value
    )


def is_pdf_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.identifier']",
        "meta[name='DC.Identifier']",
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
            pass

    if fallback_url:
        match = re.search(r"(10\.\d{4,9}/\S+)", fallback_url, re.I)
        if match:
            return match.group(1).rstrip(" .;,:)")

    raise RuntimeError("Could not detect DOI from the Elsevier page.")


def wait_for_page_ready(page, timeout_ms: int) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(ELSEVIER_POST_LOAD_WAIT_MS)


def _remaining_timeout_ms(deadline: float, fallback_ms: int) -> int:
    remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
    return min(fallback_ms, remaining_ms)


def auto_wait_for_article_ready(page, article_url: str, timeout_ms: int) -> None:
    page.wait_for_load_state("networkidle", timeout=timeout_ms)

    try:
        page.wait_for_selector('text="View PDF"', timeout=timeout_ms)
        return
    except PlaywrightTimeoutError:
        pass

    if page.locator('text="Are you a robot?"').count() > 0 and cloudscraper is not None:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            },
            delay=random.uniform(2, 5),
        )

        try:
            resp = scraper.get(article_url, timeout=30)
            if resp.status_code == 200:
                added_cookies = []
                for ck in resp.cookies:
                    added_cookies.append(
                        {
                            "name": ck.name,
                            "value": ck.value,
                            "domain": ck.domain or ".elsevier.com",
                            "path": ck.path or "/",
                            "expires": int(time.time() + 3600) if ck.expires is None else ck.expires,
                            "httpOnly": ck.has("httponly"),
                            "secure": ck.secure or False,
                        }
                    )
                if added_cookies:
                    page.context.add_cookies(added_cookies)
                page.reload()
                page.wait_for_selector('text="View PDF"', timeout=ELSEVIER_NAVIGATION_TIMEOUT_MS)
                return
        except Exception:
            pass

    if page.locator('text="Are you a robot?"').count() > 0 and pyautogui is not None:
        pyautogui.FAILSAFE = True
        pyautogui.click(600, 525)
        time.sleep(3)
        page.wait_for_selector('text="View PDF"', timeout=60000)
        return


def find_view_pdf_href(page) -> str | None:
    selectors = [
        "li#ViewPDF a[href*='/pdfft']",
        "li.ViewPDF a[href*='/pdfft']",
        "a[href*='/pdfft']",
        "a[aria-label*='View PDF']",
        "a:has-text('View PDF')",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                locator = page.locator(selector).nth(idx)
                href = locator.get_attribute("href")
                if href and looks_like_pdf_url(href):
                    return href
        except Exception:
            continue

    return None


def click_view_pdf(article_page):
    selectors = [
        "li#ViewPDF a",
        "li.ViewPDF a",
        "a[href*='/pdfft']",
        "a[aria-label*='View PDF']",
        "a:has-text('View PDF')",
    ]

    for selector in selectors:
        try:
            count = article_page.locator(selector).count()
            for idx in range(count):
                locator = article_page.locator(selector).nth(idx)
                try:
                    with article_page.expect_popup(timeout=15000) as popup_info:
                        locator.click()
                    popup = popup_info.value
                    wait_for_page_ready(popup, ELSEVIER_NETWORKIDLE_TIMEOUT_MS)
                    return popup
                except PlaywrightTimeoutError:
                    locator.click()
                    wait_for_page_ready(article_page, ELSEVIER_NETWORKIDLE_TIMEOUT_MS)
                    return article_page
        except Exception:
            continue

    raise RuntimeError("Could not trigger the Elsevier 'View PDF' button.")


def try_session_request_download(context, pdf_url: str, referer_url: str, output_file) -> tuple[bool, Optional[int], str]:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer_url},
        timeout=ELSEVIER_DOWNLOAD_TIMEOUT_MS,
    )

    if response.status != 200:
        return False, response.status, f"session_request_http_{response.status}: {pdf_url}"

    data = response.body()
    if not is_pdf_bytes(data):
        return False, response.status, f"session_request_not_pdf: {pdf_url}"

    output_file.write_bytes(data)
    return True, response.status, ""


def extract_pdf_url_from_viewer(page) -> str | None:
    current_url = page.url
    if looks_like_pdf_url(current_url):
        return current_url

    try:
        html = page.content()
        match = re.search(r"https://pdf\.sciencedirectassets\.com/[^\s\"']+", html, re.I)
        if match:
            return match.group(0)
    except Exception:
        pass

    selectors = [
        "embed[type='application/pdf']",
        "iframe[src*='.pdf']",
        "iframe[src*='pdf.sciencedirectassets.com']",
        "a[href*='.pdf']",
        "a[href*='pdf.sciencedirectassets.com']",
    ]
    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                src = page.locator(selector).nth(idx).get_attribute("src")
                href = page.locator(selector).nth(idx).get_attribute("href")
                candidate = src or href
                if candidate and looks_like_pdf_url(candidate):
                    return candidate
        except Exception:
            continue

    return None


def try_browser_download_from_viewer(page, output_file) -> bool:
    selectors = [
        "cr-icon-button#save",
        "#downloads cr-icon-button#save",
        "viewer-download-controls cr-icon-button#save",
    ]

    try:
        with page.expect_download(timeout=ELSEVIER_DOWNLOAD_TIMEOUT_MS) as download_info:
            for selector in selectors:
                try:
                    locator = page.locator(selector).first
                    if locator.count() == 0:
                        continue
                    locator.click()
                    break
                except Exception:
                    continue
        download = download_info.value
        download.save_as(str(output_file))
        return True
    except PlaywrightTimeoutError:
        return False
    except Exception:
        return False


def build_attempt_sequence(browser_mode: str, default_headless: bool) -> list[bool]:
    mode = str(browser_mode or "").strip().lower()
    if mode == "headless":
        return [True]
    if mode == "headed":
        return [False]
    if mode == "auto":
        return [True, False]
    return [default_headless]


def is_retryable_elsevier_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_elsevier",
        "download_failed_elsevier",
    }


def _run_elsevier_attempt(record: Record, start_url: str, headless: bool) -> DownloadResult:
    with sync_playwright() as playwright:
        deadline = time.monotonic() + (ELSEVIER_ATTEMPT_TIMEOUT_MS / 1000.0)
        browser = playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = context.new_page()
        page.set_default_timeout(min(ELSEVIER_ATTEMPT_TIMEOUT_MS, ELSEVIER_DOWNLOAD_TIMEOUT_MS))
        page.set_default_navigation_timeout(min(ELSEVIER_ATTEMPT_TIMEOUT_MS, ELSEVIER_NAVIGATION_TIMEOUT_MS))

        try:
            last_detail = ""
            page.goto(start_url, wait_until="domcontentloaded", timeout=_remaining_timeout_ms(deadline, ELSEVIER_NAVIGATION_TIMEOUT_MS))
            auto_wait_for_article_ready(page, start_url, _remaining_timeout_ms(deadline, ELSEVIER_NAVIGATION_TIMEOUT_MS))
            wait_for_page_ready(page, _remaining_timeout_ms(deadline, ELSEVIER_NETWORKIDLE_TIMEOUT_MS))

            final_page_url = page.url
            if not url_matches_domain_pattern(final_page_url, ELSEVIER_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record=record,
                    downloaded=0,
                    status="not_elsevier",
                    source_url=final_page_url,
                    detail=f"final_url_not_elsevier: {final_page_url}",
                )

            extract_doi_from_page(page, fallback_url=final_page_url)

            view_pdf_href = find_view_pdf_href(page)
            if view_pdf_href:
                pdf_view_url = urljoin(final_page_url, view_pdf_href)
                ok, http_status, detail = try_session_request_download(context, pdf_view_url, final_page_url, record.pdf_path)
                if ok:
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_elsevier",
                        source_url=pdf_view_url,
                        local_path=record.relative_path,
                        http_status=200,
                    )
                last_detail = detail

            viewer_page = click_view_pdf(page)
            direct_pdf_url = extract_pdf_url_from_viewer(viewer_page)
            if direct_pdf_url:
                ok, http_status, detail = try_session_request_download(context, direct_pdf_url, viewer_page.url, record.pdf_path)
                if ok:
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_elsevier",
                        source_url=direct_pdf_url,
                        local_path=record.relative_path,
                        http_status=200,
                    )
                last_detail = detail

            ok = try_browser_download_from_viewer(viewer_page, record.pdf_path)
            if ok and record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded_elsevier",
                    source_url=viewer_page.url,
                    local_path=record.relative_path,
                )
            last_detail = f"browser_download_failed_from_viewer: {viewer_page.url}"

            return make_result(
                record=record,
                downloaded=0,
                status="download_failed_elsevier",
                source_url=final_page_url,
                detail=last_detail or f"all_download_attempts_failed: {final_page_url}",
            )
        except RuntimeError as exc:
            return make_result(
                record=record,
                downloaded=0,
                status="pdf_link_not_found_elsevier",
                source_url=page.url,
                detail=str(exc).strip() or f"pdf_link_not_found: {page.url}",
            )
        finally:
            browser.close()


def try_elsevier_resolver(record: Record, source_url: str = "") -> DownloadResult:
    if not ENABLE_ELSEVIER_RESOLVER:
        return make_result(record, 0, "elsevier_resolver_disabled")

    doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw)
    if not doi:
        return make_result(record, 0, "invalid_doi")

    start_url = make_doi_url(doi)

    if record.pdf_path.exists() and record.pdf_path.stat().st_size > 0:
        return make_result(
            record=record,
            downloaded=1,
            status="duplicate_pdf",
            source_url=start_url,
            local_path=record.relative_path,
        )

    attempts = build_attempt_sequence(ELSEVIER_BROWSER_MODE, ELSEVIER_HEADLESS)
    last_result: DownloadResult | None = None

    for idx, headless in enumerate(attempts):
        result = _run_elsevier_attempt(record, start_url=start_url, headless=headless)
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_elsevier_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_elsevier", source_url=start_url)
