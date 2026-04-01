import sqlite3
import pandas as pd
import os

DB_PATH = "weather_india.db"

print("=" * 50)
print("PHASE 3 — DATABASE CREATION")
print("=" * 50)

# Connect (creates the file if it doesn't exist)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign keys
cursor.execute("PRAGMA foreign_keys = ON")

# ─────────────────────────────────────────────
# TABLE 1 — cities
# ─────────────────────────────────────────────
print("\n[1/6] Creating table: cities...")
cursor.execute("DROP TABLE IF EXISTS daily_weather")
cursor.execute("DROP TABLE IF EXISTS cities")
cursor.execute("""
    CREATE TABLE cities (
        city_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        city_name TEXT    NOT NULL UNIQUE,
        latitude  REAL    NOT NULL,
        longitude REAL    NOT NULL,
        state     TEXT
    )
""")

city_state_map = {
    "Chennai":    "Tamil Nadu",
    "Mumbai":     "Maharashtra",
    "Delhi":      "Delhi",
    "Kolkata":    "West Bengal",
    "Bangalore":  "Karnataka",
    "Hyderabad":  "Telangana",
    "Coimbatore": "Tamil Nadu",
    "Jaipur":     "Rajasthan",
}

df = pd.read_csv("cleaned_data/cleaned_weather.csv")
cities = df[["city", "latitude", "longitude"]].drop_duplicates()

for _, row in cities.iterrows():
    cursor.execute("""
        INSERT INTO cities (city_name, latitude, longitude, state)
        VALUES (?, ?, ?, ?)
    """, (row["city"], row["latitude"], row["longitude"],
          city_state_map.get(row["city"], "Unknown")))

conn.commit()
count = cursor.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
print(f"      Inserted {count} cities")

# ─────────────────────────────────────────────
# TABLE 2 — daily_weather
# ─────────────────────────────────────────────
print("\n[2/6] Creating table: daily_weather...")
cursor.execute("""
    CREATE TABLE daily_weather (
        weather_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        city_id       INTEGER NOT NULL,
        date          TEXT    NOT NULL,
        year          INTEGER,
        month         INTEGER,
        day           INTEGER,
        season        TEXT,
        temp_max      REAL,
        temp_min      REAL,
        temp_range    REAL,
        precipitation REAL,
        windspeed     REAL,
        humidity_max  REAL,
        humidity_min  REAL,
        humidity_avg  REAL,
        FOREIGN KEY (city_id) REFERENCES cities(city_id)
    )
""")

print("\n[3/6] Loading cleaned_weather.csv into daily_weather...")
city_id_map = {
    row[1]: row[0]
    for row in cursor.execute("SELECT city_id, city_name FROM cities")
}

df["city_id"] = df["city"].map(city_id_map)
insert_df = df[[
    "city_id", "date", "year", "month", "day", "season",
    "temperature_2m_max", "temperature_2m_min", "temp_range",
    "precipitation_sum", "windspeed_10m_max",
    "relative_humidity_2m_max", "relative_humidity_2m_min", "humidity_avg"
]].copy()
insert_df.columns = [
    "city_id", "date", "year", "month", "day", "season",
    "temp_max", "temp_min", "temp_range",
    "precipitation", "windspeed",
    "humidity_max", "humidity_min", "humidity_avg"
]

insert_df.to_sql("daily_weather", conn, if_exists="append", index=False)
conn.commit()
count = cursor.execute("SELECT COUNT(*) FROM daily_weather").fetchone()[0]
print(f"      Inserted {count} rows into daily_weather")

# ─────────────────────────────────────────────
# TABLE 3 — rainfall_history
# ─────────────────────────────────────────────
print("\n[4/6] Creating table: rainfall_history...")
cursor.execute("DROP TABLE IF EXISTS rainfall_history")
cursor.execute("""
    CREATE TABLE rainfall_history (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        subdivision TEXT,
        year        INTEGER,
        decade      INTEGER,
        jan REAL, feb REAL, mar REAL, apr REAL,
        may REAL, jun REAL, jul REAL, aug REAL,
        sep REAL, oct REAL, nov REAL, dec REAL,
        annual      REAL,
        jan_feb     REAL,
        mar_may     REAL,
        jun_sep     REAL,
        oct_dec     REAL
    )
""")

print("\n[5/6] Loading cleaned_rainfall.csv into rainfall_history...")
rf = pd.read_csv("cleaned_data/cleaned_rainfall.csv")
rf_insert = rf[[
    "SUBDIVISION","YEAR","DECADE",
    "JAN","FEB","MAR","APR","MAY","JUN",
    "JUL","AUG","SEP","OCT","NOV","DEC",
    "ANNUAL","Jan-Feb","Mar-May","Jun-Sep","Oct-Dec"
]].copy()
rf_insert.columns = [
    "subdivision","year","decade",
    "jan","feb","mar","apr","may","jun",
    "jul","aug","sep","oct","nov","dec",
    "annual","jan_feb","mar_may","jun_sep","oct_dec"
]
rf_insert.to_sql("rainfall_history", conn, if_exists="append", index=False)
conn.commit()
count = cursor.execute("SELECT COUNT(*) FROM rainfall_history").fetchone()[0]
print(f"      Inserted {count} rows into rainfall_history")

# ─────────────────────────────────────────────
# VERIFICATION
# ─────────────────────────────────────────────
print("\n[6/6] Verifying database...")
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()
print(f"\n      Tables created: {[t[0] for t in tables]}")

for table in [t[0] for t in tables]:
    n = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"      {table:<20} → {n} rows")

print("\n      Sample query — avg max temp per city:")
result = cursor.execute("""
    SELECT c.city_name, ROUND(AVG(w.temp_max), 2) as avg_max_temp
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name
    ORDER BY avg_max_temp DESC
""").fetchall()
for row in result:
    print(f"        {row[0]:<15} {row[1]} °C")

conn.close()
print("\n" + "=" * 50)
print(f"DATABASE SAVED: {DB_PATH}")
print("PHASE 3 COMPLETE")
print("=" * 50)
