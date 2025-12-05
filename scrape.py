import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

# --- KONFIGURASI ---
LIST_URL = "https://www.komdigi.go.id/berita/berita-hoaks"
CSV_FILE = "hoax_data_complete.csv"
MAX_PAGES = 1298

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def remove_widgets(driver):
    try:
        driver.execute_script("""
            var selectors = ['#widget_menu_disabilitas', '#hm-wrapper-translator', '.circle_aksesbilitas_popup', 'nav.fixed'];
            selectors.forEach(s => { var el = document.querySelector(s); if(el) el.remove(); });
        """)
    except: pass

def visualize_click_point(driver, element):
    try:
        driver.execute_script("arguments[0].style.border = '2px solid red';", element)
        time.sleep(0.5)
    except: pass

def run_step_1(driver, max_pages):
    existing_urls = set()
    all_data = []
    
    # Cek jika file sudah ada untuk resume/append
    if os.path.exists(CSV_FILE):
        try:
            df_exist = pd.read_csv(CSV_FILE)
            existing_urls = set(df_exist['url'].tolist())
            all_data = df_exist.to_dict('records')
            print(f"Loaded {len(existing_urls)} existing data.")
        except: pass

    print(f"Mengunjungi: {LIST_URL}")
    driver.get(LIST_URL)
    time.sleep(5) 

    current_page = 1
    
    while current_page <= max_pages:
        print(f"\n=== [STEP 1] Halaman {current_page} dari {max_pages} ===")
        remove_widgets(driver)

        # --- 1. SCRAPE LIST DATA ---
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.grid.lg\\:grid-cols-3")))
            articles = driver.find_elements(By.CSS_SELECTOR, "div.grid.lg\\:grid-cols-3 > div.flex.flex-col")
            
            count_new = 0
            for article in articles:
                try:
                    link_el = article.find_element(By.TAG_NAME, "a")
                    url = link_el.get_attribute("href")
                    title = link_el.text

                    if url in existing_urls: continue

                    try:
                        date = article.find_elements(By.CSS_SELECTOR, "div.font-medium span")[-1].text
                    except: date = "-"

                    # Simpan data awal, content diset None
                    all_data.append({
                        'title': title, 'date': date, 'url': url,
                        'content': None, 'scraped_at': time.strftime("%Y-%m-%d")
                    })
                    existing_urls.add(url)
                    count_new += 1
                except: continue
            
            print(f"   [+] Menyimpan {count_new} URL baru.")
            pd.DataFrame(all_data).to_csv(CSV_FILE, index=False)

        except Exception as e:
            print(f"[ERROR Scraping List]: {e}")

        # --- 2. NAVIGASI (NEXT PAGE) ---
        if current_page < max_pages:
            try:
                # XPath Fingerprint SVG (Tetap dipakai karena akurat)
                xpath_fingerprint = "//*[name()='path' and contains(@d, 'M10.2 9L13.8')]/ancestor::button"
                candidates = driver.find_elements(By.XPATH, xpath_fingerprint)
                
                if not candidates:
                    print("[INFO] Tombol Next tidak ditemukan (End of pages).")
                    break
                
                next_btn = candidates[-1]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", next_btn)
                time.sleep(1)
                visualize_click_point(driver, next_btn)

                actions = ActionChains(driver)
                actions.move_to_element(next_btn).click().perform()
                
                print(">> Next clicked, waiting reload...")
                time.sleep(5) 
                current_page += 1

            except Exception as e:
                print(f"[ERROR Navigasi]: {e}")
                break
        else:
            print("Mencapai batas halaman maksimum.")
            break

if __name__ == "__main__":
    driver = setup_driver()
    try:
        run_step_1(driver, MAX_PAGES)
    finally:
        driver.quit()

