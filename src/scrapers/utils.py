import time

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def parse_tophit_clean(driver, url, year, platform):
    cleaned_data = []
    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[class*='Row_row__']")))
        time.sleep(4)

        if str(year) not in driver.current_url:
            print(f"Skipping {platform.upper()} {year}: Redirected to {driver.current_url}")
            return []

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        rows = soup.find_all('div', class_=lambda x: x and 'Row_row__' in x)

        for row in rows:
            track_box = row.find('div', class_=lambda x: x and 'TrackName_container__' in x)
            song_name, artist_name = "", "unknown"
            
            if track_box:
                lines = list(track_box.stripped_strings)
                if len(lines) >= 2:
                    song_name, artist_name = lines[0], lines[1]
                elif len(lines) == 1:
                    song_name = lines[0]

            date_box = row.find('div', class_=lambda x: x and 'Row_date__' in x)
            release_date = date_box.get_text(strip=True) if date_box else ""

            lang_box = row.find('div', class_=lambda x: x and 'Row_language__' in x)
            span_tag = lang_box.find('span', title=True) if lang_box else None
            language = span_tag['title'] if span_tag else (lang_box.get_text(strip=True) if lang_box else "")

            if song_name:
                cleaned_data.append({
                    'year': year, 'platform': platform, 'artist_name': artist_name,
                    'song_name': song_name, 'release_date': release_date, 'language': language.lower()
                })

    except Exception as e:
        print(f"Error on {url}: {e}")

    return cleaned_data