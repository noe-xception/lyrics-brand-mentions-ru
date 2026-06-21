
import pandas as pd

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from typing import List

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)


def parse_pg_songs_universal(urls: List[str]) -> pd.DataFrame:
    data = []
    
    for url in urls:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        year_match = re.search(r'pesnja_(\d{4})', url)
        year = int(year_match.group(1)) if year_match else None
        
        wrapper = soup.select_one('.page-content-wrapper')
        if not wrapper:
            continue
            
        for br in wrapper.find_all('br'):
            br.replace_with('\n')
        for tag in wrapper.find_all(['p', 'li', 'ul', 'div', 'h1', 'h2', 'h3']):
            tag.insert_before('\n')
            tag.insert_after('\n')
            
        raw_text = wrapper.get_text(separator=' ')
        lines = [
            re.sub(r'\s+', ' ', line).strip() 
            for line in raw_text.split('\n') 
            if line.strip() and "Песня года" not in line
        ]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            check_line = re.sub(r'\s+\d+$', '', line)
            check_line = re.sub(r'\s*\([^)]*\)$', '', check_line).strip()
            
            is_combined = False
            if re.search(r'\s+[-–—]\s+', check_line):
                if i + 1 < len(lines):
                    next_check = re.sub(r'\s+\d+$', '', lines[i+1])
                    next_check = re.sub(r'\s*\([^)]*\)$', '', next_check).strip()
                    
                    if re.search(r'\s+[-–—]\s+', next_check) or \
                       ('(' in line and ')' in line and line.rfind(')') > line.rfind('-')) or \
                       re.match(r'^\d+\s+', line):
                        is_combined = True
                else:
                    is_combined = True
                    
            if is_combined:
                parts = re.split(r'\s+[-–—]\s+', line, maxsplit=1)
                artist = re.sub(r'^\d+\s+', '', parts[0]).strip()
                song = parts[1].strip() if len(parts) > 1 else ""
            else:
                song = line
                artist = lines[i+1] if i + 1 < len(lines) else "unknown"
                i += 1
                
            song = re.sub(r'\s+\d+$|\s*\([^)]*\)$', '', song).strip()
            artist = re.sub(r'\s+\d+$|\s*\([^)]*\)$', '', artist).strip()
            
            data.append((year, 'song of the year', artist, song, None, 'russian'))
            i += 1
            
    cols = ['year', 'platform', 'artist_name', 'song_name', 'release_date', 'language']
    return pd.DataFrame(data, columns=cols)


urls_to_parse = [
    'https://pg.ucoz.org/index/pesnja_2012/0-54',
    'https://pg.ucoz.org/index/pesnja_2011/0-49',
    'https://pg.ucoz.org/index/pesnja_2010/0-48',
    'https://pg.ucoz.org/index/pesnja_2009/0-47',
    'https://pg.ucoz.org/index/pesnja_2008/0-46',
    'https://pg.ucoz.org/index/pesnja_2007/0-45',
    'https://pg.ucoz.org/index/pesnja_2006/0-44',
    'https://pg.ucoz.org/index/pesnja_2005/0-43',
    'https://pg.ucoz.org/index/pesnja_2004/0-42',
    'https://pg.ucoz.org/index/pesnja_2003/0-41',
    'https://pg.ucoz.org/index/pesnja_2002/0-40',
    'https://pg.ucoz.org/index/pesnja_2001/0-39',
    'https://pg.ucoz.org/index/pesnja_2000/0-38',
    'https://pg.ucoz.org/index/pesnja_1999/0-37',
    'http://pg.ucoz.org/index/pesnja_1998/0-36',
    'https://pg.ucoz.org/index/pesnja_1997/0-35',
    'https://pg.ucoz.org/index/pesnja_1996/0-34',
    'https://pg.ucoz.org/index/pesnja_1995/0-33',
    'https://pg.ucoz.org/index/pesnja_1994/0-32',
    'https://pg.ucoz.org/index/pesnja_1993/0-31',
    'https://pg.ucoz.org/index/pesnja_1991/0-29',
]

df = parse_pg_songs_universal(urls_to_parse)
df.to_csv('song_of_the_year_charts/song_of_the_year_master_not_cleared.csv', index=False)


def clean_artist(name):
    name = str(name)
    name = re.sub(r'^[\d\s\.\-\)]+', '', name)
    name = re.sub(r'(?i)^(Группы\s+|Группа\s+|ВИА\s+|Кабарэ-дуэт\s+|Дуэт\s+|Ансамбль\s+)', '', name)
    name = name.replace('"', '')
    name = name.replace("'", "")
    
    name = re.split(r'(?i)\s+(feat\.?|ft\.?|при уч\.?|при участии)\s+', name)[0]
    
    name = re.sub(r'\s+и\s+', ', ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()

def clean_song(name):
    name = str(name)
    name = re.sub(r'^[\d\s\.\-\)]+', '', name)
    name = name.replace('"', '')
    name = name.replace("'", "")
    
    def replace_parens(match):
        content = match.group(0)
        return content if re.search(r'(?i)remix|acoustic', content) else ''
    
    name = re.sub(r'\(.*?\)', replace_parens, name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title()


df['artist_name'] = df['artist_name'].apply(clean_artist)
df['song_name'] = df['song_name'].apply(clean_song)

df.to_csv('song_of_the_year_charts/song_of_the_year_master_not_cleared.csv', index=False)
