from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re

ARTICLE_URL = "https://doi.org/10.3389/fpls.2023.1132108"
BASE_URL = "https://www.frontiersin.org"
OUTPUT_DIR = Path(r"C:\Users\Luís Pinto Coelho\Desktop\frontiers_downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    doi = doi.strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


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

    for sel in meta_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                content = loc.get_attribute("content")
                if content:
                    m = re.search(r'(10\.\d{4,9}/\S+)', content.strip(), re.I)
                    if m:
                        return m.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    doi_link_selectors = [
        "a[href*='doi.org/']",
        "a[href*='dx.doi.org/']",
    ]

    for sel in doi_link_selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                href = page.locator(sel).nth(i).get_attribute("href")
                if not href:
                    continue
                m = re.search(r'doi\.org/(10\.\d{4,9}/\S+)', href, re.I)
                if m:
                    return m.group(1).rstrip(" .;,:)")
        except Exception:
            pass

    try:
        html = page.content()
        m = re.search(r'(10\.\d{4,9}/[^\s"<>&]+)', html, re.I)
        if m:
            return m.group(1).rstrip(" .;,:)")
    except Exception:
        pass

    if fallback_url:
        m = re.search(r'(10\.\d{4,9}/\S+)', fallback_url, re.I)
        if m:
            return m.group(1).rstrip(" .;,:)")

    raise RuntimeError("Could not detect DOI from the Frontiers page.")


def is_pdf_bytes(data: bytes) -> bool:
    return data.startswith(b"%PDF")


def looks_like_pdf_url(href: str) -> bool:
    href_l = href.lower()
    return (
        "/pdf" in href_l
        or href_l.endswith(".pdf")
        or "download-a-pdf" in href_l
    )


def find_pdf_href(page, selectors: list[str]) -> str | None:
    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                loc = page.locator(sel).nth(i)
                href = loc.get_attribute("href")
                print(f"Selector {sel} [{i}] -> href: {href}")
                if href and looks_like_pdf_url(href):
                    print(f"Found PDF href with selector: {sel} [{i}]")
                    return href
        except Exception as e:
            print(f"Selector failed: {sel} -> {e}")
    return None


def try_session_request_download(context, pdf_url: str, referer_url: str, output_file: Path) -> bool:
    response = context.request.get(
        pdf_url,
        headers={"Referer": referer_url},
        timeout=120000
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


def try_browser_download(page, selectors: list[str], output_file: Path) -> bool:
    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                loc = page.locator(sel).nth(i)
                href = loc.get_attribute("href")
                if not href or not looks_like_pdf_url(href):
                    continue

                with page.expect_download(timeout=120000) as download_info:
                    loc.click()

                download = download_info.value
                download.save_as(str(output_file))
                return True

        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue

    return False


def main():
    pdf_selectors = [
        # Main button / standard layout
        "a[data-event='download-a-pdf']",
        "a.DownloadArticleButton_action",
        "a[href*='/pdf']",
        "a[href$='.pdf']",

        # Compact / toolbar layout
        "li.ToolbarDownload a",
        "a.ToolbarDownload_action",
        "nav.Toolbar a[data-event='download-a-pdf']",

        # Loose fallbacks
        "a:has-text('PDF')",
        "a:has-text('Download')",
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(f"Opening article page: {ARTICLE_URL}")
        page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        final_page_url = page.url
        print(f"Final page URL: {final_page_url}")

        doi = extract_doi_from_page(page, fallback_url=final_page_url)
        output_file = OUTPUT_DIR / minimal_safe_filename_from_doi(doi)

        print(f"Detected DOI: {doi}")
        print(f"Output file: {output_file}")

        pdf_href = find_pdf_href(page, pdf_selectors)

        if not pdf_href:
            browser.close()
            raise RuntimeError("Could not find a PDF link on the Frontiers page.")

        pdf_url = urljoin(BASE_URL, pdf_href)
        print(f"PDF URL found: {pdf_url}")

        ok = try_session_request_download(context, pdf_url, final_page_url, output_file)
        if ok:
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        print("Session request download failed. Trying browser click download...")

        ok = try_browser_download(page, pdf_selectors, output_file)
        if ok:
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        browser.close()
        raise RuntimeError(
            "Failed to download PDF from Frontiers. "
            "The page may require a different session state or may open the PDF in a viewer."
        )


if __name__ == "__main__":
    main()