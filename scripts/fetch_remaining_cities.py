import requests
import pandas as pd
import os
import time

# Only the 5 cities that failed
cities = {
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

    # Retry up to 3 times if rate-limited
    for attempt in range(3):
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            break
        elif response.status_code == 429:
            wait = 15 * (attempt + 1)
            print(f"  Rate limited. Waiting {wait} seconds...")
            time.sleep(wait)
        else:
            print(f"  ERROR: {response.status_code}")
            break

    if response.status_code != 200:
        print(f"  Skipping {city} after retries.")
        continue

    data = response.json()
    df = pd.DataFrame(data["daily"])
    df["city"]      = city
    df["latitude"]  = coords["lat"]
    df["longitude"] = coords["lon"]
    all_data.append(df)
    print(f"  Done. Rows: {len(df)}")

    # Polite delay between each city request
    time.sleep(10)

# Load the existing 3-city file and append
existing = pd.read_csv("raw_data/india_weather_raw.csv")
new_data = pd.concat(all_data, ignore_index=True)
new_data.rename(columns={"time": "date"}, inplace=True)

final_df = pd.concat([existing, new_data], ignore_index=True)
final_df.to_csv("raw_data/india_weather_raw.csv", index=False)

print(f"\nUpdated file saved.")
print(f"Total rows : {len(final_df)}")
print(f"Cities     : {list(final_df['city'].unique())}")
