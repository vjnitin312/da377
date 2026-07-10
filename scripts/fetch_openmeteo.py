import requests
import pandas as pd
import os

os.makedirs("raw_data", exist_ok=True)

cities = {
    "Chennai":    {"lat": 13.08, "lon": 80.27},
    "Mumbai":     {"lat": 19.07, "lon": 72.87},
    "Delhi":      {"lat": 28.61, "lon": 77.20},
    "Kolkata":    {"lat": 22.57, "lon": 88.36},
    "Bangalore":  {"lat": 12.97, "lon": 77.59},
    "Hyderabad":  {"lat": 17.38, "lon": 78.48},
    "Coimbatore": {"lat": 11.00, "lon": 76.96},
    "Jaipur":     {"lat": 26.91, "lon": 75.78},
}

variables = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "windspeed_10m_max",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
]

start_date = "2010-01-01"
end_date   = "2023-12-31"
BASE_URL   = "https://archive-api.open-meteo.com/v1/archive"

all_data = []

for city, coords in cities.items():
    print(f"Fetching data for {city}...")
    params = {
        "latitude":   coords["lat"],
        "longitude":  coords["lon"],
        "start_date": start_date,
        "end_date":   end_date,
        "daily":      ",".join(variables),
        "timezone":   "Asia/Kolkata",
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        print(f"  ERROR: {response.status_code}")
        continue
    data = response.json()
    df = pd.DataFrame(data["daily"])
    df["city"]      = city
    df["latitude"]  = coords["lat"]
    df["longitude"] = coords["lon"]
    all_data.append(df)
    print(f"  Done. Rows: {len(df)}")

final_df = pd.concat(all_data, ignore_index=True)
final_df.rename(columns={"time": "date"}, inplace=True)
output_path = "raw_data/india_weather_raw.csv"
final_df.to_csv(output_path, index=False)

print(f"\nSaved to: {output_path}")
print(f"Total rows: {len(final_df)}")
print(f"Columns: {list(final_df.columns)}")
print("\nPreview:")
print(final_df.head(5))
