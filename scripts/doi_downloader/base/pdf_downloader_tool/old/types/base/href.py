from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import requests
import re

ARTICLE_URL = "https://pse.agriculturejournals.cz/artkey/pse-202102-0002_the-effect-of-heat-stress-on-some-main-spike-traits-in-12-wheat-cultivars-at-anthesis-and-mid-grain-filling-sta.php"
BASE_URL = "https://pse.agriculturejournals.cz"
OUTPUT_DIR = Path(r"C:\Users\Luís Pinto Coelho\Desktop\journal_downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def minimal_safe_filename_from_doi(doi: str) -> str:
    safe = re.sub(r'[\\/:*?"<>|]', "_", doi.strip())
    safe = safe.rstrip(" .")
    if not safe:
        raise ValueError("Nome de ficheiro inválido após sanitização do DOI.")
    return f"{safe}.pdf"


def extract_doi_from_page(page) -> str:
    # 1) Common scholarly meta tags
    meta_selectors = [
        "meta[name='citation_doi']",
        "meta[name='DC.Identifier']",
        "meta[name='dc.Identifier']",
        "meta[name='dc.identifier']",
        "meta[name='prism.doi']",
    ]

    for sel in meta_selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                content = loc.get_attribute("content")
                if content:
                    content = content.strip()

                    # Handle cases like "doi:10.17221/2/2021-PSE"
                    m = re.search(r'(10\.\d{4,9}/\S+)', content, re.I)
                    if m:
                        return m.group(1).rstrip(" .;,)")
        except:
            pass

    # 2) Look for doi.org links
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
                        return m.group(1).rstrip(" .;,)")
        except:
            pass

    # 3) Regex over full page HTML
    try:
        html = page.content()
        m = re.search(r'(10\.\d{4,9}/[^\s"<>&]+)', html, re.I)
        if m:
            return m.group(1).rstrip(" .;,)")
    except:
        pass

    raise RuntimeError("Não foi possível detetar o DOI na página.")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    doi = extract_doi_from_page(page)
    print("DOI detetado:", doi)

    pdf_href = None
    selectors = [
        "a[href*='/pdfs/']",
        "a[href$='.pdf']",
        "a:has-text('Open full article')",
        "a:has(img[src*='pdf'])",
    ]

    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                href = loc.get_attribute("href")
                if href and ".pdf" in href:
                    pdf_href = href
                    break
        except:
            pass

    if not pdf_href:
        browser.close()
        raise RuntimeError("Não foi encontrado um link PDF.")

    pdf_url = urljoin(BASE_URL, pdf_href)
    print("PDF URL encontrado:", pdf_url)

    headers = {
        "User-Agent": page.evaluate("() => navigator.userAgent"),
        "Referer": ARTICLE_URL,
    }

    r = requests.get(pdf_url, headers=headers, timeout=120)
    r.raise_for_status()

    if "pdf" not in r.headers.get("Content-Type", "").lower() and not r.content.startswith(b"%PDF"):
        browser.close()
        raise RuntimeError("A resposta não parece ser um PDF válido.")

    output_file = OUTPUT_DIR / minimal_safe_filename_from_doi(doi)
    output_file.write_bytes(r.content)

    print(f"PDF guardado em: {output_file}")
    browser.close()