from pathlib import Path
from urllib.parse import urljoin
import random
import re
import sys
import time

import cloudscraper  # optional experimental dependency (pip install cloudscraper)
import pyautogui  # optional fallback (pip install pyautogui)
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.pdf_fetcher.core.config import SHEET_NAME, build_current_workbook_path
from tools.pdf_fetcher.core.excel_io import build_col_map, build_record, get_optional_cell, load_workbook_and_sheet
from tools.pdf_fetcher.core.utils import build_pdf_filename, normalize_doi


PUBLISHER = "Elsevier / ScienceDirect"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "elsevier"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    doi = doi.strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


def build_output_file(record_id: str, title: str, doi: str) -> Path:
    try:
        file_name = build_pdf_filename(record_id, title)
    except Exception:
        file_name = minimal_safe_filename_from_doi(doi)
    return OUTPUT_DIR / file_name


def is_pdf_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def looks_like_pdf_url(url: str) -> bool:
    value = str(url or "").strip().lower()
    return (
        value.endswith(".pdf")
        or ".pdf?" in value
        or "/pdfft" in value
        or "pdf.sciencedirectassets.com" in value
    )


def is_elsevier_candidate(doi_raw: str, doi_link_raw: str, source_url: str = "") -> bool:
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
        if "sciencedirect.com" in value:
            return True
        if "elsevier.com" in value:
            return True
        if "linkinghub.elsevier.com" in value:
            return True
        if value.startswith("10.1016/"):
            return True
        if "/10.1016/" in value:
            return True
    return False


def collect_elsevier_cases_from_current() -> list[dict]:
    workbook_path = build_current_workbook_path()
    wb, ws = load_workbook_and_sheet(workbook_path, SHEET_NAME)

    try:
        col_map = build_col_map(ws)
        cases: list[dict] = []

        for row_idx in range(2, ws.max_row + 1):
            record = build_record(ws, row_idx, col_map)
            if record is None:
                continue

            source_url = str(get_optional_cell(ws, row_idx, col_map, "pdf_source_url", "") or "").strip()
            if not is_elsevier_candidate(record.doi_raw, record.doi_link_raw, source_url):
                continue

            doi = normalize_doi(record.doi_raw) or normalize_doi(record.doi_link_raw)
            if not doi:
                continue

            cases.append(
                {
                    "row_idx": row_idx,
                    "record_id": record.record_id,
                    "title": record.title,
                    "doi": doi,
                    "article_url": f"https://doi.org/{doi}",
                    "source_url": source_url,
                    "output_file": build_output_file(record.record_id, record.title, doi),
                }
            )

        return cases
    finally:
        wb.close()


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.identifier']",
        "meta[name='DC.Identifier']",
        "meta[name='prism.doi']",
    ]

    for sel in meta_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                content = loc.get_attribute("content")
                if content:
                    m = re.search(r"(10\.\d{4,9}/\S+)", content.strip(), re.I)
                    if m:
                        return m.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    if fallback_url:
        m = re.search(r"(10\.\d{4,9}/\S+)", fallback_url, re.I)
        if m:
            return m.group(1).rstrip(" .;,:)")

    raise RuntimeError("Could not detect DOI from the Elsevier page.")


def wait_for_page_ready(page, timeout_ms: int = 120000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(2000)


def auto_wait_for_article_ready(page, article_url: str) -> None:
    print("Waiting for Elsevier article page to become ready...")
    page.wait_for_load_state("networkidle", timeout=30000)

    try:
        page.wait_for_selector('text="View PDF"', timeout=300000)
        print("Button 'View PDF' detected automatically.")
        return
    except PlaywrightTimeoutError:
        pass

    if page.locator('text="Are you a robot?"').count() > 0:
        print("CAPTCHA / WAF detected. Trying cloudscraper as experimental pre-step...")
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
                print("cloudscraper returned status 200. Syncing cookies to Playwright...")
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
                page.wait_for_selector('text="View PDF"', timeout=120000)
                print("Button 'View PDF' found after cloudscraper.")
                return
            print(f"cloudscraper returned status {resp.status_code}")
        except Exception as exc:
            print(f"cloudscraper failed: {exc}")

    print("Using pyautogui as fallback (experimental CAPTCHA click).")
    pyautogui.click(600, 525)
    time.sleep(3)

    try:
        page.wait_for_selector('text="View PDF"', timeout=60000)
        print("Button 'View PDF' found after fallback click.")
    except PlaywrightTimeoutError:
        raise RuntimeError("Could not resolve the Elsevier CAPTCHA/WAF automatically.")


def find_view_pdf_href(page) -> str | None:
    selectors = [
        "li#ViewPDF a[href*='/pdfft']",
        "li.ViewPDF a[href*='/pdfft']",
        "a[href*='/pdfft']",
        "a[aria-label*='View PDF']",
        "a:has-text('View PDF')",
    ]

    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                loc = page.locator(sel).nth(i)
                href = loc.get_attribute("href")
                if href and looks_like_pdf_url(href):
                    print(f"Found View PDF href with selector {sel} [{i}]: {href}")
                    return href
        except Exception as exc:
            print(f"Selector failed: {sel} -> {exc}")

    return None


def click_view_pdf(article_page):
    selectors = [
        "li#ViewPDF a",
        "li.ViewPDF a",
        "a[href*='/pdfft']",
        "a[aria-label*='View PDF']",
        "a:has-text('View PDF')",
    ]

    for sel in selectors:
        try:
            count = article_page.locator(sel).count()
            for i in range(count):
                loc = article_page.locator(sel).nth(i)
                print(f"Trying View PDF selector: {sel} [{i}]")

                try:
                    with article_page.expect_popup(timeout=15000) as popup_info:
                        loc.click()
                    popup = popup_info.value
                    wait_for_page_ready(popup)
                    return popup
                except PlaywrightTimeoutError:
                    loc.click()
                    wait_for_page_ready(article_page)
                    return article_page
        except Exception as exc:
            print(f"View PDF selector failed: {sel} -> {exc}")

    raise RuntimeError("Could not trigger the Elsevier 'View PDF' button.")


def try_session_request_download(context, pdf_url: str, referer_url: str, output_file: Path) -> bool:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer_url},
        timeout=120000,
    )

    print(f"Session request status: {response.status}")

    if response.status != 200:
        return False

    data = response.body()
    if not is_pdf_bytes(data):
        print("Response is not a valid PDF.")
        return False

    output_file.write_bytes(data)
    return True


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
    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                src = page.locator(sel).nth(i).get_attribute("src")
                href = page.locator(sel).nth(i).get_attribute("href")
                candidate = src or href
                if candidate and looks_like_pdf_url(candidate):
                    return candidate
        except Exception:
            pass

    return None


def try_browser_download_from_viewer(page, output_file: Path) -> bool:
    selectors = [
        "cr-icon-button#save",
        "#downloads cr-icon-button#save",
        "viewer-download-controls cr-icon-button#save",
    ]

    try:
        with page.expect_download(timeout=120000) as download_info:
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.count() == 0:
                        continue
                    loc.click()
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


def process_case(case: dict) -> str:
    pyautogui.FAILSAFE = True

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        )
        page = context.new_page()

        try:
            article_url = case["article_url"]
            output_file = case["output_file"]

            if output_file.exists() and output_file.stat().st_size > 0:
                print(f"[{case['record_id']}] duplicate_pdf -> {output_file.name}")
                return "duplicate_pdf"

            print("=" * 78)
            print(f"publisher: {PUBLISHER}")
            print(f"record_id: {case['record_id']}")
            print(f"doi: {case['doi']}")
            print(f"article_url: {article_url}")
            print(f"source_url: {case['source_url']}")
            print(f"title: {case['title']}")
            print(f"output_file: {output_file}")

            print(f"Opening article page: {article_url}")
            page.goto(article_url, wait_until="domcontentloaded", timeout=120000)
            auto_wait_for_article_ready(page, article_url)

            print(f"Current page URL: {page.url}")
            doi = extract_doi_from_page(page, fallback_url=page.url)
            print(f"Detected DOI: {doi}")
            print(f"Output file: {output_file}")

            view_pdf_href = find_view_pdf_href(page)
            if view_pdf_href:
                pdf_view_url = urljoin(page.url, view_pdf_href)
                print(f"View PDF URL found: {pdf_view_url}")

                ok = try_session_request_download(context, pdf_view_url, page.url, output_file)
                if ok:
                    print(f"PDF saved successfully: {output_file}")
                    return "downloaded"

            print("Direct request failed or no href found. Opening viewer from page...")
            viewer_page = click_view_pdf(page)
            print(f"Viewer URL: {viewer_page.url}")

            direct_pdf_url = extract_pdf_url_from_viewer(viewer_page)
            if direct_pdf_url:
                print(f"Direct PDF URL found in viewer: {direct_pdf_url}")
                ok = try_session_request_download(context, direct_pdf_url, viewer_page.url, output_file)
                if ok:
                    print(f"PDF saved successfully: {output_file}")
                    return "downloaded"

            print("Viewer request failed. Trying viewer download button...")
            ok = try_browser_download_from_viewer(viewer_page, output_file)
            if ok:
                print(f"PDF saved successfully: {output_file}")
                return "downloaded"

            raise RuntimeError("Failed to download PDF from Elsevier after opening the viewer.")
        finally:
            browser.close()


def main():
    current_workbook = build_current_workbook_path()
    cases = collect_elsevier_cases_from_current()

    print(f"Current workbook: {current_workbook}")
    print(f"Elsevier candidates found: {len(cases)}")

    if not cases:
        print("No Elsevier candidates found in Current workbook.")
        return

    downloaded = 0
    duplicates = 0
    failed = 0

    for idx, case in enumerate(cases, start=1):
        print(f"\n[{idx}/{len(cases)}] Processing Elsevier candidate...")
        try:
            status = process_case(case)
            if status == "downloaded":
                downloaded += 1
            elif status == "duplicate_pdf":
                duplicates += 1
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            failed += 1
            print(f"[{case['record_id']}] failed -> {type(exc).__name__}: {exc}")

    print("\n" + "=" * 78)
    print("Elsevier batch finished")
    print(f"Candidates : {len(cases)}")
    print(f"Downloaded : {downloaded}")
    print(f"Duplicates : {duplicates}")
    print(f"Failed     : {failed}")


if __name__ == "__main__":
    main()
