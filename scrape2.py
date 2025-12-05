import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURASI ---
CSV_FILE = "hoax_data_complete.csv"

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def run_step_2(driver):
    if not os.path.exists(CSV_FILE):
        print(f"File {CSV_FILE} tidak ditemukan. Jalankan Step 1 dulu.")
        return

    df = pd.read_csv(CSV_FILE)
    
    # Filter hanya data yang kolom 'content'-nya masih kosong (NaN)
    targets = df[df['content'].isnull()].index
    
    if len(targets) == 0:
        print("Semua data sudah memiliki konten. Tidak ada yang perlu di-scrape.")
        return

    print(f"\n=== [STEP 2] MENGAMBIL KONTEN ({len(targets)} Artikel) ===")

    for i, idx in enumerate(targets):
        url = df.at[idx, 'url']
        print(f"[{i+1}/{len(targets)}] Membuka: {url}")
        
        try:
            driver.get(url)
            try:
                # Menunggu elemen custom-body muncul
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "custom-body")))
                content_elem = driver.find_element(By.CLASS_NAME, "custom-body")
                
                # Mengambil text (opsional: bisa ambil innerHTML jika butuh format)
                content = content_elem.text
                
                df.at[idx, 'content'] = content
                print("   -> OK: Konten tersimpan.")
            except:
                print("   -> FAIL: Konten tidak ditemukan/Timeout.")
                # Kita biarkan kosong agar bisa dicoba lagi nanti, 
                # atau set "ERR" jika ingin skip di run berikutnya.
                # df.at[idx, 'content'] = "ERR_TIMEOUT" 

        except Exception as e:
            print(f"   -> ERROR Link: {e}")
        
        # Simpan setiap 5 data agar aman jika crash
        if (i+1) % 5 == 0:
            df.to_csv(CSV_FILE, index=False)
            print("   (Data disimpan ke CSV)")
        
        # Delay sopan
        time.sleep(2)

    # Simpan final
    df.to_csv(CSV_FILE, index=False)
    print("\n=== STEP 2 SELESAI ===")

if __name__ == "__main__":
    driver = setup_driver()
    try:
        run_step_2(driver)
    finally:
        driver.quit()
