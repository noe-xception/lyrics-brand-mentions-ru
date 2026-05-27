import pandas as pd
import ast

def get_continuous_years(df):
    if df.empty or df['year'].dropna().empty: return []
    return list(range(int(df['year'].min()), int(df['year'].max()) + 1))

def build_bar_data(df, group_col, target_years):
    if df.empty or group_col not in df.columns: return {"years": target_years, "datasets": []}
    counts = df.drop_duplicates(subset=['matched_artist', 'matched_song', group_col]).groupby(['year', group_col]).size().unstack(fill_value=0)
    if counts.empty: return {"years": target_years, "datasets": []}
    
    counts = counts.reindex(target_years, fill_value=0)
    top_items = counts.sum().nlargest(10).index[::-1]
    return {"years": target_years, "datasets": [{"label": str(i).title(), "data": counts[i].tolist()} for i in top_items]}

def get_top_brands_chart(df):
    years = get_continuous_years(df)
    data = build_bar_data(df, 'brands', years)
    top_brands = [d['label'].lower() for d in data['datasets']][::-1] if data['datasets'] else []
    return data, top_brands, years

def get_top_brands_per_year(df, target_years, target_origins=None):
    if df.empty or 'parsed_brands' not in df.columns: return [[] for _ in target_years]
    unique_songs = df.drop_duplicates(subset=['matched_artist', 'matched_song'])
    res = []
    
    for y in target_years:
        year_df = unique_songs[unique_songs['year'] == y]
        counts = {}
        for brands in year_df['parsed_brands']:
            if not isinstance(brands, list): continue
            seen = set()
            for b in brands:
                norm, orig = b.get('brand'), b.get('origin')
                if norm and (not target_origins or orig in target_origins) and norm not in seen:
                    seen.add(norm)
                    counts[norm] = counts.get(norm, 0) + 1
        res.append([b[0] for b in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]])
    return res

def build_ratio_data(df, target_years, label, color, condition_fn, target_origins=None):
    if not target_years or df.empty: return {"years": target_years, "datasets": []}
    unique_songs = df.drop_duplicates(subset=['matched_artist', 'matched_song'])
    total_counts = unique_songs.groupby('year').size().reindex(target_years, fill_value=0)
    target_counts = unique_songs[unique_songs['parsed_brands'].apply(condition_fn)].groupby('year').size().reindex(target_years, fill_value=0)
    
    ratio = (target_counts / total_counts * 100).fillna(0).round(1)
    
    return {
        "years": target_years,
        "datasets": [{
            "label": label, "data": ratio.tolist(), "topBrands": get_top_brands_per_year(df, target_years, target_origins),
            "type": "line", "borderColor": color, "backgroundColor": color, "borderWidth": 2, "pointRadius": 4,
            "pointBackgroundColor": color, "pointBorderColor": "#fff", "pointBorderWidth": 1.5, "fill": False, "tension": 0.1
        }]
    }

def get_mtld_chart(df):
    if 'mtld' not in df.columns or df.empty: return {"labels": [], "datasets": []}
    mtld_series = df.drop_duplicates(subset=['matched_artist', 'matched_song']).dropna(subset=['mtld', 'chosen_genre']).groupby('chosen_genre')['mtld'].mean().sort_values(ascending=False).round(2)
    return {"labels": [str(g).title() for g in mtld_series.index], "datasets": [{"label": "avg mtld", "data": mtld_series.tolist()}]}

def get_genre_summary_data(orig_df, filtered_df):
    if orig_df.empty or 'chosen_genre' not in orig_df.columns: return []
    
    unique_songs = orig_df.drop_duplicates(subset=['matched_artist', 'matched_song']).copy()
    unique_songs['char_len'] = unique_songs['lyrics'].fillna('').apply(len)
    unique_songs['word_len'] = unique_songs['lyrics'].fillna('').apply(lambda x: len(x.split()))
    
    summary = []
    for g in unique_songs['chosen_genre'].dropna().unique():
        g_songs = unique_songs[unique_songs['chosen_genre'] == g]
        total = len(g_songs)
        if total == 0: continue
        
        mentions = len(filtered_df[filtered_df['chosen_genre'] == g]['brands'].dropna())
        pct = round((g_songs['parsed_brands'].astype(bool).sum() / total * 100), 1)
        
        summary.append({
            "genre": str(g).title(), "total_songs": total, "total_mentions": mentions, "mentions_percent": f"{pct}%",
            "chars_stats": f"{int(g_songs['char_len'].min())} / {int(g_songs['char_len'].median())} / {int(g_songs['char_len'].max())}",
            "words_stats": f"{int(g_songs['word_len'].min())} / {int(g_songs['word_len'].median())} / {int(g_songs['word_len'].max())}"
        })
    return sorted(summary, key=lambda x: x['total_songs'], reverse=True)

def get_brand_forms_data(df):
    if df.empty or 'brands' not in df.columns or 'mentions' not in df.columns: return []

    temp_df = df.copy()
    # capitalize forms to merge
    mentions_series = temp_df['mentions'].fillna(temp_df['brands']).astype(str)
    temp_df['mentions_cap'] = mentions_series.str.capitalize()
    
    # deduplicate tracking 1 unique
    unique_brand_song = temp_df.drop_duplicates(subset=['matched_artist', 'matched_song', 'brands', 'mentions_cap'])

    brand_stats = {}
    for _, row in unique_brand_song.iterrows():
        b = row['brands']
        m = row['mentions_cap']
        c = row.get('categories', 'other')
        
        if pd.isna(b) or b == 'unknown': continue
        
        if b not in brand_stats:
            brand_stats[b] = {'songs': set(), 'forms': {}, 'category': c}
            
        brand_stats[b]['songs'].add((row['matched_artist'], row['matched_song']))
        brand_stats[b]['forms'][m] = brand_stats[b]['forms'].get(m, 0) + 1

    res = []
    for b, data in brand_stats.items():
        sorted_forms = sorted(data['forms'].items(), key=lambda x: x[1], reverse=True)[:5]
        res.append({
            'brand': str(b),
            'category': str(data['category']).lower() if pd.notna(data['category']) else 'other',
            'total_songs': len(data['songs']),
            'top_forms': [{'form': str(f[0]), 'count': f[1]} for f in sorted_forms]
        })
        
    return sorted(res, key=lambda x: x['total_songs'], reverse=True)

def get_table_data_chart(df):
    cols = [c for c in ['year', 'platform', 'matched_artist', 'matched_song', 'chosen_genre', 'extracted_brands', 'lyrics'] if c in df.columns]
    table_df = df[cols].drop_duplicates(subset=['matched_artist', 'matched_song']).copy()
    
    def parse_brands(val):
        if pd.isna(val) or val == '[]': return []
        return ast.literal_eval(val) if isinstance(val, str) else val

    if 'extracted_brands' in table_df.columns:
        table_df['extracted_brands'] = table_df['extracted_brands'].apply(parse_brands)
        
    if 'year' in table_df.columns: table_df = table_df.sort_values(by='year', ascending=False)
    return table_df.fillna("").to_dict(orient='records')