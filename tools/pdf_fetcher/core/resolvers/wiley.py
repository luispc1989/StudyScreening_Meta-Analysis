from __future__ import annotations

import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

from tools.pdf_fetcher.core.config import (
    ENABLE_WILEY_RESOLVER,
    WILEY_ALLOWED_DOMAIN_PATTERN,
    WILEY_ATTEMPT_TIMEOUT_MS,
    WILEY_BROWSER_MODE,
    WILEY_DOWNLOAD_TIMEOUT_MS,
    WILEY_HEADLESS,
    WILEY_NAVIGATION_TIMEOUT_MS,
    WILEY_NETWORKIDLE_TIMEOUT_MS,
    WILEY_POST_LOAD_WAIT_MS,
    WILEY_VIEWER_DOWNLOAD_TIMEOUT_MS,
    WILEY_VIEWER_READY_TIMEOUT_MS,
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


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
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
            continue

    for selector in ["a[href*='doi.org/']", "a[href*='dx.doi.org/']"]:
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
            continue

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

    raise RuntimeError("Could not detect DOI from the Wiley page.")


def is_pdf_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def looks_like_pdf_url(href: str) -> bool:
    href_l = str(href or "").lower()
    return any(
        marker in href_l
        for marker in ("/doi/pdf", "/doi/epdf", "pdfdirect", "asset/pdf", ".pdf")
    )


def build_pdf_variants(href_or_url: str, base_url: str) -> list[str]:
    absolute = urljoin(base_url, href_or_url)
    variants = [absolute]

    path = urlparse(absolute).path
    query = urlparse(absolute).query

    if "/doi/pdf/" in path:
        variants.append(absolute.replace("/doi/pdf/", "/doi/pdfdirect/", 1))
    if "/doi/epdf/" in path:
        variants.append(absolute.replace("/doi/epdf/", "/doi/pdfdirect/", 1))
        variants.append(absolute.replace("/doi/epdf/", "/doi/pdf/", 1))

    base_no_query = absolute.split("?", 1)[0]
    variants.append(f"{base_no_query}?download=true")
    variants.append(f"{base_no_query}?download=1")
    if query:
        variants.append(absolute)

    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        deduped.append(variant)
    return deduped


def build_wiley_html_viewer_url(href_or_url: str, base_url: str) -> str:
    absolute = urljoin(base_url, href_or_url)
    path = urlparse(absolute).path

    if "/doi/pdf/" in path:
        file_path = path.replace("/doi/pdf/", "/doi/pdfdirect/", 1)
    elif "/doi/epdf/" in path:
        file_path = path.replace("/doi/epdf/", "/doi/pdfdirect/", 1)
    else:
        file_path = path

    return urljoin(
        base_url,
        f"/templates/jsp/_ux3/_acropolis/_pericles/pdf-viewer/web/viewer.html?file={file_path}",
    )


def dismiss_cookie_banner(page) -> None:
    selectors = [
        "button:has-text('Aceitar tudo')",
        "button:has-text('Accept all')",
        "button:has-text('I agree')",
        "button#onetrust-accept-btn-handler",
        "button[aria-label*='Accept']",
    ]
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if locator.count() > 0 and locator.is_visible():
                locator.click(timeout=3000)
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


def collect_pdf_candidates(page) -> list[str]:
    selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdf']",
        "a[href*='/doi/epdf']",
        "a[href*='/doi/pdfdirect']",
        "a[href*='pdfdirect']",
        "a.article-pdfLink",
        "a.pdf-download",
        "a:has-text('PDF')",
        "a:has-text('Full Text PDF')",
        "a:has-text('Download PDF')",
    ]

    candidates: list[str] = []
    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if href and looks_like_pdf_url(href):
                    candidates.append(href)
        except Exception:
            continue

    try:
        html = page.content()
        candidates.extend(
            re.findall(r"""["']([^"']*(?:/doi/(?:pdf|epdf)|pdfdirect|asset/pdf)[^"']*)["']""", html, flags=re.I)
        )
    except Exception:
        pass

    deduped: list[str] = []
    seen: set[str] = set()
    for href in candidates:
        if href in seen:
            continue
        seen.add(href)
        deduped.append(href)
    return deduped


def collect_viewer_pdf_candidates(page) -> list[str]:
    candidates: list[str] = []
    selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdfdirect/']",
        "a.btn-cta[href*='/doi/pdfdirect/']",
        "a[data-download-files-key='pdf']",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                href = page.locator(selector).nth(idx).get_attribute("href")
                if href:
                    candidates.append(href)
        except Exception:
            continue

    try:
        current_url = page.url
        if looks_like_pdf_url(current_url):
            candidates.append(current_url)
    except Exception:
        pass

    try:
        html = page.content()
        candidates.extend(
            re.findall(r"""["']([^"']*(?:/doi/(?:pdf|epdf|pdfdirect)|pdfdirect|asset/pdf|\.pdf)[^"']*)["']""", html, flags=re.I)
        )
    except Exception:
        pass

    try:
        js_candidates = page.evaluate(
            """
            () => {
                const values = [];
                const selectors = ['embed', 'iframe', 'object', 'a[href]'];
                for (const selector of selectors) {
                    for (const el of document.querySelectorAll(selector)) {
                        const src = el.getAttribute('src') || el.getAttribute('data') || el.getAttribute('href');
                        if (src) values.push(src);
                    }
                }
                return values;
            }
            """
        )
        if js_candidates:
            candidates.extend(js_candidates)
    except Exception:
        pass

    deduped: list[str] = []
    seen: set[str] = set()
    for href in candidates:
        if not href or not looks_like_pdf_url(href) or href in seen:
            continue
        seen.add(href)
        deduped.append(href)
    return deduped


def try_session_request_download(
    context,
    pdf_url: str,
    referer_url: str,
    output_path,
    timeout_ms: int = WILEY_DOWNLOAD_TIMEOUT_MS,
) -> tuple[bool, Optional[int], str]:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer_url},
        timeout=timeout_ms,
    )

    if response.status != 200:
        return False, response.status, f"session_request_http_{response.status}: {pdf_url}"

    data = response.body()
    if not is_pdf_bytes(data):
        return False, response.status, f"session_request_not_pdf: {pdf_url}"

    saved = save_pdf_bytes(output_path, data)
    if not saved:
        return False, response.status, f"session_request_save_failed: {pdf_url}"
    return True, response.status, ""


def wait_for_page_ready(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=WILEY_NETWORKIDLE_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(WILEY_POST_LOAD_WAIT_MS)


def _remaining_timeout_ms(deadline: float, fallback_ms: int) -> int:
    remaining_ms = max(1000, int((deadline - time.monotonic()) * 1000))
    return min(fallback_ms, remaining_ms)


def wait_for_wiley_viewer(page) -> bool:
    try:
        body_text = page.locator("body").inner_text(timeout=1500).lower()
        if "0 de 0" in body_text or "0 of 0" in body_text:
            return False
    except Exception:
        pass

    selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdfdirect/']",
        "a.btn-cta",
        "#simpleViewer",
        ".viewer-pdf",
        "embed[type='application/pdf']",
        "iframe[src*='pdf']",
    ]
    for selector in selectors:
        try:
            page.locator(selector).first.wait_for(state="visible", timeout=WILEY_VIEWER_READY_TIMEOUT_MS)
            try:
                body_text = page.locator("body").inner_text(timeout=1000).lower()
                if "0 de 0" in body_text or "0 of 0" in body_text:
                    return False
            except Exception:
                pass
            return True
        except Exception:
            continue

    try:
        body_text = page.locator("body").inner_text(timeout=3000).lower()
        if "0 de 0" in body_text or "0 of 0" in body_text:
            return False
    except Exception:
        pass

    return False


def open_pdf_viewer(page, candidate_hrefs: list[str], base_url: str, deadline: float | None = None) -> bool:
    for href in candidate_hrefs:
        viewer_url = build_wiley_html_viewer_url(href, base_url)
        try:
            timeout_ms = WILEY_NAVIGATION_TIMEOUT_MS
            if deadline is not None:
                timeout_ms = _remaining_timeout_ms(deadline, WILEY_NAVIGATION_TIMEOUT_MS)
            page.goto(viewer_url, wait_until="domcontentloaded", timeout=timeout_ms)
            wait_for_page_ready(page)
            body_text = page.locator("body").inner_text(timeout=3000).lower()
            if "request username" in body_text:
                continue
            if not wait_for_wiley_viewer(page):
                continue
            return True
        except Exception:
            continue
    return False


def try_wiley_html_viewer_download(page, output_path) -> bool:
    selectors = [
        "a[aria-label='Download PDF']",
        "a.btn-cta[href*='/doi/pdfdirect/']",
        "a[href*='/doi/pdfdirect/'][data-download-file='true']",
        "a[href*='/doi/pdfdirect/']",
    ]

    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                locator = page.locator(selector).nth(idx)
                with page.expect_download(timeout=WILEY_VIEWER_DOWNLOAD_TIMEOUT_MS) as download_info:
                    locator.click(timeout=10000)
                download = download_info.value
                download.save_as(str(output_path))
                if output_path.exists() and output_path.stat().st_size > 0:
                    return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue
    return False


def try_pdf_viewer_save_download(page, output_path) -> bool:
    selectors = [
        "cr-icon-button#save",
        "#downloads cr-icon-button#save",
        "viewer-download-controls cr-icon-button#save",
    ]

    try:
        with page.expect_download(timeout=WILEY_VIEWER_DOWNLOAD_TIMEOUT_MS) as download_info:
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
        download.save_as(str(output_path))
        return output_path.exists() and output_path.stat().st_size > 0
    except PlaywrightTimeoutError:
        return False
    except Exception:
        return False


def try_viewer_sources_download(page, context, output_path, timeout_ms: int = WILEY_DOWNLOAD_TIMEOUT_MS) -> tuple[bool, Optional[int], str]:
    base_url = f"{urlparse(page.url).scheme}://{urlparse(page.url).netloc}"
    viewer_candidates = collect_viewer_pdf_candidates(page)
    for candidate in viewer_candidates:
        for pdf_url in build_pdf_variants(candidate, base_url):
            ok, http_status, _detail = try_session_request_download(
                context,
                pdf_url,
                page.url,
                output_path,
                timeout_ms=timeout_ms,
            )
            if ok:
                return True, http_status, pdf_url
    return False, None, f"viewer_source_request_failed: {page.url}"


def try_browser_download(page, output_path, timeout_ms: int = WILEY_VIEWER_DOWNLOAD_TIMEOUT_MS) -> bool:
    selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdf']",
        "a[href*='/doi/epdf']",
        "a[href*='/doi/pdfdirect']",
        "a[href*='pdfdirect']",
        "a.article-pdfLink",
        "a.pdf-download",
        "a:has-text('Full Text PDF')",
        "a:has-text('Download PDF')",
    ]
    for selector in selectors:
        try:
            count = page.locator(selector).count()
            for idx in range(count):
                locator = page.locator(selector).nth(idx)
                with page.expect_download(timeout=timeout_ms) as download_info:
                    locator.click()
                download = download_info.value
                download.save_as(str(output_path))
                if output_path.exists() and output_path.stat().st_size > 0:
                    return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue
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


def is_retryable_wiley_status(status: str) -> bool:
    return status in {
        "pdf_link_not_found_wiley",
        "download_failed_wiley",
    }


def _run_wiley_attempt(record: Record, start_url: str, headless: bool) -> DownloadResult:
    with sync_playwright() as playwright:
        deadline = time.monotonic() + (WILEY_ATTEMPT_TIMEOUT_MS / 1000.0)
        browser = playwright.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(min(WILEY_ATTEMPT_TIMEOUT_MS, WILEY_DOWNLOAD_TIMEOUT_MS))
        page.set_default_navigation_timeout(min(WILEY_ATTEMPT_TIMEOUT_MS, WILEY_NAVIGATION_TIMEOUT_MS))

        try:
            last_detail = ""
            page.goto(
                start_url,
                wait_until="domcontentloaded",
                timeout=_remaining_timeout_ms(deadline, WILEY_NAVIGATION_TIMEOUT_MS),
            )
            wait_for_page_ready(page)
            dismiss_cookie_banner(page)

            final_page_url = page.url
            if not url_matches_domain_pattern(final_page_url, WILEY_ALLOWED_DOMAIN_PATTERN):
                return make_result(
                    record,
                    0,
                    "not_wiley",
                    source_url=final_page_url,
                    detail=f"final_url_not_wiley: {final_page_url}",
                )

            extract_doi_from_page(page, fallback_url=final_page_url)
            base_url = f"{urlparse(final_page_url).scheme}://{urlparse(final_page_url).netloc}"
            pdf_candidates = collect_pdf_candidates(page)
            if not pdf_candidates:
                return make_result(
                    record,
                    0,
                    "pdf_link_not_found_wiley",
                    source_url=final_page_url,
                    detail=f"no_pdf_link_found_on_page: {final_page_url}",
                )

            for href in pdf_candidates:
                if time.monotonic() >= deadline:
                    last_detail = f"attempt_timeout_before_candidate_requests: {final_page_url}"
                    break
                for pdf_url in build_pdf_variants(href, base_url):
                    if time.monotonic() >= deadline:
                        last_detail = f"attempt_timeout_during_candidate_requests: {final_page_url}"
                        break
                    ok, http_status, detail = try_session_request_download(
                        context,
                        pdf_url,
                        final_page_url,
                        record.pdf_path,
                        timeout_ms=_remaining_timeout_ms(deadline, WILEY_DOWNLOAD_TIMEOUT_MS),
                    )
                    if ok:
                        return make_result(
                            record=record,
                            downloaded=1,
                            status="downloaded_wiley",
                            source_url=pdf_url,
                            local_path=record.relative_path,
                            http_status=http_status,
                        )
                    last_detail = detail

            if time.monotonic() < deadline and open_pdf_viewer(page, pdf_candidates, base_url, deadline=deadline):
                dismiss_cookie_banner(page)

                if time.monotonic() < deadline and try_wiley_html_viewer_download(page, record.pdf_path):
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_wiley",
                        source_url=page.url,
                        local_path=record.relative_path,
                    )
                if time.monotonic() < deadline and try_pdf_viewer_save_download(page, record.pdf_path):
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_wiley",
                        source_url=page.url,
                        local_path=record.relative_path,
                    )
                last_detail = f"viewer_browser_download_failed: {page.url}"

                ok, http_status, source_or_detail = (False, None, last_detail)
                if time.monotonic() < deadline:
                    ok, http_status, source_or_detail = try_viewer_sources_download(
                        page,
                        context,
                        record.pdf_path,
                        timeout_ms=_remaining_timeout_ms(deadline, WILEY_DOWNLOAD_TIMEOUT_MS),
                    )
                if ok:
                    return make_result(
                        record=record,
                        downloaded=1,
                        status="downloaded_wiley",
                        source_url=source_or_detail,
                        local_path=record.relative_path,
                        http_status=http_status,
                    )
                last_detail = source_or_detail

                current_url = page.url
                if time.monotonic() < deadline and "/doi/pdf/" in current_url:
                    direct_url = current_url.replace("/doi/pdf/", "/doi/pdfdirect/", 1)
                    ok, http_status, detail = try_session_request_download(
                        context,
                        direct_url,
                        current_url,
                        record.pdf_path,
                        timeout_ms=_remaining_timeout_ms(deadline, WILEY_DOWNLOAD_TIMEOUT_MS),
                    )
                    if ok:
                        return make_result(
                            record=record,
                            downloaded=1,
                            status="downloaded_wiley",
                            source_url=direct_url,
                            local_path=record.relative_path,
                            http_status=http_status,
                        )
                    last_detail = detail
            else:
                if time.monotonic() >= deadline:
                    last_detail = f"attempt_timeout_before_viewer_download: {page.url}"
                else:
                    last_detail = f"viewer_open_failed_or_empty: {page.url}"

            if time.monotonic() < deadline and try_browser_download(
                page,
                record.pdf_path,
                timeout_ms=_remaining_timeout_ms(deadline, WILEY_VIEWER_DOWNLOAD_TIMEOUT_MS),
            ):
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded_wiley",
                    source_url=page.url,
                    local_path=record.relative_path,
                )
            if time.monotonic() < deadline and try_pdf_viewer_save_download(page, record.pdf_path):
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded_wiley",
                    source_url=page.url,
                    local_path=record.relative_path,
                )
            if time.monotonic() >= deadline:
                last_detail = f"attempt_timeout_before_browser_fallbacks: {page.url}"
            else:
                last_detail = f"browser_download_failed: {page.url}"

            ok, http_status, source_or_detail = (False, None, last_detail)
            if time.monotonic() < deadline:
                ok, http_status, source_or_detail = try_viewer_sources_download(
                    page,
                    context,
                    record.pdf_path,
                    timeout_ms=_remaining_timeout_ms(deadline, WILEY_DOWNLOAD_TIMEOUT_MS),
                )
            if ok:
                return make_result(
                    record=record,
                    downloaded=1,
                    status="downloaded_wiley",
                    source_url=source_or_detail,
                    local_path=record.relative_path,
                    http_status=http_status,
                )
            last_detail = source_or_detail

            return make_result(
                record,
                0,
                "download_failed_wiley",
                source_url=final_page_url,
                detail=last_detail or f"all_download_attempts_failed: {final_page_url}",
            )
        finally:
            browser.close()


def try_wiley_resolver(record: Record, source_url: str = "") -> DownloadResult:
    if not ENABLE_WILEY_RESOLVER:
        return make_result(record, 0, "wiley_resolver_disabled")

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

    attempts = build_attempt_sequence(WILEY_BROWSER_MODE, WILEY_HEADLESS)
    last_result: DownloadResult | None = None

    for idx, headless in enumerate(attempts):
        result = _run_wiley_attempt(record, start_url=start_url, headless=headless)
        last_result = result
        if result.pdf_downloaded:
            return result
        if idx == len(attempts) - 1:
            return result
        if not is_retryable_wiley_status(result.pdf_download_status):
            return result

    return last_result or make_result(record, 0, "download_failed_wiley", source_url=start_url)
