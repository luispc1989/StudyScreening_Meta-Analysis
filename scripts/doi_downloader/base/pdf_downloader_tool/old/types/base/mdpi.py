from pathlib import Path
from playwright.sync_api import sync_playwright

ARTICLE_URL = "https://www.mdpi.com/2073-4395/13/5/1379"
OUTPUT_DIR = Path(r"C:\Users\Luís Pinto Coelho\Desktop\mdpi_downloads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(accept_downloads=True)
    page = context.new_page()

    page.goto(ARTICLE_URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # abrir dropdown Download
    for sel in [
        "div.download a.button--drop-down",
        "a.button--drop-down",
        "text=Download"
    ]:
        try:
            page.locator(sel).first.click(timeout=3000)
            break
        except:
            pass

    page.wait_for_timeout(1500)

    pdf_link = None
    for sel in [
        "a.UD_ArticlePDF",
        "a[data-name*='Download PDF']",
        "a[href*='/pdf?version=']",
        "a[href$='/pdf']",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                pdf_link = loc
                break
        except:
            pass

    if pdf_link is None:
        browser.close()
        raise RuntimeError("Não consegui localizar o link do PDF.")

    with page.expect_download(timeout=120000) as download_info:
        pdf_link.click()

    download = download_info.value
    target = OUTPUT_DIR / "agronomy_2023_13_5_1379.pdf"
    download.save_as(str(target))

    print(f"PDF guardado em: {target}")
    browser.close()