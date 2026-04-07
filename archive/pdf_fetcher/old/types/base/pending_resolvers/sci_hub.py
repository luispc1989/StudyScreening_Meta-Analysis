from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PUBLISHER = "Sci-Hub"
BASE_URL = "https://sci-hub.box/"
DOI = "10.1111/j.1439-0523.2007.01460.x"
RECORD_ID = "sci_hub_test"
TITLE = "Sci-Hub test download"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "sci_hub"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    doi = str(doi or "").strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


def minimal_safe_filename_from_record(record_id: str, title: str) -> str:
    base = f"{record_id}_{title}".strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", base)
    safe = re.sub(r"\s+", " ", safe).strip().rstrip(" .")
    safe = re.sub(r"_+", "_", safe)
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


def build_sci_hub_url(doi: str) -> str:
    doi = str(doi or "").strip()
    if not doi:
        raise ValueError("DOI is required.")
    return urljoin(BASE_URL, doi)


def extract_pdf_url(page) -> str | None:
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


def get_pdf_bytes(context, pdf_url: str, referer: str) -> bytes | None:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer},
        timeout=60000,
    )
    if response.status != 200:
        return None

    data = response.body()
    if data.startswith(b"%PDF"):
        return data
    return None


def fill_sci_hub_search(page, doi: str) -> None:
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)

    if page.locator("textarea#request").count() > 0:
        page.fill("textarea#request", doi)
    elif page.locator("input[name='request']").count() > 0:
        page.fill("input[name='request']", doi)
    else:
        raise RuntimeError("Sci-Hub search box not found.")

    if page.locator("button[type='submit']").count() > 0:
        page.click("button[type='submit']")
    else:
        page.keyboard.press("Enter")

    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(2000)


def download_pdf_via_browser(page, output_file: Path) -> bool:
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
                with page.expect_download(timeout=60000) as download_info:
                    locator.click()
                download = download_info.value
                download.save_as(str(output_file))
                return output_file.exists() and output_file.stat().st_size > 0
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue

    return False


def main():
    output_file = OUTPUT_DIR / minimal_safe_filename_from_record(RECORD_ID, TITLE)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(f"Opening Sci-Hub home page and submitting DOI: {DOI}")
        fill_sci_hub_search(page, DOI)

        pdf_href = extract_pdf_url(page)
        if pdf_href:
            pdf_url = urljoin(page.url, pdf_href)
            print(f"Detected PDF URL: {pdf_url}")
            pdf_bytes = get_pdf_bytes(context, pdf_url, page.url)
            if pdf_bytes:
                output_file.write_bytes(pdf_bytes)
                print(f"Saved PDF to: {output_file}")
                browser.close()
                return

        print("Direct PDF URL not found or not downloadable, trying browser download.")
        if download_pdf_via_browser(page, output_file):
            print(f"Saved PDF to: {output_file}")
            browser.close()
            return

        browser.close()
        raise RuntimeError("Sci-Hub download failed. The page may require manual resolution or a different selector path.")


if __name__ == "__main__":
    main()
