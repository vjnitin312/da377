import sqlite3
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import os

os.makedirs("maps", exist_ok=True)

conn = sqlite3.connect("weather_india.db")

# Load city summary statistics
city_stats = pd.read_sql("""
    SELECT
        c.city_name, c.state, c.latitude, c.longitude,
        ROUND(AVG(w.temp_max), 2)      AS avg_temp_max,
        ROUND(AVG(w.temp_min), 2)      AS avg_temp_min,
        ROUND(AVG(w.precipitation), 2) AS avg_precip,
        ROUND(AVG(w.humidity_avg), 2)  AS avg_humidity,
        ROUND(AVG(w.windspeed), 2)     AS avg_windspeed,
        SUM(CASE WHEN w.precipitation > 50 THEN 1 ELSE 0 END) AS extreme_rain_days
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
    GROUP BY c.city_name
""", conn)

# Load daily weather for heatmap layer
daily = pd.read_sql("""
    SELECT c.latitude, c.longitude, w.temp_max, w.precipitation
    FROM daily_weather w
    JOIN cities c ON w.city_id = c.city_id
""", conn)

conn.close()

print("=" * 50)
print("PHASE 7 — INTERACTIVE MAP CREATION")
print("=" * 50)

# ─────────────────────────────────────────────
# Colour helper based on temperature
# ─────────────────────────────────────────────
def temp_color(temp):
    if temp >= 32:   return "red"
    elif temp >= 30: return "orange"
    elif temp >= 28: return "lightred"
    else:            return "green"

def rain_color(rain):
    if rain >= 4:    return "blue"
    elif rain >= 2:  return "lightblue"
    else:            return "beige"

# ─────────────────────────────────────────────
# MAP 1 — City climate markers
# ─────────────────────────────────────────────
print("\n[1/5] Creating city climate marker map...")

m1 = folium.Map(
    location=[20.5, 78.9],
    zoom_start=5,
    tiles="CartoDB positron"
)

for _, row in city_stats.iterrows():
    popup_html = f"""
    <div style='font-family:Arial; min-width:200px'>
      <h4 style='margin:0;color:#333'>{row['city_name']}</h4>
      <p style='margin:2px 0;color:#666'>{row['state']}</p>
      <hr style='margin:4px 0'>
      <table style='width:100%;font-size:13px'>
        <tr><td>Avg max temp</td><td><b>{row['avg_temp_max']} °C</b></td></tr>
        <tr><td>Avg min temp</td><td><b>{row['avg_temp_min']} °C</b></td></tr>
        <tr><td>Avg rainfall</td><td><b>{row['avg_precip']} mm/day</b></td></tr>
        <tr><td>Avg humidity</td><td><b>{row['avg_humidity']} %</b></td></tr>
        <tr><td>Avg windspeed</td><td><b>{row['avg_windspeed']} km/h</b></td></tr>
        <tr><td>Extreme rain days</td><td><b>{int(row['extreme_rain_days'])}</b></td></tr>
      </table>
      <p style='font-size:11px;color:#999;margin:4px 0'>Data: 2010–2023 · Open-Meteo API</p>
    </div>
    """
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=18,
        color=temp_color(row["avg_temp_max"]),
        fill=True,
        fill_color=temp_color(row["avg_temp_max"]),
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{row['city_name']} — {row['avg_temp_max']}°C avg max"
    ).add_to(m1)

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=folium.DivIcon(
            html=f'<div style="font-size:10px;font-weight:bold;color:#333;'
                 f'text-shadow:1px 1px 2px white;margin-top:-8px">'
                 f'{row["city_name"]}</div>',
            icon_size=(80, 20),
            icon_anchor=(40, 0)
        )
    ).add_to(m1)

# Legend
legend_html = """
<div style='position:fixed;bottom:30px;left:30px;z-index:1000;
     background:white;padding:12px;border-radius:8px;
     border:1px solid #ccc;font-size:12px;font-family:Arial'>
  <b>Avg max temperature</b><br>
  <span style='color:red'>●</span> ≥ 32°C (Hot)<br>
  <span style='color:orange'>●</span> 30–32°C (Warm)<br>
  <span style='color:#ff9999'>●</span> 28–30°C (Moderate)<br>
  <span style='color:green'>●</span> &lt; 28°C (Cool)
</div>
"""
m1.get_root().html.add_child(folium.Element(legend_html))
m1.save("maps/01_city_climate_markers.html")
print("      Saved: maps/01_city_climate_markers.html")

# ─────────────────────────────────────────────
# MAP 2 — Temperature bubble map
# ─────────────────────────────────────────────
print("\n[2/5] Creating temperature bubble map...")

m2 = folium.Map(
    location=[20.5, 78.9],
    zoom_start=5,
    tiles="CartoDB dark_matter"
)

temp_min_val = city_stats["avg_temp_max"].min()
temp_max_val = city_stats["avg_temp_max"].max()

for _, row in city_stats.iterrows():
    norm = (row["avg_temp_max"] - temp_min_val) / (temp_max_val - temp_min_val)
    radius = 20 + norm * 25

    r = int(255 * norm)
    g = int(100 * (1 - norm))
    b = 50
    color = f"#{r:02x}{g:02x}{b:02x}"

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.75,
        tooltip=f"{row['city_name']}: {row['avg_temp_max']}°C",
        popup=folium.Popup(
            f"<b>{row['city_name']}</b><br>"
            f"Avg max: {row['avg_temp_max']}°C<br>"
            f"Avg min: {row['avg_temp_min']}°C",
            max_width=180
        )
    ).add_to(m2)

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=folium.DivIcon(
            html=f'<div style="font-size:11px;font-weight:bold;'
                 f'color:white;text-align:center;margin-top:-6px">'
                 f'{row["avg_temp_max"]}°C</div>',
            icon_size=(60, 20),
            icon_anchor=(30, 0)
        )
    ).add_to(m2)

m2.save("maps/02_temperature_bubble_map.html")
print("      Saved: maps/02_temperature_bubble_map.html")

# ─────────────────────────────────────────────
# MAP 3 — Rainfall bubble map
# ─────────────────────────────────────────────
print("\n[3/5] Creating rainfall bubble map...")

m3 = folium.Map(
    location=[20.5, 78.9],
    zoom_start=5,
    tiles="CartoDB positron"
)

for _, row in city_stats.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=10 + row["avg_precip"] * 8,
        color=rain_color(row["avg_precip"]),
        fill=True,
        fill_color=rain_color(row["avg_precip"]),
        fill_opacity=0.7,
        tooltip=f"{row['city_name']}: {row['avg_precip']} mm/day",
        popup=folium.Popup(
            f"<b>{row['city_name']}</b><br>"
            f"Avg rainfall: {row['avg_precip']} mm/day<br>"
            f"Extreme rain days: {int(row['extreme_rain_days'])}",
            max_width=200
        )
    ).add_to(m3)

    folium.Marker(
        location=[row["latitude"], row["longitude"]],
        icon=folium.DivIcon(
            html=f'<div style="font-size:10px;font-weight:bold;'
                 f'color:#333;margin-top:-6px">'
                 f'{row["city_name"]}<br>{row["avg_precip"]}mm</div>',
            icon_size=(90, 30),
            icon_anchor=(45, 0)
        )
    ).add_to(m3)

rain_legend = """
<div style='position:fixed;bottom:30px;left:30px;z-index:1000;
     background:white;padding:12px;border-radius:8px;
     border:1px solid #ccc;font-size:12px;font-family:Arial'>
  <b>Avg daily rainfall</b><br>
  <span style='color:blue'>●</span> ≥ 4 mm (Heavy)<br>
  <span style='color:lightblue'>●</span> 2–4 mm (Moderate)<br>
  <span style='color:#f5deb3'>●</span> &lt; 2 mm (Light)
  <br><i style='font-size:11px'>Bubble size = rainfall amount</i>
</div>
"""
m3.get_root().html.add_child(folium.Element(rain_legend))
m3.save("maps/03_rainfall_bubble_map.html")
print("      Saved: maps/03_rainfall_bubble_map.html")

# ─────────────────────────────────────────────
# MAP 4 — Heatwave risk map
# ─────────────────────────────────────────────
print("\n[4/5] Creating heatwave risk map...")

m4 = folium.Map(
    location=[20.5, 78.9],
    zoom_start=5,
    tiles="CartoDB positron"
)

# HeatMap layer using daily max temperature data
heat_data = daily[["latitude", "longitude", "temp_max"]].values.tolist()
HeatMap(
    heat_data,
    min_opacity=0.3,
    max_zoom=10,
    radius=40,
    blur=25,
    gradient={0.2: "blue", 0.5: "yellow", 0.8: "orange", 1.0: "red"}
).add_to(m4)

# Add city markers on top
for _, row in city_stats.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=8,
        color="black",
        fill=True,
        fill_color="white",
        fill_opacity=0.9,
        tooltip=f"{row['city_name']} — {row['avg_temp_max']}°C avg max",
        popup=folium.Popup(
            f"<b>{row['city_name']}</b><br>"
            f"Avg max temp: {row['avg_temp_max']}°C<br>"
            f"95th pct threshold: hot days",
            max_width=180
        )
    ).add_to(m4)

m4.save("maps/04_heatwave_risk_map.html")
print("      Saved: maps/04_heatwave_risk_map.html")

# ─────────────────────────────────────────────
# MAP 5 — Combined layered map
# ─────────────────────────────────────────────
print("\n[5/5] Creating combined layer map...")

m5 = folium.Map(
    location=[20.5, 78.9],
    zoom_start=5,
    tiles="CartoDB positron"
)

# Layer 1 — Temperature markers
temp_layer = folium.FeatureGroup(name="Temperature markers")
for _, row in city_stats.iterrows():
    popup_html = f"""
    <div style='font-family:Arial;min-width:220px'>
      <h4 style='margin:0'>{row['city_name']}, {row['state']}</h4>
      <hr style='margin:4px 0'>
      <table style='width:100%;font-size:13px'>
        <tr><td>Avg max temp</td><td><b>{row['avg_temp_max']} °C</b></td></tr>
        <tr><td>Avg rainfall</td><td><b>{row['avg_precip']} mm/day</b></td></tr>
        <tr><td>Avg humidity</td><td><b>{row['avg_humidity']} %</b></td></tr>
        <tr><td>Avg windspeed</td><td><b>{row['avg_windspeed']} km/h</b></td></tr>
        <tr><td>Extreme rain days</td><td><b>{int(row['extreme_rain_days'])}</b></td></tr>
      </table>
    </div>
    """
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=20,
        color=temp_color(row["avg_temp_max"]),
        fill=True,
        fill_color=temp_color(row["avg_temp_max"]),
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=260),
        tooltip=f"{row['city_name']} — {row['avg_temp_max']}°C"
    ).add_to(temp_layer)
temp_layer.add_to(m5)

# Layer 2 — Rainfall bubbles
rain_layer = folium.FeatureGroup(name="Rainfall bubbles")
for _, row in city_stats.iterrows():
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=10 + row["avg_precip"] * 6,
        color="blue",
        fill=True,
        fill_color="blue",
        fill_opacity=0.4,
        tooltip=f"{row['city_name']} — {row['avg_precip']} mm/day",
    ).add_to(rain_layer)
rain_layer.add_to(m5)

# Layer 3 — Heatwave heat layer
heat_layer = folium.FeatureGroup(name="Temperature heatmap")
HeatMap(
    heat_data,
    min_opacity=0.2,
    radius=40,
    blur=25,
    gradient={0.2: "blue", 0.5: "yellow", 0.8: "orange", 1.0: "red"}
).add_to(heat_layer)
heat_layer.add_to(m5)

folium.LayerControl(collapsed=False).add_to(m5)

m5.save("maps/05_combined_layer_map.html")
print("      Saved: maps/05_combined_layer_map.html")

print("\n" + "=" * 50)
print("ALL 5 MAPS SAVED IN: maps/")
print("PHASE 7 COMPLETE")
print("=" * 50)
