import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from prophet import Prophet
import os
import warnings
warnings.filterwarnings("ignore")

os.makedirs("plots/forecasts", exist_ok=True)
os.makedirs("reports", exist_ok=True)

conn = sqlite3.connect("weather_india.db")
df = pd.read_sql("""
    SELECT c.city_name, w.date, w.temp_max, w.precipitation
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
""", conn)
conn.close()
df["date"] = pd.to_datetime(df["date"])

cities    = sorted(df["city_name"].unique())
FORECAST_DAYS = 90
all_forecasts = []

print("=" * 55)
print("PHASE 8 — FORECASTING WITH PROPHET")
print("=" * 55)

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor":   "white",
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size":  11,
})

for city in cities:
    city_df = df[df["city_name"] == city].sort_values("date")

    for variable, col, unit, color in [
        ("Temperature", "temp_max",      "°C", "#e76f51"),
        ("Rainfall",    "precipitation", "mm", "#2a9d8f"),
    ]:
        print(f"\n  Forecasting {variable} for {city}...")

        # Prophet requires columns named 'ds' and 'y'
        prophet_df = city_df[["date", col]].rename(
            columns={"date": "ds", col: "y"}
        )

        # For rainfall — floor at 0 (cannot be negative)
        if col == "precipitation":
            prophet_df["y"]     = prophet_df["y"].clip(lower=0)
            prophet_df["floor"] = 0
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
            )
            model.fit(prophet_df)
            future = model.make_future_dataframe(periods=FORECAST_DAYS)
            future["floor"] = 0
        else:
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
            )
            model.fit(prophet_df)
            future = model.make_future_dataframe(periods=FORECAST_DAYS)

        forecast = model.predict(future)

        # Clip rainfall predictions to 0
        if col == "precipitation":
            forecast["yhat"]       = forecast["yhat"].clip(lower=0)
            forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0)

        # Collect forecast rows for CSV
        forecast_only = forecast[forecast["ds"] > prophet_df["ds"].max()].copy()
        forecast_only["city"]     = city
        forecast_only["variable"] = variable
        forecast_only["unit"]     = unit
        all_forecasts.append(
            forecast_only[["city","variable","ds","yhat","yhat_lower","yhat_upper","unit"]]
        )

        # ── Plot ──────────────────────────────────
        fig, ax = plt.subplots(figsize=(13, 4))

        # Historical data
        ax.plot(prophet_df["ds"], prophet_df["y"],
                color="gray", alpha=0.4, linewidth=0.8, label="Historical")

        # Forecast line
        ax.plot(forecast["ds"], forecast["yhat"],
                color=color, linewidth=1.8, label="Forecast")

        # Uncertainty band
        ax.fill_between(
            forecast["ds"],
            forecast["yhat_lower"],
            forecast["yhat_upper"],
            alpha=0.25, color=color, label="Uncertainty band"
        )

        # Vertical line at forecast start
        split_date = prophet_df["ds"].max()
        ax.axvline(x=split_date, color="black",
                   linestyle="--", linewidth=1, alpha=0.6)
        ax.text(split_date, ax.get_ylim()[1] * 0.95,
                " Forecast start", fontsize=9, color="black")

        ax.set_title(
            f"{city} — {variable} forecast (next {FORECAST_DAYS} days)",
            fontsize=12
        )
        ax.set_xlabel("Date")
        ax.set_ylabel(f"{variable} ({unit})")
        ax.legend(fontsize=9)
        plt.tight_layout()

        fname = f"plots/forecasts/{city.lower()}_{col}_forecast.png"
        plt.savefig(fname, dpi=130)
        plt.close()
        print(f"    Saved: {fname}")

# ── Save all forecasts to CSV ─────────────────
final_forecast_df = pd.concat(all_forecasts, ignore_index=True)
final_forecast_df.rename(columns={
    "ds":          "date",
    "yhat":        "predicted",
    "yhat_lower":  "lower_bound",
    "yhat_upper":  "upper_bound",
}, inplace=True)
final_forecast_df["predicted"]    = final_forecast_df["predicted"].round(2)
final_forecast_df["lower_bound"]  = final_forecast_df["lower_bound"].round(2)
final_forecast_df["upper_bound"]  = final_forecast_df["upper_bound"].round(2)

csv_path = "reports/forecast_90days.csv"
final_forecast_df.to_csv(csv_path, index=False)

print("\n" + "=" * 55)
print(f"Forecast CSV saved : {csv_path}")
print(f"Total forecast rows: {len(final_forecast_df)}")
print(f"Charts saved in    : plots/forecasts/")
print(f"Cities forecasted  : {len(cities)}")
print(f"Variables          : Temperature + Rainfall")
print(f"Forecast horizon   : {FORECAST_DAYS} days")
print("=" * 55)
print("PHASE 8 COMPLETE")
print("=" * 55)
