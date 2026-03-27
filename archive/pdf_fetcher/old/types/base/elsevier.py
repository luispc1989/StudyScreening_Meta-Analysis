from pathlib import Path
from urllib.parse import urljoin
import re
import time
import random
import pyautogui  # optional fallback (pip install pyautogui)
import cloudscraper  # pip install cloudscraper
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


PUBLISHER = "Elsevier / ScienceDirect"
ARTICLE_URL = "https://doi.org/10.1016/j.sjbs.2022.103417"
SOURCE_URL = "https://linkinghub.elsevier.com/retrieve/pii/S1319562X22003333"
DOI = "10.1016/j.sjbs.2022.103417"
RECORD_ID = "7"
TITLE = "Grain and flour quality of wheat genotypes grown under heat stress"
OUTPUT_DIR = Path.home() / "Desktop" / "resolver_tests" / "elsevier"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    doi = doi.strip()
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi)
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Empty filename after sanitization.")
    return f"{safe}.pdf"


def is_pdf_bytes(data: bytes) -> bool:
    return bool(data) and data.startswith(b"%PDF")


def looks_like_pdf_url(url: str) -> str:
    value = str(url or "").strip().lower()
    return (
        value.endswith(".pdf")
        or ".pdf?" in value
        or "/pdfft" in value
        or "pdf.sciencedirectassets.com" in value
    )


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


def auto_wait_for_article_ready(page, max_wait=300):
    """Usa Playwright + cloudscraper para superar CAPTCHA/WAF, pyautogui apenas como fallback."""
    print("Aguardando página artigo carregar...")

    page.wait_for_load_state("networkidle", timeout=30000)

    # 1. Tentativa direta no Playwright
    try:
        page.wait_for_selector('text="View PDF"', timeout=300000)  # 5min
        print("Botão 'View PDF' detectado automaticamente!")
        return
    except PlaywrightTimeoutError:
        pass

    # 2. Se ainda houver CAPTCHA/WAF, tenta cloudscraper
    if page.locator('text="Are you a robot?"').count() > 0:
        print("CAPTCHA / WAF detectado. Usando cloudscraper para pré‑resolver...")
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            },
            delay=random.uniform(2, 5),
        )

        try:
            resp = scraper.get(ARTICLE_URL, timeout=30)
            if resp.status_code == 200:
                print("cloudscraper conseguiu superar o WAF.")

                # 2.1. Adicionar todas as cookies para o contexto Playwright
                added_cookies = []
                for ck in resp.cookies:
                    added_cookies.append({
                        "name": ck.name,
                        "value": ck.value,
                        "domain": ck.domain or ".elsevier.com",
                        "path": ck.path or "/",
                        "expires": int(time.time() + 3600)
                        if ck.expires is None else ck.expires,
                        "httpOnly": ck.has("httponly"),
                        "secure": ck.secure or False,
                    })
                page.context.add_cookies(added_cookies)
                print("Cookies transferidas para Playwright.")

                # 2.2. Recarregar página e tentar de novo
                page.reload()
                page.wait_for_selector('text="View PDF"', timeout=120000)
                print("Botão 'View PDF' encontrado após cloudscraper.")
                return
            else:
                print(f"cloudscraper retornou status {resp.status_code}")
        except Exception as e:
            print(f"cloudscraper falhou: {e}")

    # 3. Fallback: se ainda estiver com CAPTCHA, tenta clique automático (pyautogui)
    print("Usando pyautogui como fallback (botão CAPTCHA).")
    pyautogui.click(600, 525)
    time.sleep(3)

    try:
        page.wait_for_selector('text="View PDF"', timeout=60000)
        print("Botão 'View PDF' encontrado após clique.")
    except PlaywrightTimeoutError:
        raise RuntimeError("Não foi possível resolver o CAPTCHA/WAF automaticamente.")


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


def main():
    pyautogui.FAILSAFE = True  # Move mouse canto superior‑esq para parar script

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            accept_downloads=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            print(f"Opening article page: {ARTICLE_URL}")
            page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=120000)

            # Substitui o modo manual por auto_wait + cloudscraper
            auto_wait_for_article_ready(page)

            print(f"Current page URL: {page.url}")

            doi = extract_doi_from_page(page, fallback_url=page.url)
            output_file = OUTPUT_DIR / minimal_safe_filename_from_doi(doi)
            print(f"Detected DOI: {doi}")
            print(f"Output file: {output_file}")

            view_pdf_href = find_view_pdf_href(page)
            if view_pdf_href:
                pdf_view_url = urljoin(page.url, view_pdf_href)
                print(f"View PDF URL found: {pdf_view_url}")

                ok = try_session_request_download(context, pdf_view_url, page.url, output_file)
                if ok:
                    print(f"PDF saved successfully: {output_file}")
                    return

            print("Direct request failed or no href found. Opening viewer from page...")
            viewer_page = click_view_pdf(page)
            print(f"Viewer URL: {viewer_page.url}")

            direct_pdf_url = extract_pdf_url_from_viewer(viewer_page)
            if direct_pdf_url:
                print(f"Direct PDF URL found in viewer: {direct_pdf_url}")
                ok = try_session_request_download(context, direct_pdf_url, viewer_page.url, output_file)
                if ok:
                    print(f"PDF saved successfully: {output_file}")
                    return

            print("Viewer request failed. Trying viewer download button...")
            ok = try_browser_download_from_viewer(viewer_page, output_file)
            if ok:
                print(f"PDF saved successfully: {output_file}")
                return

            raise RuntimeError(
                "Failed to download PDF from Elsevier after opening the viewer."
            )
        finally:
            browser.close()


if __name__ == "__main__":
    main()
