import pandas as pd
import numpy as np
import os

os.makedirs("cleaned_data", exist_ok=True)

print("=" * 50)
print("PHASE 2 — DATA CLEANING")
print("=" * 50)

# ─────────────────────────────────────────────
# PART A — Clean india_weather_raw.csv
# ─────────────────────────────────────────────
print("\n[1/5] Loading india_weather_raw.csv...")
df = pd.read_csv("raw_data/india_weather_raw.csv")
print(f"      Shape before cleaning : {df.shape}")

# STEP 1 — Fix data types
print("\n[2/5] Fixing data types and dates...")
df["date"] = pd.to_datetime(df["date"])
df["year"]  = df["date"].dt.year
df["month"] = df["date"].dt.month
df["day"]   = df["date"].dt.day
df["season"] = df["month"].map({
    12: "Winter", 1: "Winter",  2: "Winter",
    3:  "Summer", 4: "Summer",  5: "Summer",
    6:  "Monsoon",7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-Monsoon", 11: "Post-Monsoon"
})
print("      date column converted to datetime")
print("      year, month, day, season columns added")

# STEP 2 — Handle missing values (check + fill)
print("\n[3/5] Checking and handling missing values...")
missing_before = df.isnull().sum().sum()
print(f"      Missing values before : {missing_before}")

numeric_cols = [
    "temperature_2m_max", "temperature_2m_min",
    "precipitation_sum",  "windspeed_10m_max",
    "relative_humidity_2m_max", "relative_humidity_2m_min"
]
# Fill any missing numeric values using forward fill within each city
df[numeric_cols] = df.groupby("city")[numeric_cols].transform(
    lambda x: x.ffill().bfill()
)
missing_after = df.isnull().sum().sum()
print(f"      Missing values after  : {missing_after}")

# STEP 3 — Remove outliers using IQR method per city per column
print("\n[4/5] Removing outliers...")
total_outliers = 0
for col in numeric_cols:
    Q1 = df.groupby("city")[col].transform("quantile", 0.01)
    Q3 = df.groupby("city")[col].transform("quantile", 0.99)
    mask = (df[col] < Q1) | (df[col] > Q3)
    count = mask.sum()
    total_outliers += count
    # Cap the values instead of dropping rows (safer for time-series)
    df[col] = np.where(df[col] < Q1, Q1, df[col])
    df[col] = np.where(df[col] > Q3, Q3, df[col])
print(f"      Outlier values capped  : {total_outliers}")

# STEP 4 — Add derived columns
print("\n[5/5] Adding derived columns...")
df["temp_range"] = df["temperature_2m_max"] - df["temperature_2m_min"]
df["humidity_avg"] = (df["relative_humidity_2m_max"] + df["relative_humidity_2m_min"]) / 2
print("      temp_range  = max_temp - min_temp")
print("      humidity_avg = (max_humidity + min_humidity) / 2")

# Round all numeric columns to 2 decimal places
df[numeric_cols + ["temp_range", "humidity_avg"]] = \
    df[numeric_cols + ["temp_range", "humidity_avg"]].round(2)

# Save
output_path = "cleaned_data/cleaned_weather.csv"
df.to_csv(output_path, index=False)
print(f"\n      Saved: {output_path}")
print(f"      Final shape: {df.shape}")
print(f"      Columns: {list(df.columns)}")

# ─────────────────────────────────────────────
# PART B — Clean rainfall_in_india_1901-2015.csv
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("CLEANING RAINFALL 1901-2015 DATA")
print("=" * 50)

rf = pd.read_csv("raw_data/rainfall_in_india_1901-2015.csv")
print(f"\nShape before : {rf.shape}")

# Strip whitespace from column names
rf.columns = rf.columns.str.strip()

# Fix data types
rf["YEAR"] = rf["YEAR"].astype(int)

# Month columns
month_cols = ["JAN","FEB","MAR","APR","MAY","JUN",
              "JUL","AUG","SEP","OCT","NOV","DEC","ANNUAL"]

# Convert to numeric (some may have stray strings)
for col in month_cols:
    rf[col] = pd.to_numeric(rf[col], errors="coerce")

# Fill missing with subdivision mean
missing_rf = rf[month_cols].isnull().sum().sum()
print(f"Missing values before : {missing_rf}")
rf[month_cols] = rf.groupby("SUBDIVISION")[month_cols].transform(
    lambda x: x.fillna(x.mean())
)
missing_rf_after = rf[month_cols].isnull().sum().sum()
print(f"Missing values after  : {missing_rf_after}")

# Add decade column for trend analysis
rf["DECADE"] = (rf["YEAR"] // 10) * 10

# Round
rf[month_cols] = rf[month_cols].round(2)

output_path2 = "cleaned_data/cleaned_rainfall.csv"
rf.to_csv(output_path2, index=False)
print(f"\nSaved: {output_path2}")
print(f"Final shape: {rf.shape}")
print(f"Columns: {list(rf.columns)}")

print("\n" + "=" * 50)
print("PHASE 2 COMPLETE")
print("=" * 50)
