# Brand Vocabulary in Russian Popular Music Lyrics (1991-2025): A Corpus Study

**Degree**: Master's Project

---

## 1. Abstract
This research identifies, catalogs, and analyzes brand name mentions in Russian popular music lyrics from 1991 to 2025. The goal is to observe changes in post-Soviet consumer culture through popular music. By building a lyrics corpus and using Natural Language Processing (NLP) methods, this project tracks how brand mentions change over time, showing trends in consumer behavior and the use of status symbols during economic shifts.

## 2. Project Architecture
The repository is organized to separate data, analysis, and application code.

```text
lyrics-brand-mentions-ru/
├── data/                  # raw and processed datasets, aggregated charts, and text data
├── notebooks/             # exploratory data analysis and data cleaning prototypes
│   ├── data_clean.ipynb
│   └── parse_*.ipynb
└── src/                   # main pipeline and application code
    ├── app/               # flask web dashboard for viewing data trends
    │   ├── app.py
    │   ├── charts_logic.py
    │   └── static/ & templates/
    ├── data_pipeline/     # scripts for data cleaning and adding metadata
    │   └── data_clean.py
    └── scrapers/          # scripts to collect chart data
        ├── parse_master.py
        ├── parse_song_of_the_year.py
        └── parse_tophit.py
```

## 3. Methodology & Computational Pipeline
The research uses a data pipeline divided into five steps:

1. **Chart Aggregation**: Combined historical television records (1991-2012) and digital streaming data (2003-2025) to identify popular tracks.
2. **Data Retrieval**: Used an automated system with alias generation to fix transliteration and metadata issues across different data sources.
3. **Named Entity Recognition (NER)**: Used Large Language Models (LLMs) to extract brand entities. This helped group informal slang and different spellings under their main brand names.
4. **Metadata Processing**: Added genre classifications from external databases. Calculated the Measure of Textual Lexical Diversity (MTLD) on lemmatized lyrics to measure vocabulary richness.
5. **Data Structuring and Visualization**: Built a data pipeline and a Flask web dashboard to display trends over time. The dashboard highlights brand mentions directly in the lyrics.

## 4. Key Findings
Analysis of the corpus shows the following patterns:

* **Genre Differences**: The Rap genre has the highest rate of brand mentions (37.7%) and the highest average lexical diversity. The Pop genre makes up most of the dataset but has a low brand mention rate (4.2%) and the lowest lexical diversity.
* **Frequent Brands**: Western brands are the most common in the lyrics. The four most mentioned brands across the studied period are Mercedes-Benz, BMW, Apple, and Gucci.
* **Post-2022 Trends**: Despite economic changes and the withdrawal of Western businesses after 2022, mentions of Western luxury brands remained at high levels.

## 5. Setup and Execution

To set up the project and run the dashboard, follow these steps:

### Prerequisites
* Python 3.9+
* Required packages (Pandas, Flask, etc.)

### Environment Setup
Use a Python virtual environment to isolate project dependencies.

```bash
# 1. clone the repository
git clone https://github.com/noe-xception/lyrics-brand-mentions-ru
cd lyrics-brand-mentions-ru

# 2. activate the virtual environment (macos/linux)
source .venv/bin/activate
# to create a new environment: python -m venv .venv && source .venv/bin/activate

# 3. install dependencies
# pip install -r requirements.txt
```

### Execution Steps
1. **Data Collection and Cleaning**: 
   Go to the `src/scrapers/` folder to run data extraction scripts (e.g., `parse_master.py`), or use the Jupyter notebooks in `notebooks/` to review the data cleaning steps.
2. **Launch the Dashboard**:
   You can view the data analysis through the web application.
   ```bash
   cd src/app
   python app.py
   ```
   *The dashboard will run locally on port 5001 (e.g., `http://localhost:5001` or `http://127.0.0.1:5001`).*
