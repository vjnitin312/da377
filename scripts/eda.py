import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

os.makedirs("plots", exist_ok=True)

conn = sqlite3.connect("weather_india.db")

print("=" * 50)
print("PHASE 4 — EXPLORATORY DATA ANALYSIS")
print("=" * 50)

# ── Shared style ──────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "font.size":        11,
})
COLORS = ["#1f77b4","#ff7f0e","#2ca02c","#d62728",
          "#9467bd","#8c564b","#e377c2","#7f7f7f"]

# ─────────────────────────────────────────────
# ANALYSIS 1 — Yearly avg max temperature per city
# ─────────────────────────────────────────────
print("\n[1/6] Temperature trends over years...")
df1 = pd.read_sql("""
    SELECT c.city_name, w.year, ROUND(AVG(w.temp_max),2) AS avg_max
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name, w.year
    ORDER BY w.year
""", conn)

fig, ax = plt.subplots(figsize=(12, 5))
for i, city in enumerate(df1["city_name"].unique()):
    d = df1[df1["city_name"] == city]
    ax.plot(d["year"], d["avg_max"], label=city,
            color=COLORS[i], linewidth=1.8, marker="o", markersize=3)
ax.set_title("Yearly average maximum temperature by city (2010–2023)", fontsize=13)
ax.set_xlabel("Year")
ax.set_ylabel("Avg max temperature (°C)")
ax.legend(loc="upper left", fontsize=9, ncol=2)
ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
plt.tight_layout()
plt.savefig("plots/01_temperature_trends.png", dpi=150)
plt.close()
print("      Saved: plots/01_temperature_trends.png")

# ─────────────────────────────────────────────
# ANALYSIS 2 — Monthly avg rainfall (monsoon pattern)
# ─────────────────────────────────────────────
print("\n[2/6] Monsoon rainfall pattern...")
df2 = pd.read_sql("""
    SELECT c.city_name, w.month,
           ROUND(AVG(w.precipitation), 2) AS avg_rain
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name, w.month
    ORDER BY w.month
""", conn)

month_names = ["Jan","Feb","Mar","Apr","May","Jun",
               "Jul","Aug","Sep","Oct","Nov","Dec"]

fig, ax = plt.subplots(figsize=(12, 5))
for i, city in enumerate(df2["city_name"].unique()):
    d = df2[df2["city_name"] == city]
    ax.plot(d["month"], d["avg_rain"], label=city,
            color=COLORS[i], linewidth=2, marker="s", markersize=4)
ax.set_title("Average daily precipitation by month — monsoon pattern (2010–2023)", fontsize=13)
ax.set_xlabel("Month")
ax.set_ylabel("Avg daily precipitation (mm)")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(month_names)
ax.legend(loc="upper left", fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig("plots/02_monsoon_pattern.png", dpi=150)
plt.close()
print("      Saved: plots/02_monsoon_pattern.png")

# ─────────────────────────────────────────────
# ANALYSIS 3 — City-wise comparison (bar chart)
# ─────────────────────────────────────────────
print("\n[3/6] City-wise comparison...")
df3 = pd.read_sql("""
    SELECT c.city_name,
           ROUND(AVG(w.temp_max), 2)      AS avg_max_temp,
           ROUND(AVG(w.temp_min), 2)      AS avg_min_temp,
           ROUND(AVG(w.precipitation), 2) AS avg_rain,
           ROUND(AVG(w.humidity_avg), 2)  AS avg_humidity
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name
    ORDER BY avg_max_temp DESC
""", conn)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
bars1 = axes[0].bar(df3["city_name"], df3["avg_max_temp"],
                    color=COLORS[:len(df3)], edgecolor="white")
axes[0].set_title("Average maximum temperature by city", fontsize=12)
axes[0].set_ylabel("Temperature (°C)")
axes[0].set_xticklabels(df3["city_name"], rotation=30, ha="right")
for bar, val in zip(bars1, df3["avg_max_temp"]):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f"{val}", ha="center", va="bottom", fontsize=9)

bars2 = axes[1].bar(df3["city_name"], df3["avg_humidity"],
                    color=COLORS[:len(df3)], edgecolor="white")
axes[1].set_title("Average humidity by city", fontsize=12)
axes[1].set_ylabel("Humidity (%)")
axes[1].set_xticklabels(df3["city_name"], rotation=30, ha="right")
for bar, val in zip(bars2, df3["avg_humidity"]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                 f"{val}", ha="center", va="bottom", fontsize=9)

plt.suptitle("City-wise climate comparison (2010–2023)", fontsize=13, y=1.01)
plt.tight_layout()
plt.savefig("plots/03_city_comparison.png", dpi=150, bbox_inches="tight")
plt.close()
print("      Saved: plots/03_city_comparison.png")

# ─────────────────────────────────────────────
# ANALYSIS 4 — Seasonal breakdown per city
# ─────────────────────────────────────────────
print("\n[4/6] Seasonal breakdown...")
df4 = pd.read_sql("""
    SELECT c.city_name, w.season,
           ROUND(AVG(w.temp_max), 2)      AS avg_max,
           ROUND(AVG(w.precipitation), 2) AS avg_rain
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name, w.season
""", conn)

seasons      = ["Winter","Summer","Monsoon","Post-Monsoon"]
season_color = ["#4e9af1","#f4a261","#2a9d8f","#e9c46a"]
cities_list  = df4["city_name"].unique()
x = range(len(cities_list))
width = 0.2

fig, ax = plt.subplots(figsize=(14, 5))
for i, season in enumerate(seasons):
    vals = []
    for city in cities_list:
        row = df4[(df4["city_name"]==city) & (df4["season"]==season)]
        vals.append(row["avg_max"].values[0] if len(row) > 0 else 0)
    offset = (i - 1.5) * width
    ax.bar([xi + offset for xi in x], vals, width,
           label=season, color=season_color[i], edgecolor="white")

ax.set_title("Average max temperature by season and city (2010–2023)", fontsize=13)
ax.set_ylabel("Avg max temperature (°C)")
ax.set_xticks(list(x))
ax.set_xticklabels(cities_list, rotation=30, ha="right")
ax.legend(title="Season", fontsize=9)
plt.tight_layout()
plt.savefig("plots/04_seasonal_breakdown.png", dpi=150)
plt.close()
print("      Saved: plots/04_seasonal_breakdown.png")

# ─────────────────────────────────────────────
# ANALYSIS 5 — Humidity vs Rainfall scatter
# ─────────────────────────────────────────────
print("\n[5/6] Humidity vs rainfall correlation...")
df5 = pd.read_sql("""
    SELECT c.city_name, w.humidity_avg, w.precipitation
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    WHERE w.precipitation > 0
""", conn)

fig, ax = plt.subplots(figsize=(10, 5))
for i, city in enumerate(df5["city_name"].unique()):
    d = df5[df5["city_name"] == city].sample(min(500, len(df5)))
    ax.scatter(d["humidity_avg"], d["precipitation"],
               label=city, alpha=0.4, s=10, color=COLORS[i])
ax.set_title("Humidity vs precipitation (rainy days only, 2010–2023)", fontsize=13)
ax.set_xlabel("Average humidity (%)")
ax.set_ylabel("Precipitation (mm)")
ax.legend(fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig("plots/05_humidity_vs_rainfall.png", dpi=150)
plt.close()
print("      Saved: plots/05_humidity_vs_rainfall.png")

# ─────────────────────────────────────────────
# ANALYSIS 6 — 115-year annual rainfall trend
# ─────────────────────────────────────────────
print("\n[6/6] 115-year rainfall trend...")
df6 = pd.read_sql("""
    SELECT year, ROUND(AVG(annual), 2) AS avg_annual
    FROM rainfall_history
    GROUP BY year
    ORDER BY year
""", conn)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(df6["year"], df6["avg_annual"],
        color="#2a9d8f", linewidth=1.2, alpha=0.6, label="Annual rainfall")

# 10-year rolling average
df6["rolling"] = df6["avg_annual"].rolling(10, center=True).mean()
ax.plot(df6["year"], df6["rolling"],
        color="#e76f51", linewidth=2.5, label="10-year rolling average")

ax.set_title("All-India average annual rainfall — 115-year trend (1901–2015)", fontsize=13)
ax.set_xlabel("Year")
ax.set_ylabel("Average annual rainfall (mm)")
ax.legend(fontsize=10)
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
plt.tight_layout()
plt.savefig("plots/06_115year_rainfall_trend.png", dpi=150)
plt.close()
print("      Saved: plots/06_115year_rainfall_trend.png")

conn.close()
print("\n" + "=" * 50)
print("ALL 6 PLOTS SAVED IN: plots/")
print("PHASE 4 COMPLETE")
print("=" * 50)
