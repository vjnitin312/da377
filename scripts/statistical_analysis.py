import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

os.makedirs("plots", exist_ok=True)
os.makedirs("reports", exist_ok=True)

conn   = sqlite3.connect("weather_india.db")
report = []  # lines collected for the text report

def section(title):
    line = f"\n{'='*55}\n{title}\n{'='*55}"
    print(line)
    report.append(line)

def log(text):
    print(text)
    report.append(text)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size":  11,
})

df = pd.read_sql("""
    SELECT c.city_name, w.*
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
""", conn)
df["date"] = pd.to_datetime(df["date"])

rf = pd.read_sql("SELECT * FROM rainfall_history", conn)

# ─────────────────────────────────────────────
# ANALYSIS 1 — Correlation matrix
# ─────────────────────────────────────────────
section("ANALYSIS 1 — CORRELATION MATRIX")

num_cols = ["temp_max","temp_min","temp_range",
            "precipitation","windspeed","humidity_avg"]
corr = df[num_cols].corr().round(3)
log("\n" + corr.to_string())

fig, ax = plt.subplots(figsize=(8, 6))
mask = np.zeros_like(corr, dtype=bool)
mask[np.triu_indices_from(mask)] = True
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
            center=0, ax=ax, linewidths=0.5,
            cbar_kws={"shrink": 0.8})
ax.set_title("Correlation matrix — weather variables (2010–2023)", fontsize=12)
plt.tight_layout()
plt.savefig("plots/07_correlation_matrix.png", dpi=150)
plt.close()
log("Saved: plots/07_correlation_matrix.png")

# ─────────────────────────────────────────────
# ANALYSIS 2 — Heatwave detection
# A heatwave day = temp_max > city's 95th percentile
# ─────────────────────────────────────────────
section("ANALYSIS 2 — HEATWAVE DETECTION")

p95 = df.groupby("city_name")["temp_max"].quantile(0.95).reset_index()
p95.columns = ["city_name", "threshold_95p"]
df2 = df.merge(p95, on="city_name")
df2["is_heatwave"] = df2["temp_max"] >= df2["threshold_95p"]

hw_yearly = df2.groupby(["city_name","year"])["is_heatwave"].sum().reset_index()
hw_yearly.columns = ["city_name","year","heatwave_days"]

log("\nHeatwave days per city (total 2010–2023):")
total_hw = hw_yearly.groupby("city_name")["heatwave_days"].sum().sort_values(ascending=False)
log(total_hw.to_string())

log("\n95th percentile temperature thresholds per city:")
log(p95.to_string(index=False))

fig, ax = plt.subplots(figsize=(12, 5))
COLORS = ["#1f77b4","#ff7f0e","#2ca02c","#d62728",
          "#9467bd","#8c564b","#e377c2","#7f7f7f"]
for i, city in enumerate(hw_yearly["city_name"].unique()):
    d = hw_yearly[hw_yearly["city_name"] == city]
    ax.plot(d["year"], d["heatwave_days"], label=city,
            color=COLORS[i], linewidth=2, marker="o", markersize=4)
ax.set_title("Heatwave days per year by city (temp ≥ city 95th percentile)", fontsize=12)
ax.set_xlabel("Year")
ax.set_ylabel("Number of heatwave days")
ax.legend(fontsize=9, ncol=2)
plt.tight_layout()
plt.savefig("plots/08_heatwave_days.png", dpi=150)
plt.close()
log("Saved: plots/08_heatwave_days.png")

# ─────────────────────────────────────────────
# ANALYSIS 3 — Decade-wise rainfall trend
# ─────────────────────────────────────────────
section("ANALYSIS 3 — DECADE-WISE RAINFALL TREND")

decade_rf = rf.groupby("decade")["annual"].agg(["mean","std","min","max"]).round(2)
decade_rf.columns = ["avg_mm","std_mm","min_mm","max_mm"]
log("\nDecade-wise all-India average annual rainfall:")
log(decade_rf.to_string())

# Linear regression on annual trend
slope, intercept, r, p, se = stats.linregress(rf["year"], rf["annual"])
log(f"\nLinear trend (1901–2015):")
log(f"  Slope     : {slope:.4f} mm/year")
log(f"  R²        : {r**2:.4f}")
log(f"  p-value   : {p:.4f}  ({'significant' if p < 0.05 else 'not significant'})")

fig, ax = plt.subplots(figsize=(12, 5))
decade_avg = decade_rf["avg_mm"]
bars = ax.bar(decade_avg.index, decade_avg.values, width=7,
              color=plt.cm.RdYlGn(
                  np.linspace(0.2, 0.8, len(decade_avg))),
              edgecolor="white")
for bar, val in zip(bars, decade_avg.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f"{val:.0f}", ha="center", va="bottom", fontsize=9)
ax.set_title("Decade-wise average annual rainfall — all India (1901–2015)", fontsize=12)
ax.set_xlabel("Decade")
ax.set_ylabel("Average annual rainfall (mm)")
ax.xaxis.set_major_locator(plt.MultipleLocator(10))
plt.tight_layout()
plt.savefig("plots/09_decade_rainfall.png", dpi=150)
plt.close()
log("Saved: plots/09_decade_rainfall.png")

# ─────────────────────────────────────────────
# ANALYSIS 4 — Monsoon onset index per city
# Onset = first month where precipitation crosses
# 150% of the city's annual daily average
# ─────────────────────────────────────────────
section("ANALYSIS 4 — MONSOON ONSET INDEX")

monthly = df.groupby(["city_name","month"])["precipitation"].mean().reset_index()
annual_avg = df.groupby("city_name")["precipitation"].mean().reset_index()
annual_avg.columns = ["city_name","annual_daily_avg"]
monthly = monthly.merge(annual_avg, on="city_name")
monthly["ratio"] = monthly["precipitation"] / monthly["annual_daily_avg"]

month_names = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
               7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}

log("\nMonsoon intensity ratio (monthly avg / annual daily avg):")
log("Ratio > 1.5 = monsoon-active month\n")
for city in monthly["city_name"].unique():
    d = monthly[monthly["city_name"]==city].sort_values("month")
    onset = d[d["ratio"] >= 1.5]["month"].min()
    onset_name = month_names.get(onset, "None")
    peak  = d.loc[d["precipitation"].idxmax(), "month"]
    log(f"  {city:<14} onset: {onset_name:<5}  peak: {month_names[peak]}")

fig, ax = plt.subplots(figsize=(12, 5))
for i, city in enumerate(monthly["city_name"].unique()):
    d = monthly[monthly["city_name"]==city].sort_values("month")
    ax.plot(d["month"], d["ratio"], label=city,
            color=COLORS[i], linewidth=2, marker="o", markersize=4)
ax.axhline(y=1.5, color="red", linestyle="--", linewidth=1.2, label="Onset threshold (1.5×)")
ax.set_title("Monsoon onset index — monthly precipitation ratio per city", fontsize=12)
ax.set_xlabel("Month")
ax.set_ylabel("Precipitation ratio (monthly / annual avg)")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(list(month_names.values()))
ax.legend(fontsize=9, ncol=3)
plt.tight_layout()
plt.savefig("plots/10_monsoon_onset_index.png", dpi=150)
plt.close()
log("Saved: plots/10_monsoon_onset_index.png")

# ─────────────────────────────────────────────
# ANALYSIS 5 — Monthly descriptive statistics
# ─────────────────────────────────────────────
section("ANALYSIS 5 — MONTHLY STATISTICS (ALL CITIES COMBINED)")

monthly_stats = df.groupby("month").agg(
    avg_temp_max   =("temp_max",      "mean"),
    avg_temp_min   =("temp_min",      "mean"),
    avg_precip     =("precipitation", "mean"),
    avg_humidity   =("humidity_avg",  "mean"),
    avg_windspeed  =("windspeed",     "mean"),
).round(2)
monthly_stats.index = list(month_names.values())
log("\n" + monthly_stats.to_string())

fig, axes = plt.subplots(2, 1, figsize=(12, 8))
axes[0].bar(monthly_stats.index, monthly_stats["avg_temp_max"],
            color="#e76f51", label="Avg max temp")
axes[0].bar(monthly_stats.index, monthly_stats["avg_temp_min"],
            color="#457b9d", label="Avg min temp", alpha=0.7)
axes[0].set_title("Monthly average temperature range — all cities combined", fontsize=12)
axes[0].set_ylabel("Temperature (°C)")
axes[0].legend()

axes[1].bar(monthly_stats.index, monthly_stats["avg_precip"],
            color="#2a9d8f")
axes[1].set_title("Monthly average daily precipitation — all cities combined", fontsize=12)
axes[1].set_ylabel("Precipitation (mm)")
plt.tight_layout()
plt.savefig("plots/11_monthly_statistics.png", dpi=150)
plt.close()
log("Saved: plots/11_monthly_statistics.png")

# ─────────────────────────────────────────────
# ANALYSIS 6 — Extreme rain days per city per year
# Extreme = precipitation > 50mm in a day
# ─────────────────────────────────────────────
section("ANALYSIS 6 — EXTREME RAINFALL DAYS (>50mm)")

df["extreme_rain"] = df["precipitation"] > 50
extreme = df.groupby(["city_name","year"])["extreme_rain"].sum().reset_index()
extreme.columns = ["city_name","year","extreme_days"]

log("\nTotal extreme rain days (>50mm) per city (2010–2023):")
total_ext = extreme.groupby("city_name")["extreme_days"].sum().sort_values(ascending=False)
log(total_ext.to_string())

fig, ax = plt.subplots(figsize=(12, 5))
for i, city in enumerate(extreme["city_name"].unique()):
    d = extreme[extreme["city_name"]==city]
    ax.bar(d["year"] + i*0.09 - 0.32, d["extreme_days"],
           width=0.09, label=city, color=COLORS[i])
ax.set_title("Extreme rainfall days per year by city (daily precipitation > 50mm)", fontsize=12)
ax.set_xlabel("Year")
ax.set_ylabel("Number of extreme rain days")
ax.legend(fontsize=9, ncol=2)
ax.xaxis.set_major_locator(plt.MultipleLocator(1))
plt.tight_layout()
plt.savefig("plots/12_extreme_rain_days.png", dpi=150)
plt.close()
log("Saved: plots/12_extreme_rain_days.png")

# ─────────────────────────────────────────────
# SAVE TEXT REPORT
# ─────────────────────────────────────────────
report_path = "reports/stats_summary.txt"
with open(report_path, "w") as f:
    f.write("\n".join(report))

conn.close()
print(f"\nReport saved: {report_path}")
print("=" * 55)
print("PHASE 5 COMPLETE — 6 plots + 1 report saved")
print("=" * 55)
