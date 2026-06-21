
import os
import re
import json
import time
import requests
import numpy as np
import pandas as pd
from typing import Optional, Tuple
from tqdm import tqdm
from openai import OpenAI
from lyricsgenius import Genius

# python 3.11+ compatibility patch
import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = lambda f: inspect.getfullargspec(f)[:4]
import pymorphy2

# setup display config
pd.set_option('display.max_columns', None)
tqdm.pandas(desc="processing data")

morph = pymorphy2.MorphAnalyzer()


# init api clients
ai_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-4c355f2d8d8c4885a616da01b419ad53"),
    base_url="https://api.deepseek.com"
)
genius = Genius(
    os.getenv("GENIUS_API_KEY", "JNKpGBtCKFm_E6_idil9o-Ew-rfzMDiQyPET8Iz9-ZXbdwa-GjcR7ScekF0WQmls"),
    timeout=15, retries=3, verbose=False
)
genius.remove_section_headers = True
lastfm_key = os.getenv("LASTFM_API_KEY", "e230cd7998903ddb5876beb486e82ee2")


# genre maps
genre_map = {
    'folk': 'folk', 'electronics': 'electronics', 'caucasian': 'caucasian',
    'rusrock': 'rock', 'rock': 'rock', 'dance': 'dance', 'rusrap': 'rap',
    'rap': 'rap', 'rusestrada': 'estrada', 'estrada': 'estrada',
    'ruspop': 'pop', 'pop': 'pop'
}
genre_priority = ['folk', 'electronics', 'caucasian', 'rock', 'dance', 'rap', 'estrada', 'pop']


def get_lyrics(artist: str, song: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    # search via yandex
    try:
        headers = {"X-Yandex-Music-Client": "YandexMusicAndroid/24023231"}
        search_res = requests.get(
            "https://api.music.yandex.net/search", 
            params={"text": f"{artist} {song}", "type": "track", "page": 0},
            headers=headers,
            timeout=1
        )
        if search_res.status_code == 200:
            tracks = search_res.json().get("result", {}).get("tracks", {}).get("results", [])
            if tracks and tracks[0].get("id"):
                track_id = tracks[0]["id"]
                supp_res = requests.get(
                    f"https://api.music.yandex.net/tracks/{track_id}/supplement",
                    headers=headers,
                    timeout=1
                )
                if supp_res.status_code == 200:
                    lyrics = supp_res.json().get("result", {}).get("lyrics", {}).get("fullLyrics")
                    if lyrics:
                        return lyrics, "yandex", track_id
    except Exception:
        pass

    # search via genius
    try:
        if song_data := genius.search_song(title=song, artist=artist):
            if song_data.lyrics:
                return song_data.lyrics, "genius", song_data.id
    except Exception:
        pass
    
    # fallback to lrclib
    try:
        res = requests.get("https://lrclib.net/api/get", params={"artist_name": artist, "track_name": song}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return data.get("plainLyrics"), "lrclib", data.get("id")
    except requests.RequestException:
        pass
        
    return None, None, None


def get_ai_aliases(artist: str, song: str) -> list[Tuple[str, str]]:
    # llm data cleaning
    prompt = (
        f"Raw Artist: '{artist}', Raw Song: '{song}'.\n"
        "The input data is often messy. Fix it to determine the true core artist and song name compatible with lyrics aggregators (Genius, Musixmatch).\n"
        "Resolve common issues such as:\n"
        "- Swapped artist and song names.\n"
        "- Extraneous quotes/brackets («») or metadata (e.g., 'Песня-82', years).\n"
        "- Multiple artists (extract ONLY the primary one).\n"
        "Generate up to 3 clean search combinations, including English aliases/transliterations (e.g., 'Уматурман' -> 'Uma2rman').\n"
        "Return ONLY JSON: {\"combinations\": [[\"Artist\", \"Song\"]]}"
    )
    try:
        resp = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content).get('combinations', [])
    except Exception:
        return []


def process_track(row: pd.Series) -> pd.Series:
    orig_art, orig_sng = str(row['artist_name']), str(row['song_name'])
    if orig_art == 'nan' or orig_sng == 'nan':
        return pd.Series([None, None, None, "not found", None, None])

    lyrics, source, source_id = get_lyrics(orig_art, orig_sng)
    if lyrics:
        return pd.Series([orig_art, orig_sng, "[]", lyrics, source, source_id])

    aliases = get_ai_aliases(orig_art, orig_sng)
    aliases_str = json.dumps(aliases, ensure_ascii=False) 

    for alt_art, alt_sng in aliases:
        time.sleep(0.5)
        lyrics, source, source_id = get_lyrics(alt_art, alt_sng)
        if lyrics:
            return pd.Series([alt_art, alt_sng, aliases_str, lyrics, source, source_id])

    return pd.Series([None, None, aliases_str, "not found", None, None])


import json

def extract_brands(lyrics: str, release_date: str) -> str:
    # extract brands
    if not isinstance(lyrics, str) or not lyrics.strip():
        return "[]"

    prompt = (
        "You are an expert linguistic analyst. Extract all brand names, companies, designers, "
        "car manufacturers, and tech companies mentioned in the provided lyrics. \n\n"
        "CRITICAL RULES:\n"
        "1. Identify official names, transliterations, abbreviations, and street slang.\n"
        "2. PARENT BRAND ONLY: Normalize to the core brand or parent company name. Do NOT include specific products, items, or models. "
        "For example, normalize to 'Apple' (not 'Apple MacBook' or 'iPhone'), and 'Porsche' (not 'Porsche Cayenne').\n"
        "3. TIME AWARENESS: The song's release date is provided below. Do NOT extract or hallucinate brands that did not exist on or before this date "
        "(e.g., do not identify 'TikTok' in a song from 2005).\n"
        "4. Examples of targets:\n"
        "   - Cars: гелик/мерс (Mercedes-Benz), бэха/бумер (BMW), порш/каен (Porsche), ваз/тазик (LADA), роллс (Rolls-Royce).\n"
        "   - Fashion: гучи/gucci (Gucci), луи/луи витон (Louis Vuitton), стоник (Stone Island), прада (Prada), баленсиага (Balenciaga).\n"
        "   - Tech/Other: айфон/мак (Apple), макдак (McDonald's), спрайт (Sprite), ролекс (Rolex).\n"
        "5. If no brands are found, return an empty list.\n\n"
        f"RELEASE DATE: {release_date}\n"
        f"LYRICS:\n{lyrics}\n\n"
        "Return ONLY JSON in this format: {\"brands\": [{\"mention\": \"exact word in text\", \"normalized\": \"Official Brand Name\"}]}"
    )
    
    try:
        resp = ai_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        brands = json.loads(resp.choices[0].message.content).get('brands', [])
        return json.dumps(brands, ensure_ascii=False)
    except Exception:
        return "[]"


def fetch_artist_genres(artist: str, lastfm_api_key: str) -> dict:
    # fetch genres
    genres = {'itunes': [], 'yandex': [], 'lastfm': [], 'musicbrainz': []}
    
    try:
        res = requests.get("https://itunes.apple.com/search", params={"term": artist, "entity": "musicArtist", "limit": 1}).json()
        if res.get("results") and "primaryGenreName" in res["results"][0]:
            genres['itunes'] = [res["results"][0]["primaryGenreName"]]
    except Exception: pass

    try:
        res = requests.get("https://api.music.yandex.net/search", params={"text": artist, "type": "artist", "page": 0}, headers={"X-Yandex-Music-Client": "YandexMusicAndroid/24023231"})
        if res.status_code == 200:
            artists_data = res.json().get("result", {}).get("artists", {}).get("results", [])
            if artists_data and "genres" in artists_data[0]:
                genres['yandex'] = [g.get("title", g) if isinstance(g, dict) else g for g in artists_data[0].get("genres", [])]
    except Exception: pass

    try:
        res = requests.get("https://ws.audioscrobbler.com/2.0/", params={"method": "artist.gettoptags", "artist": artist, "api_key": lastfm_api_key, "format": "json"}).json()
        tags = res.get("toptags", {}).get("tag", [])
        tags = [tags] if isinstance(tags, dict) else tags
        genres['lastfm'] = [tag.get("name") for tag in tags[:5]]
    except Exception: pass

    try:
        res = requests.get("https://musicbrainz.org/ws/2/artist", params={"query": artist, "limit": 1, "fmt": "json"}, headers={"User-Agent": "DataPipeline/1.0"}).json()
        if res.get("artists"):
            genres['musicbrainz'] = [tag.get("name") for tag in res["artists"][0].get("tags", [])]
    except Exception: pass

    return genres


def pick_best_genre(genres: list) -> str:
    if not isinstance(genres, list) or not genres:
        return 'other'
    mapped = [genre_map[g] for g in genres if g in genre_map]
    return min(mapped, key=lambda g: genre_priority.index(g)) if mapped else 'other'


def calc_mtld_side(tokens: list, ttr_thresh: float) -> float:
    # calc side mtld
    if not tokens:
        return 0.0
    types = set()
    factors = 0.0
    t_count = 0
    for token in tokens:
        t_count += 1
        types.add(token)
        ttr = len(types) / t_count
        if ttr < ttr_thresh:
            factors += 1
            types = set()
            t_count = 0
    if t_count > 0:
        ttr = len(types) / t_count
        factors += (1.0 - ttr) / (1.0 - ttr_thresh)
    return len(tokens) / factors if factors > 0 else 0.0

def get_mtld(lyrics: str, ttr_thresh: float = 0.72) -> float:
    # calc bidirectional mtld
    if not isinstance(lyrics, str) or not lyrics.strip():
        return 0.0
    # extract tokens
    raw_tokens = re.findall(r'(?u)\b\w+\b', lyrics.lower())
    if not raw_tokens:
        return 0.0
    # lemmatize tokens
    tokens = [morph.parse(token)[0].normal_form for token in raw_tokens]
    forward = calc_mtld_side(tokens, ttr_thresh)
    backward = calc_mtld_side(tokens[::-1], ttr_thresh)
    return (forward + backward) / 2.0


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # merge raw data
    df_tophit = pd.read_csv(os.path.join(BASE_DIR, "data", "raw", "tophit_charts", "tophit_master_all.csv")) # [:5]
    df_pg = pd.read_csv(os.path.join(BASE_DIR, "data", "raw", "song_of_the_year_charts", "song_of_the_year_master_not_cleared.csv")) # [:5]
    df = pd.concat([df_tophit, df_pg], ignore_index=True)
    df.columns = df.columns.str.lower()

    # clean initial data
    df = df.drop_duplicates(subset=['artist_name', 'song_name'])
    valid_mask = (
        ~df['artist_name'].astype(str).str.contains('unknown', case=False, na=False) &
        ~df['song_name'].astype(str).str.contains('unknown', case=False, na=False) &
        df['language'].astype(str).str.contains('russian', case=False, na=False)
    )
    df = df[valid_mask].reset_index(drop=True)

    # fetch lyrics
    new_cols = ['matched_artist', 'matched_song', 'ai_suggestions', 'lyrics', 'source', 'source_id']
    df[new_cols] = df.progress_apply(process_track, axis=1, result_type='expand')

    # clean lyrics text
    df['lyrics'] = df['lyrics'].str.replace(r'^\d+\s*Contributors?.*?Lyrics\s*', '', regex=True, flags=re.IGNORECASE)
    df_valid = df[df['lyrics'] != 'not found'].copy()

    # extract brands
    df_valid['extracted_brands'] = df_valid.progress_apply(
    lambda row: extract_brands(row['lyrics'], row['release_date']), 
    axis=1
    )

    # calc mtld
    df_valid['mtld'] = df_valid['lyrics'].apply(get_mtld)

    # fetch artist genres
    unique_artists = df_valid['matched_artist'].dropna().unique()
    genre_data = {}
    for artist in tqdm(unique_artists, desc="fetching genres"):
        genre_data[artist] = fetch_artist_genres(artist, lastfm_key)
        time.sleep(1)

    # map genres
    df_valid['genres_itunes'] = df_valid['matched_artist'].map(lambda a: genre_data.get(a, {}).get('itunes', []))
    df_valid['genres_yandex'] = df_valid['matched_artist'].map(lambda a: genre_data.get(a, {}).get('yandex', []))
    df_valid['genres_lastfm'] = df_valid['matched_artist'].map(lambda a: genre_data.get(a, {}).get('lastfm', []))
    df_valid['genres_musicbrainz'] = df_valid['matched_artist'].map(lambda a: genre_data.get(a, {}).get('musicbrainz', []))
    df_valid['chosen_genre'] = df_valid['genres_yandex'].apply(pick_best_genre)

    # format columns
    df_final = df_valid.assign(
        year=lambda x: x['release_date'].fillna(x['year']) if 'release_date' in x.columns else x['year'],
        genius_id=lambda x: np.where(x['source'] == 'genius', x['source_id'], np.nan),
        lrclib_id=lambda x: np.where(x['source'] == 'lrclib', x['source_id'], np.nan)
    ).rename(columns={
        'artist_name': 'raw_artist',
        'song_name': 'raw_song'
    })

    final_cols = [
        'year', 'platform', 'raw_artist', 'raw_song', 'matched_artist', 
        'matched_song', 'ai_suggestions', 'lyrics', 'genius_id', 'lrclib_id', 
        'genres_yandex', 'genres_musicbrainz', 'genres_itunes', 'genres_lastfm', 
        'chosen_genre', 'extracted_brands', 'mtld'
    ]
    
    # filter columns
    available_cols = [c for c in final_cols if c in df_final.columns]
    df_final = df_final[available_cols]

    # export to csv
    df_final.to_csv(os.path.join(BASE_DIR, "data", "processed", "final_processed_dataset.csv"), index=False, encoding='utf-8')
