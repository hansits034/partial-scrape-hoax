import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ==========================================
# --- KONFIGURASI BATCH (GANTI DI SINI) ---
# ==========================================
# Batch 1: 0 sampai 4000
# Batch 2: 4000 sampai 8000
# Batch 3: 8000 sampai 12000, dst...
BATCH_START = 50     
BATCH_END   = 5000  

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

def run_step_2_batch(driver):
    if not os.path.exists(CSV_FILE):
        print(f"File {CSV_FILE} tidak ditemukan.")
        return

    df = pd.read_csv(CSV_FILE)
    total_rows = len(df)
    
    # Pastikan range tidak melebihi jumlah data
    real_end = min(BATCH_END, total_rows)
    
    print(f"\n=== MODE BATCH ===")
    print(f"Total Data: {total_rows}")
    print(f"Target Batch: Baris {BATCH_START} sampai {real_end}")

    # Ambil index data yang content-nya masih kosong (NaN)
    empty_indices = df[df['content'].isnull()].index
    
    # FILTER: Hanya ambil index yang masuk dalam range BATCH_START s/d BATCH_END
    targets = [idx for idx in empty_indices if BATCH_START <= idx < real_end]
    
    if len(targets) == 0:
        print("✅ Batch ini sudah lengkap atau tidak ada data kosong di range ini.")
        return

    print(f"--> Akan memproses {len(targets)} URL di batch ini.\n")

    for i, idx in enumerate(targets):
        url = df.at[idx, 'url']
        print(f"[{i+1}/{len(targets)}] (Baris {idx}) {url}")
        
        try:
            driver.get(url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "custom-body")))
                content = driver.find_element(By.CLASS_NAME, "custom-body").text
                df.at[idx, 'content'] = content
                print("   -> OK: Tersimpan")
            except:
                print("   -> SKIP: Konten tidak muncul/Timeout")
                # Bisa diisi error flag jika mau, tapi dibiarkan kosong agar bisa diretry nanti
        except Exception as e:
            print(f"   -> ERROR: {e}")
        
        # Save setiap 10 data biar aman
        if (i+1) % 10 == 0:
            df.to_csv(CSV_FILE, index=False)
        
        time.sleep(1) 

    # Simpan hasil akhir batch
    df.to_csv(CSV_FILE, index=False)
    print(f"\n=== BATCH {BATCH_START}-{real_end} SELESAI DISIMPAN ===")

if __name__ == "__main__":
    driver = setup_driver()
    try:
        run_step_2_batch(driver)
    finally:
        driver.quit()
