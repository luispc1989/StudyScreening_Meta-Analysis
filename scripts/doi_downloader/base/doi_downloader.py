from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re

download_dir = r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos\pdf_files_3"
os.makedirs(download_dir, exist_ok=True)

site_base = "https://sci-hub.box/"

def safe_filename(doi):
    return re.sub(r"[^\w\-_.]", "_", doi) + ".pdf"

def list_pdfs():
    return {
        f for f in os.listdir(download_dir)
        if f.lower().endswith(".pdf")
    }

def window_closed(driver):
    try:
        _ = driver.current_url
        return False
    except:
        return True

def newest_pdf(before_set):
    after_set = list_pdfs()
    new_files = list(after_set - before_set)
    if new_files:
        new_files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
        return new_files[0]
    return None

def download_pdf(doi, doi_index, total):
    driver = None
    try:
        before_files = list_pdfs()

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0
        }
        chrome_options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.maximize_window()

        url = site_base + doi
        print(f"\n🔥 [{doi_index}/{total}] {doi}")
        print("Fecha a janela se não houver artigo; se houver, clica em download e depois Enter.")
        driver.get(url)
        time.sleep(2)

        input("Enter quando terminares essa decisão... ")

        if window_closed(driver):
            print("⏭️ Janela fechada manualmente.")
            return "skip"

        new_file = newest_pdf(before_files)
        if new_file:
            old_path = os.path.join(download_dir, new_file)
            final_name = safe_filename(doi)
            final_path = os.path.join(download_dir, final_name)

            if old_path != final_path and os.path.exists(old_path):
                try:
                    os.replace(old_path, final_path)
                    print(f"✅ Download detetado e renomeado: {final_name}")
                except:
                    print(f"✅ Download detetado: {new_file}")
            else:
                print(f"✅ Download detetado: {final_name}")

            return "success"

        print("⏭️ Sem download detetado.")
        return "skip"

    except Exception as e:
        print(f"❌ Erro: {e}")
        return "error"

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

print("=== DOI DOWNLOADER ===")

if not os.path.exists("dois.txt"):
    print("❌ Não encontrei o ficheiro dois.txt")
    raise SystemExit

with open("dois.txt", "r", encoding="utf-8") as f:
    dois = [linha.strip() for linha in f if linha.strip()]

sucessos = 0
skips = 0
erros = 0

for i, doi in enumerate(dois, 1):
    result = download_pdf(doi, i, len(dois))

    if result == "success":
        sucessos += 1
    elif result == "skip":
        skips += 1
    else:
        erros += 1

    print(f"📊 {sucessos} OK | {skips} Skip | {erros} Erro")

print(f"\n🎉 FINAL: {sucessos}/{len(dois)}")
