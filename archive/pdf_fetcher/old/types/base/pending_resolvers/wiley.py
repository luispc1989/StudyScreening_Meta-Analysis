from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import re

PUBLISHER = "Wiley"
ARTICLE_URL = "https://doi.org/10.1111/j.1439-0523.2007.01460.x"
SOURCE_URL = "https://onlinelibrary.wiley.com/doi/10.1111/j.1439-0523.2007.01460.x"
DOI = "10.1111/j.1439-0523.2007.01460.x"
RECORD_ID = "19"
TITLE = "Reduction in kernel weight as a potential indirect selection criterion for wheat grain yield under terminal heat stress"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "wiley"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    doi = doi.strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


def minimal_safe_filename_from_record(record_id: str, title: str) -> str:
    base = f"{record_id}__{title}".strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", base)
    safe = re.sub(r"\s+", " ", safe).strip().rstrip(" .")
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
                    match = re.search(r"(10\.\d{4,9}/\S+)", content.strip(), re.I)
                    if match:
                        return match.group(1).rstrip(" .;,:)")
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

    raise RuntimeError("Could not detect DOI from the Wiley page.")


def is_pdf_bytes(data: bytes) -> bool:
    return data.startswith(b"%PDF")


def looks_like_pdf_url(href: str) -> bool:
    href_l = href.lower()
    return any(
        marker in href_l
        for marker in (
            "/doi/pdf",
            "/doi/epdf",
            "pdfdirect",
            "asset/pdf",
            ".pdf",
        )
    )


def build_pdf_variants(href_or_url: str, base_url: str) -> list[str]:
    absolute = urljoin(base_url, href_or_url)
    variants = [absolute]

    parsed = urlparse(absolute)
    path = parsed.path
    query = parsed.query

    if "/doi/pdf/" in path:
        variants.append(absolute.replace("/doi/pdf/", "/doi/pdfdirect/", 1))
    if "/doi/epdf/" in path:
        variants.append(absolute.replace("/doi/epdf/", "/doi/pdfdirect/", 1))
        variants.append(absolute.replace("/doi/epdf/", "/doi/pdf/", 1))

    base_no_query = absolute.split("?", 1)[0]
    variants.append(f"{base_no_query}?download=true")
    variants.append(f"{base_no_query}?download=1")

    if "/doi/pdfdirect/" in base_no_query:
        variants.append(base_no_query)
    if query:
        variants.append(absolute)

    deduped: list[str] = []
    seen = set()
    for variant in variants:
        if variant in seen:
            continue
        seen.add(variant)
        deduped.append(variant)
    return deduped


def build_wiley_html_viewer_url(href_or_url: str, base_url: str) -> str:
    absolute = urljoin(base_url, href_or_url)
    parsed = urlparse(absolute)
    path = parsed.path

    if "/doi/pdf/" in path:
        file_path = path.replace("/doi/pdf/", "/doi/pdfdirect/", 1)
    elif "/doi/epdf/" in path:
        file_path = path.replace("/doi/epdf/", "/doi/pdfdirect/", 1)
    elif "/doi/pdfdirect/" in path:
        file_path = path
    else:
        file_path = path

    return urljoin(
        base_url,
        f"/templates/jsp/_ux3/_acropolis/_pericles/pdf-viewer/web/viewer.html?file={file_path}",
    )


def is_access_gate(page) -> bool:
    try:
        text = page.locator("body").inner_text(timeout=3000).lower()
    except Exception:
        return False

    markers = [
        "are you a robot",
        "captcha",
        "security check",
        "access denied",
        "verify you are human",
    ]
    return any(marker in text for marker in markers)


def wait_for_manual_access_if_needed(page) -> None:
    if not is_access_gate(page):
        return

    print("Access gate detected on Wiley page.")
    print("Resolve it manually in the browser, then press Enter here to continue.")
    input()
    page.wait_for_timeout(2000)


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
    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                href = page.locator(sel).nth(i).get_attribute("href")
                print(f"Selector {sel} [{i}] -> href: {href}")
                if href and looks_like_pdf_url(href):
                    candidates.append(href)
        except Exception as exc:
            print(f"Selector failed: {sel} -> {exc}")

    try:
        html = page.content()
        regex_candidates = re.findall(
            r'''["']([^"']*(?:/doi/(?:pdf|epdf)|pdfdirect|asset/pdf)[^"']*)["']''',
            html,
            flags=re.I,
        )
        candidates.extend(regex_candidates)
    except Exception:
        pass

    deduped: list[str] = []
    seen = set()
    for href in candidates:
        if href in seen:
            continue
        seen.add(href)
        deduped.append(href)

    return deduped


def collect_viewer_pdf_candidates(page) -> list[str]:
    candidates: list[str] = []

    explicit_selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdfdirect/']",
        "a.btn-cta[href*='/doi/pdfdirect/']",
        "a[data-download-files-key='pdf']",
    ]
    for sel in explicit_selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                href = page.locator(sel).nth(i).get_attribute("href")
                print(f"Viewer selector {sel} [{i}] -> href: {href}")
                if href:
                    candidates.append(href)
        except Exception:
            pass

    try:
        current_url = page.url
        if looks_like_pdf_url(current_url):
            candidates.append(current_url)
    except Exception:
        pass

    try:
        html = page.content()
        regex_candidates = re.findall(
            r'''["']([^"']*(?:/doi/(?:pdf|epdf|pdfdirect)|pdfdirect|asset/pdf|\.pdf)[^"']*)["']''',
            html,
            flags=re.I,
        )
        candidates.extend(regex_candidates)
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
    seen = set()
    for href in candidates:
        if not href or not looks_like_pdf_url(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        deduped.append(href)
    return deduped


def wait_for_wiley_viewer(page) -> None:
    selectors = [
        "a[aria-label='Download PDF']",
        "a[href*='/doi/pdfdirect/']",
        "a.btn-cta",
        "#simpleViewer",
        ".viewer-pdf",
    ]
    for sel in selectors:
        try:
            page.locator(sel).first.wait_for(state="visible", timeout=8000)
            return
        except Exception:
            continue


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


def try_browser_download(page, selectors: list[str], output_file: Path) -> bool:
    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                loc = page.locator(sel).nth(i)
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


def open_pdf_viewer(page, candidate_hrefs: list[str], base_url: str) -> bool:
    for href in candidate_hrefs:
        viewer_url = build_wiley_html_viewer_url(href, base_url)
        print(f"Opening Wiley HTML viewer: {viewer_url}")
        try:
            page.goto(viewer_url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(2500)
            try:
                page.wait_for_load_state("networkidle", timeout=8000)
            except PlaywrightTimeoutError:
                pass
            if "request username" in page.locator("body").inner_text(timeout=3000).lower():
                print("Viewer URL redirected to authentication flow, skipping.")
                continue
            return True
        except Exception as exc:
            print(f"Viewer navigation failed for {viewer_url} -> {exc}")
            continue
    return False


def dismiss_cookie_banner(page) -> None:
    selectors = [
        "button:has-text('Aceitar tudo')",
        "button:has-text('Accept all')",
        "button:has-text('I agree')",
        "button#onetrust-accept-btn-handler",
        "button[aria-label*='Accept']",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0 and loc.is_visible():
                print(f"Dismissing cookie banner with: {sel}")
                loc.click(timeout=3000)
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


def try_viewer_sources_download(page, context, output_file: Path) -> bool:
    base_url = f"{urlparse(page.url).scheme}://{urlparse(page.url).netloc}"
    viewer_candidates = collect_viewer_pdf_candidates(page)
    if not viewer_candidates:
        return False

    print(f"Viewer candidates found: {len(viewer_candidates)}")
    for candidate in viewer_candidates:
        for pdf_url in build_pdf_variants(candidate, base_url):
            print(f"Trying viewer-derived PDF URL: {pdf_url}")
            ok = try_session_request_download(context, pdf_url, page.url, output_file)
            if ok:
                return True
    return False


def try_wiley_html_viewer_download(page, output_file: Path) -> bool:
    selectors = [
        "a[aria-label='Download PDF']",
        "a.btn-cta[href*='/doi/pdfdirect/']",
        "a[href*='/doi/pdfdirect/'][data-download-file='true']",
        "a[href*='/doi/pdfdirect/']",
    ]

    for sel in selectors:
        try:
            count = page.locator(sel).count()
            for i in range(count):
                loc = page.locator(sel).nth(i)
                href = loc.get_attribute("href")
                print(f"Trying Wiley HTML viewer download selector {sel} [{i}] -> href: {href}")
                with page.expect_download(timeout=120000) as download_info:
                    loc.click(timeout=10000)
                download = download_info.value
                download.save_as(str(output_file))
                return True
        except PlaywrightTimeoutError:
            continue
        except Exception as exc:
            print(f"Wiley HTML viewer selector failed: {sel} -> {exc}")
            continue

    return False


def main():
    click_download_selectors = [
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

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print(f"Opening article page: {ARTICLE_URL}")
        page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=120000)
        wait_for_manual_access_if_needed(page)

        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except PlaywrightTimeoutError:
            pass

        page.wait_for_timeout(3000)
        dismiss_cookie_banner(page)

        final_page_url = page.url
        base_url = f"{urlparse(final_page_url).scheme}://{urlparse(final_page_url).netloc}"
        print(f"Final page URL: {final_page_url}")

        doi = extract_doi_from_page(page, fallback_url=final_page_url)
        temp_output_file = OUTPUT_DIR / minimal_safe_filename_from_doi(doi)
        output_file = OUTPUT_DIR / minimal_safe_filename_from_record(RECORD_ID, TITLE)

        print(f"Detected DOI: {doi}")
        print(f"Output file: {output_file}")

        pdf_candidates = collect_pdf_candidates(page)
        if not pdf_candidates:
            browser.close()
            raise RuntimeError("Could not find a Wiley PDF link on the page.")

        for href in pdf_candidates:
            for pdf_url in build_pdf_variants(href, base_url):
                print(f"Trying PDF URL: {pdf_url}")
                ok = try_session_request_download(context, pdf_url, final_page_url, temp_output_file)
                if ok:
                    if temp_output_file != output_file:
                        temp_output_file.replace(output_file)
                    print(f"PDF saved successfully: {output_file}")
                    browser.close()
                    return

        print("Direct session download failed. Opening Wiley viewer...")

        ok = open_pdf_viewer(page, pdf_candidates, base_url)
        if ok:
            wait_for_wiley_viewer(page)
            dismiss_cookie_banner(page)

            ok = try_wiley_html_viewer_download(page, temp_output_file)
            if ok:
                if temp_output_file != output_file:
                    temp_output_file.replace(output_file)
                print(f"PDF saved successfully: {output_file}")
                browser.close()
                return

            ok = try_viewer_sources_download(page, context, temp_output_file)
            if ok:
                if temp_output_file != output_file:
                    temp_output_file.replace(output_file)
                print(f"PDF saved successfully: {output_file}")
                browser.close()
                return

            current_url = page.url
            if "/doi/pdf/" in current_url:
                direct_url = current_url.replace("/doi/pdf/", "/doi/pdfdirect/", 1)
                print(f"Trying viewer current URL variant: {direct_url}")
                ok = try_session_request_download(context, direct_url, current_url, temp_output_file)
                if ok:
                    if temp_output_file != output_file:
                        temp_output_file.replace(output_file)
                    print(f"PDF saved successfully: {output_file}")
                    browser.close()
                    return

        print("Viewer source extraction failed. Trying browser download event...")

        ok = try_browser_download(page, click_download_selectors, temp_output_file)
        if ok:
            if temp_output_file != output_file:
                temp_output_file.replace(output_file)
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        dismiss_cookie_banner(page)
        print("Browser click download failed. Trying viewer-derived sources...")

        ok = try_viewer_sources_download(page, context, temp_output_file)
        if ok:
            if temp_output_file != output_file:
                temp_output_file.replace(output_file)
            print(f"PDF saved successfully: {output_file}")
            browser.close()
            return

        browser.close()
        raise RuntimeError(
            "Failed to download PDF from Wiley. "
            "The page may require a different session state or use a viewer flow not yet covered."
        )


if __name__ == "__main__":
    main()
