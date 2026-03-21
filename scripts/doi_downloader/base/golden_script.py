from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re

download_dir = r"C:\Users\Luís Pinto Coelho\Desktop\Dissertação\metanalysis development\2 - literature search & study screening\data\wos\pdf_files_3"
os.makedirs(download_dir, exist_ok=True)

def safe_filename(doi):
    return re.sub(r"[^\w\-_.]", "_", doi) + ".pdf"

def list_pdfs():
    return {f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")}

def download_pdf(doi, index, total):
    before_files = list_pdfs()
    
    options = Options()
    options.add_experimental_option('prefs', {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True
    })
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    actions = ActionChains(driver)
    
    print(f"\n🔥 [{index}/{total}] {doi}")
    driver.get(f"https://sci-hub.box/{doi}")
    time.sleep(5)
    
    if "não tenho" in driver.page_source.lower():
        print("🚫 Skip")
        driver.quit()
        return False
    
    # Clica link PDF (que funciona)
    try:
        link = driver.find_element(By.CSS_SELECTOR, "a[href*='.pdf']")
        link.click()
        print("✅ Link PDF")
    except:
        print("❌ Sem link")
        driver.quit()
        return False
    
    time.sleep(4)  # Download bar aparece
    
    # 🎯 CLICA "ABRIR" por coordenadas (canto download bar)
    try:
        # Download bar fica em ~90% altura, 50% largura (botão Abrir)
        size = driver.get_window_size()
        actions.move_to_location(size['width']*0.5, size['height']*0.9).click().perform()
        print("✅ ABRIR por posição!")
    except:
        print("⚠️ Sem clique posição")
    
    time.sleep(15)
    driver.quit()
    
    # Espera PDF final
    for _ in range(20):
        files = os.listdir(download_dir)
        pdfs = [f for f in files if f.endswith('.pdf')]
        if pdfs:
            newest = max(pdfs, key=lambda x: os.path.getmtime(os.path.join(download_dir, x)))
            final = safe_filename(doi)
            if newest != final:
                os.rename(os.path.join(download_dir, newest), os.path.join(download_dir, final))
            print(f"✅ {final}")
            return True
        time.sleep(1)
    
    print("❌ Timeout")
    return False

with open("dois.txt", "r") as f:
    dois = [l.strip() for l in f if l.strip()]

sucessos = 0
for i, doi in enumerate(dois, 1):
    if download_pdf(doi, i, len(dois)):
        sucessos += 1
    print(f"📊 {sucessos}/{i}")

print(f"\n🎉 {sucessos}/{len(dois)}")
