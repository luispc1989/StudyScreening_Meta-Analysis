from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re

ARTICLE_URL = "https://link.springer.com/article/10.1007/s40009-023-01331-x"
BASE_URL = "https://link.springer.com"
OUTPUT_DIR = Path(r"C:\Users\Luís Pinto Coelho\Desktop\springer_downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_doi_from_page(page, fallback_url: str | None = None) -> str:
    """
    Detect the DOI from the current article page.
    Tries metadata first, then DOI links, then HTML regex, then URL fallback.
    """
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='dc.Identifier']",
        "meta[name='DC.Identifier']",
        "meta[name='dc.identifier']",
        "meta[name='DC.identifier']",
        "meta[name='prism.doi']",
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
            loc = page.locator(sel).first
            if loc.count() > 0:
                href = loc.get_attribute("href")
                if href:
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

    if fallback_url and "/article/" in fallback_url:
        return fallback_url.split("/article/", 1)[1].strip()

    raise RuntimeError("Could not detect DOI from the Springer page.")


def minimal_safe_filename_from_doi(doi: str) -> str:
    """
    Keep the DOI as close as possible to the original.
    Only replace characters that are invalid in Windows filenames.
    """
    doi = doi.strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")

    if not safe:
        raise ValueError("Empty filename after sanitization.")

    return f"{safe}.pdf"


def is_pdf_bytes(data: bytes) -> bool:
    return data.startswith(b"%PDF")


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
        return False

    output_file.write_bytes(data)
    return True


def try_browser_download(page, selectors: list[str], output_file: Path) -> bool:
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
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
    selectors = [
        "a[data-test='pdf-link']",
        "a[data-article-pdf='true']",
        "a.c-pdf-download__link",
        "a[href*='/content/pdf/']",
        "a:has-text('Download PDF')",
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
        page.wait_for_timeout(2000)

        doi = extract_doi_from_page(page, fallback_url=ARTICLE_URL)
        output_file = OUTPUT_DIR / minimal_safe_filename_from_doi(doi)

        print(f"Detected DOI: {doi}")
        print(f"Output file: {output_file}")

        pdf_href = None
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if loc.count() == 0:
                    continue

                href = loc.get_attribute("href")
                if href:
                    pdf_href = href
                    print(f"Found PDF href with selector: {sel}")
                    break
            except Exception:
                continue

        if not pdf_href:
            browser.close()
            raise RuntimeError("Could not find a PDF link on the Springer page.")

        pdf_url = urljoin(BASE_URL, pdf_href)
        print(f"PDF URL found: {pdf_url}")

        ok = try_session_request_download(context, pdf_url, ARTICLE_URL, output_file)
        if ok:
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        print("Session request download failed. Trying browser click download...")

        ok = try_browser_download(page, selectors, output_file)
        if ok:
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        browser.close()
        raise RuntimeError(
            "Failed to download PDF from Springer. "
            "The page may require a different session state or may open the PDF in a non-download viewer."
        )


if __name__ == "__main__":
    main()