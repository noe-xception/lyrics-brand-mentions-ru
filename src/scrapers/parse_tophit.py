
import os
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from utils import parse_tophit_clean

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


current_year = datetime.now().year
recent_years = list(range(2025, current_year + 1))

available_charts = {
    "apple": recent_years,
    "itunes": recent_years, 
    "radio": list(range(2003, current_year + 1)),
    "shazam": recent_years,
    "vk": recent_years, 
    "yandex": recent_years, 
    "youtube": list(range(2018, current_year + 1)),
    "zvuk": recent_years
}

output_dir = "tophit_charts"
os.makedirs(output_dir, exist_ok=True)

opts = Options()
opts.add_argument("--headless") 
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")
opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
all_data = []

try:
    for platform, years in available_charts.items():
        for year in years:
            url = f"https://tophit.ru/chart/top/{platform}/hits/ru/annual/{year}"
            print(f"Processing: {platform.upper()} {year}")
            
            all_data.extend(parse_tophit_clean(driver, url, year, platform))
finally:
    driver.quit()

df_master = pd.DataFrame(all_data)


if not df_master.empty:
    df_master.columns = df_master.columns.str.lower()
    
    if 'release_date' in df_master.columns:
        df_master['release_date'] = pd.to_datetime(df_master['release_date'], errors='coerce').dt.strftime('%Y-%m-%d')
        
    target_cols = ['year', 'platform', 'artist_name', 'song_name', 'release_date', 'language']
    for col in target_cols:
        if col not in df_master.columns:
            df_master[col] = 'russian' if col == 'language' else None
            
    df_master = df_master[target_cols]
    
    master_csv_path = os.path.join(output_dir, "tophit_master_all.csv")
    df_master.to_csv(master_csv_path, index=False, encoding='utf-8')
    print(f"\nFinished! Master DataFrame saved to '{master_csv_path}' with {len(df_master)} rows.")
