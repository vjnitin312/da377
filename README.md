# Historical Weather Data Platform — India

An end-to-end interactive platform for historical weather data analysis
and visualization across 8 major Indian cities.

## Features

- 40,904 daily weather records (2010–2023) via Open-Meteo API
- 115-year IMD subdivision rainfall data (1901–2015)
- SQLite relational database (3 tables, ~4MB)
- 12 EDA charts + 6 statistical analysis charts
- 5 interactive Folium maps (markers, bubbles, heatmap)
- Streamlit web dashboard with live filters
- 90-day Prophet forecasts for all 8 cities

## Cities Covered

Chennai · Mumbai · Delhi · Kolkata · Bangalore · Hyderabad · Coimbatore · Jaipur

## Quick Start
```bash
git clone https://github.com/YOUR_USERNAME/da377.git
cd da377
python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Project Structure
```
da377/
├── raw_data/          Original datasets
├── cleaned_data/      Cleaned CSVs
├── plots/             28 analysis charts
├── maps/              5 interactive HTML maps
├── reports/           Project report + forecast CSV
├── scripts/           11 Python scripts
├── app.py             Streamlit dashboard
├── weather_india.db   SQLite database
└── requirements.txt
```

## Tech Stack

Python 3.12 · pandas · SQLite · Streamlit · Plotly · Folium · Prophet · Matplotlib

## Data Sources

- [Open-Meteo API](https://open-meteo.com/) — free historical weather API
- [data.gov.in](https://data.gov.in/catalog/rainfall-india) — IMD rainfall data

## Key Findings

- Chennai is the hottest city (31.79°C avg max), Bangalore the coolest (28.45°C)
- Mumbai receives the most extreme rainfall — 112 days >50mm over 14 years
- Chennai follows Northeast monsoon (onset August), all others Southwest (June)
- India's wettest decade was the 1930s (1485mm); declining trend post-1960
- Humidity and temperature range are strongly negatively correlated (−0.81)
