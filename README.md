# Brand Vocabulary in Russian Popular Music Lyrics (1991-2025): A Corpus Study

**Degree**: Master's Project

---

## 1. Abstract
This research systematically identifies, catalogs, and analyzes brand name mentions within Russian popular music lyrics spanning from 1991 to 2025. The objective is to document cultural and economic shifts in post-Soviet consumer culture through the lens of popular music. By constructing a comprehensive lyrical corpus and deploying advanced Natural Language Processing (NLP) techniques, this project maps the evolution of brand integration, revealing critical insights into consumer behavior, linguistic assimilation, and the resilience of status-driven cultural signifiers amid macroeconomic turbulence.

## 2. Project Architecture
The repository is modularly structured to ensure clear separation of concerns, reproducibility, and scalability of the computational pipeline.

```text
lyrics-brand-mentions-ru/
├── data/                  # Raw and processed datasets, including aggregated charts and enriched text data
├── notebooks/             # Exploratory Data Analysis (EDA), data cleaning prototypes, and parser logic
│   ├── data_clean.ipynb
│   └── parse_*.ipynb
└── src/                   # Core reproducible pipeline and application logic
    ├── app/               # Interactive Flask-based web dashboard for longitudinal trend mapping
    │   ├── app.py
    │   ├── charts_logic.py
    │   └── static/ & templates/
    ├── data_pipeline/     # Scripts for rigorous data cleaning and metadata enrichment
    │   └── data_clean.py
    └── scrapers/          # Automated extraction tools for historical and digital streaming charts
        ├── parse_master.py
        ├── parse_song_of_the_year.py
        └── parse_tophit.py
```

## 3. Methodology & Computational Pipeline
The research employs a highly structured computational pipeline divided into five distinct phases, emphasizing methodological rigor and data integrity:

1. **Chart Aggregation**: Aggregated chart-topping tracks by systematically combining historical television broadcast records (1991-2012) with modern digital streaming metrics (2003-2025) to ensure a holistic longitudinal representation of popularity.
2. **Automated Lyrics Retrieval**: Implemented an automated, multi-tiered data retrieval system that utilized AI-assisted alias generation. This successfully resolved persistent transliteration and metadata inconsistencies across varying source datasets.
3. **Context-Aware Named Entity Recognition (NER)**: Deployed Large Language Models (LLMs) to perform complex entity extraction. This enabled the accurate identification of informal slang and creative morphology, effectively normalizing highly variable commercial mentions into their primary corporate parents.
4. **Metadata Enrichment**: Cross-referenced overarching genre classifications across multiple external databases. Furthermore, the Measure of Textual Lexical Diversity (MTLD) was computed on lemmatized lyrics to establish a standardized baseline for vocabulary richness across different musical epochs and genres.
5. **Data Structuring and Visualization**: Developed a structured computational pipeline and an interactive web dashboard (via Flask) to map longitudinal trends. This interface includes dynamic capabilities to highlight extracted brand entities directly within the lyrical texts, facilitating exploratory qualitative analysis.

## 4. Key Empirical Findings
Quantitative and qualitative analysis of the assembled corpus yielded several significant sociological and linguistic insights:

*   **Genre Stratification**: The Rap genre demonstrates the highest rate of brand inclusion (37.7%) alongside the highest average lexical diversity. In stark contrast, the Pop genre, while constituting the bulk of the overall corpus, contains a negligible brand inclusion rate (4.2%) and the lowest lexical diversity metric.
*   **Dominant Entities**: Western commercial entities completely dominate the lyrical landscape. The four most frequently mentioned brands across the entire timeline are **Mercedes-Benz**, **BMW**, **Apple**, and **Gucci**.
*   **Sanctions Resilience**: Despite severe economic isolation and the formal withdrawal of Western businesses from the Russian Federation post-2022, lyrical mentions of Western luxury brands stabilized at their highest recorded levels. This phenomenon indicates that status culture and the symbolic use of these commercial entities remain deeply ingrained, decoupled from immediate economic availability.

## 5. Reproducibility & Setup

To reproduce the environment and interact with the data pipeline and visualization dashboard, follow these steps:

### Prerequisites
*   Python 3.9+ (or highly recommended version based on dependencies)
*   Standard scientific computing stack (Pandas, Flask, etc.)

### Environment Setup
It is highly recommended to isolate the project dependencies using a Python virtual environment.

```bash
# 1. Clone the repository
git clone https://github.com/noe-xception/lyrics-brand-mentions-ru
cd lyrics-brand-mentions-ru

# 2. Activate the existing virtual environment (macOS/Linux)
source .venv/bin/activate
# Note: If creating a new environment: python -m venv .venv && source .venv/bin/activate

# 3. Install required dependencies
# pip install -r requirements.txt
```

### Execution Steps
1. **Data Scraping & Cleaning Pipeline**: 
   Navigate to the `src/scrapers/` directory to execute data extraction modules (e.g., `parse_master.py`), or use the Jupyter notebooks inside `notebooks/` to review the interactive parsing and cleaning processes.
2. **Launch the Dashboard**:
   The interactive visualizations and lyrical analysis tools can be explored via the included web application.
   ```bash
   cd src/app
   python app.py
   ```
   *The dashboard will be served locally on port 5001 (e.g., `http://localhost:5001` or `http://127.0.0.1:5001`).*
