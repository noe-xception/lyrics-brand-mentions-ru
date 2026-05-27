from flask import Flask, render_template, request, jsonify
import pandas as pd
import ast
import charts_logic 

import os

app = Flask(__name__)

# load data
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
data_path = os.path.join(BASE_DIR, 'data', 'processed', 'dashboard_data', 'df_genres v2.csv')
df = pd.read_csv(data_path)
df['year'] = pd.to_datetime(df['year'], format='mixed', errors='coerce').dt.year
df = df[df['year'] <= 2025]

def parse_brand_data(val):
    if pd.isna(val) or val == '[]': return []
    try:
        return [{'brand': b.get('normalized'), 'category': b.get('category', 'other'), 'origin': b.get('origin', 'unknown'), 'mention': b.get('mention', b.get('normalized'))} 
                for b in ast.literal_eval(val) if b.get('normalized')]
    except: return []

df['parsed_brands'] = df['extracted_brands'].apply(parse_brand_data)
df_exploded = df.explode('parsed_brands').dropna(subset=['parsed_brands', 'year', 'platform', 'matched_artist', 'matched_song', 'chosen_genre', 'lyrics'])

df_exploded['brands'] = df_exploded['parsed_brands'].apply(lambda x: x.get('brand'))
df_exploded['categories'] = df_exploded['parsed_brands'].apply(lambda x: x.get('category'))
df_exploded['origins'] = df_exploded['parsed_brands'].apply(lambda x: x.get('origin'))
df_exploded['mentions'] = df_exploded['parsed_brands'].apply(lambda x: x.get('mention'))
df_exploded.drop(columns=['parsed_brands'], inplace=True)

@app.route('/')
def home():
    lists = {k: sorted([str(i) for i in df_exploded[k].dropna().unique() if str(i).strip() and str(i) != 'unknown']) 
             for k in ['chosen_genre', 'platform', 'brands', 'categories', 'origins']}
    return render_template('index.html', genres=lists['chosen_genre'], platforms=lists['platform'], 
                           brands=lists['brands'], categories=lists['categories'], origins=lists['origins'])

@app.route('/api/data')
def get_chart_data():
    filters = {
        'chosen_genre': request.args.get('genre', 'all'),
        'platform': request.args.get('platform', 'all'),
        'brands': request.args.get('brand', 'all'),
        'categories': request.args.get('category', 'all'),
        'origins': request.args.get('origin', 'all')
    }
    
    # filter
    orig_df, filt_df = df.copy(), df_exploded.copy()
    for col, val in filters.items():
        if val != 'all':
            if col in orig_df.columns: orig_df = orig_df[orig_df[col] == val]
            if col in filt_df.columns: filt_df = filt_df[filt_df[col] == val]

    # build charts
    g1, top_brands, yrs = charts_logic.get_top_brands_chart(filt_df)
    
    return jsonify({
        "graph1": g1, 
        "graph2": charts_logic.build_bar_data(filt_df, 'chosen_genre', yrs),
        "graph3": charts_logic.build_bar_data(filt_df, 'categories', yrs),
        "graph4": charts_logic.build_ratio_data(orig_df, yrs, "% of Songs w/ Brands", "#decbe4", lambda x: bool(x)),
        "graph5": charts_logic.build_ratio_data(orig_df, yrs, "% Western/Abroad Brands", "#b3cde0", lambda x: any(b.get('origin') in ['Western/Abroad'] for b in x) if isinstance(x, list) else False, ['Western/Abroad']),
        "graph6": charts_logic.build_ratio_data(orig_df, yrs, "% Domestic/CIS Brands", "#fbb4ae", lambda x: any(b.get('origin') in ['Domestic', 'CIS'] for b in x) if isinstance(x, list) else False, ['Domestic', 'CIS']),
        "graph7": charts_logic.get_mtld_chart(orig_df),
        "summary_data": charts_logic.get_genre_summary_data(orig_df, filt_df),
        "brand_forms_data": charts_logic.get_brand_forms_data(filt_df),
        "table_data": charts_logic.get_table_data_chart(filt_df)
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)