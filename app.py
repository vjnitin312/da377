import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="India Weather Analytics",
    page_icon="🌦",
    layout="wide",
)

# ─────────────────────────────────────────────
# DATA LOADING (cached for speed)
# ─────────────────────────────────────────────
@st.cache_data
def load_weather():
    conn = sqlite3.connect("weather_india.db")
    df = pd.read_sql("""
        SELECT c.city_name, c.state, c.latitude, c.longitude, w.*
        FROM daily_weather w
        JOIN cities c ON w.city_id = c.city_id
    """, conn)
    conn.close()
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data
def load_rainfall():
    conn = sqlite3.connect("weather_india.db")
    rf = pd.read_sql("SELECT * FROM rainfall_history", conn)
    conn.close()
    return rf

df  = load_weather()
rf  = load_rainfall()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
st.sidebar.title("Filters")
st.sidebar.markdown("---")

all_cities = sorted(df["city_name"].unique().tolist())
selected_cities = st.sidebar.multiselect(
    "Select cities", all_cities, default=all_cities
)

year_min, year_max = int(df["year"].min()), int(df["year"].max())
selected_years = st.sidebar.slider(
    "Year range", year_min, year_max, (year_min, year_max)
)

all_seasons = ["Winter", "Summer", "Monsoon", "Post-Monsoon"]
selected_seasons = st.sidebar.multiselect(
    "Seasons", all_seasons, default=all_seasons
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Data sources**")
st.sidebar.markdown("- Open-Meteo API (2010–2023)")
st.sidebar.markdown("- IMD rainfall data (1901–2015)")
st.sidebar.markdown("- 8 cities · 40,904 daily records")

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
filtered = df[
    (df["city_name"].isin(selected_cities)) &
    (df["year"].between(*selected_years)) &
    (df["season"].isin(selected_seasons))
].copy()

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("🌦 Historical Weather Data Platform — India")
st.markdown("Interactive analysis of temperature, rainfall, humidity and climate trends across major Indian cities.")
st.markdown("---")

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg max temp",    f"{filtered['temp_max'].mean():.1f} °C")
k2.metric("Avg min temp",    f"{filtered['temp_min'].mean():.1f} °C")
k3.metric("Avg rainfall",    f"{filtered['precipitation'].mean():.2f} mm/day")
k4.metric("Avg humidity",    f"{filtered['humidity_avg'].mean():.1f} %")
k5.metric("Total records",   f"{len(filtered):,}")

st.markdown("---")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🌡 Temperature", "🌧 Rainfall", "📊 Climate statistics", "📋 Raw data"
])

# ══════════════════════════════════════════════
# TAB 1 — TEMPERATURE
# ══════════════════════════════════════════════
with tab1:
    st.subheader("Temperature trends")

    # Yearly avg max temp line chart
    yearly = filtered.groupby(["city_name","year"]).agg(
        avg_max=("temp_max","mean"),
        avg_min=("temp_min","mean"),
    ).reset_index()

    fig1 = px.line(
        yearly, x="year", y="avg_max", color="city_name",
        markers=True,
        title="Yearly average maximum temperature by city",
        labels={"avg_max":"Avg max temp (°C)","year":"Year","city_name":"City"},
    )
    fig1.update_layout(hovermode="x unified", height=400)
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Seasonal avg temp bar
        seasonal = filtered.groupby(["city_name","season"])["temp_max"].mean().reset_index()
        fig2 = px.bar(
            seasonal, x="city_name", y="temp_max", color="season",
            barmode="group",
            title="Average max temperature by season",
            labels={"temp_max":"Avg max temp (°C)","city_name":"City"},
            category_orders={"season":["Winter","Summer","Monsoon","Post-Monsoon"]}
        )
        fig2.update_layout(height=380)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        # Monthly temperature range
        monthly_temp = filtered.groupby("month").agg(
            avg_max=("temp_max","mean"),
            avg_min=("temp_min","mean"),
        ).reset_index()
        months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly_temp["month_name"] = monthly_temp["month"].apply(lambda x: months[x-1])

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=monthly_temp["month_name"], y=monthly_temp["avg_max"],
            name="Avg max", marker_color="#e76f51"
        ))
        fig3.add_trace(go.Bar(
            x=monthly_temp["month_name"], y=monthly_temp["avg_min"],
            name="Avg min", marker_color="#457b9d"
        ))
        fig3.update_layout(
            title="Monthly temperature range (all selected cities)",
            barmode="group", height=380,
            yaxis_title="Temperature (°C)"
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Heatwave detection
    st.subheader("Heatwave analysis")
    p95 = df.groupby("city_name")["temp_max"].quantile(0.95).reset_index()
    p95.columns = ["city_name","threshold"]
    merged = filtered.merge(p95, on="city_name")
    merged["is_heatwave"] = merged["temp_max"] >= merged["threshold"]
    hw = merged.groupby(["city_name","year"])["is_heatwave"].sum().reset_index()
    hw.columns = ["city_name","year","heatwave_days"]

    fig4 = px.line(
        hw, x="year", y="heatwave_days", color="city_name",
        markers=True,
        title="Heatwave days per year (days ≥ city 95th percentile temperature)",
        labels={"heatwave_days":"Heatwave days","year":"Year","city_name":"City"},
    )
    fig4.update_layout(height=380)
    st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 2 — RAINFALL
# ══════════════════════════════════════════════
with tab2:
    st.subheader("Rainfall analysis")

    col1, col2 = st.columns(2)

    with col1:
        # Monthly rainfall pattern
        monthly_rain = filtered.groupby(["city_name","month"])["precipitation"].mean().reset_index()
        months = ["Jan","Feb","Mar","Apr","May","Jun",
                  "Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly_rain["month_name"] = monthly_rain["month"].apply(lambda x: months[x-1])

        fig5 = px.line(
            monthly_rain, x="month_name", y="precipitation",
            color="city_name", markers=True,
            title="Monthly average rainfall — monsoon pattern",
            labels={"precipitation":"Avg daily rainfall (mm)","month_name":"Month","city_name":"City"},
            category_orders={"month_name": months}
        )
        fig5.update_layout(height=380)
        st.plotly_chart(fig5, use_container_width=True)

    with col2:
        # Rainfall by season
        rain_season = filtered.groupby(["city_name","season"])["precipitation"].mean().reset_index()
        fig6 = px.bar(
            rain_season, x="city_name", y="precipitation", color="season",
            barmode="group",
            title="Average daily rainfall by season and city",
            labels={"precipitation":"Avg rainfall (mm)","city_name":"City"},
            category_orders={"season":["Winter","Summer","Monsoon","Post-Monsoon"]}
        )
        fig6.update_layout(height=380)
        st.plotly_chart(fig6, use_container_width=True)

    # 115-year rainfall trend
    st.subheader("115-year all-India rainfall trend (1901–2015)")

    rf_sub = st.selectbox(
        "Select subdivision",
        sorted(rf["subdivision"].unique()),
        index=0
    )
    rf_filtered = rf[rf["subdivision"] == rf_sub].sort_values("year")
    rf_filtered["rolling_10"] = rf_filtered["annual"].rolling(10, center=True).mean()

    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(
        x=rf_filtered["year"], y=rf_filtered["annual"],
        mode="lines", name="Annual rainfall",
        line=dict(color="#2a9d8f", width=1), opacity=0.6
    ))
    fig7.add_trace(go.Scatter(
        x=rf_filtered["year"], y=rf_filtered["rolling_10"],
        mode="lines", name="10-year rolling avg",
        line=dict(color="#e76f51", width=2.5)
    ))
    fig7.update_layout(
        title=f"Annual rainfall trend — {rf_sub}",
        xaxis_title="Year", yaxis_title="Annual rainfall (mm)",
        height=400, hovermode="x unified"
    )
    st.plotly_chart(fig7, use_container_width=True)

    # Decade-wise bar
    st.subheader("Decade-wise average annual rainfall — all India")
    decade = rf.groupby("decade")["annual"].mean().reset_index()
    fig8 = px.bar(
        decade, x="decade", y="annual",
        title="Decade-wise average annual rainfall",
        labels={"annual":"Avg annual rainfall (mm)","decade":"Decade"},
        color="annual",
        color_continuous_scale="RdYlGn",
    )
    fig8.update_layout(height=380)
    st.plotly_chart(fig8, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 3 — CLIMATE STATISTICS
# ══════════════════════════════════════════════
with tab3:
    st.subheader("Climate statistics")

    col1, col2 = st.columns(2)

    with col1:
        # Correlation heatmap
        import numpy as np
        num_cols = ["temp_max","temp_min","temp_range",
                    "precipitation","windspeed","humidity_avg"]
        corr = filtered[num_cols].corr().round(2)

        fig9 = px.imshow(
            corr, text_auto=True, color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Correlation matrix — weather variables",
            aspect="auto"
        )
        fig9.update_layout(height=420)
        st.plotly_chart(fig9, use_container_width=True)

    with col2:
        # Humidity vs precipitation scatter
        sample = filtered[filtered["precipitation"] > 0].sample(
            min(2000, len(filtered[filtered["precipitation"] > 0]))
        )
        fig10 = px.scatter(
            sample, x="humidity_avg", y="precipitation",
            color="city_name", opacity=0.5, size_max=6,
            title="Humidity vs precipitation (rainy days)",
            labels={
                "humidity_avg":"Avg humidity (%)",
                "precipitation":"Precipitation (mm)",
                "city_name":"City"
            }
        )
        fig10.update_layout(height=420)
        st.plotly_chart(fig10, use_container_width=True)

    # Extreme rain days
    st.subheader("Extreme rainfall days (>50mm/day)")
    filtered["extreme"] = filtered["precipitation"] > 50
    extreme_yr = filtered.groupby(["city_name","year"])["extreme"].sum().reset_index()
    fig11 = px.bar(
        extreme_yr, x="year", y="extreme", color="city_name",
        title="Extreme rainfall days per year by city",
        labels={"extreme":"Extreme rain days","year":"Year","city_name":"City"},
        barmode="stack"
    )
    fig11.update_layout(height=380)
    st.plotly_chart(fig11, use_container_width=True)

    # City summary statistics table
    st.subheader("City summary statistics")
    summary = filtered.groupby("city_name").agg(
        avg_temp_max   =("temp_max",      "mean"),
        avg_temp_min   =("temp_min",      "mean"),
        avg_precip     =("precipitation", "mean"),
        avg_humidity   =("humidity_avg",  "mean"),
        avg_windspeed  =("windspeed",     "mean"),
        total_records  =("temp_max",      "count"),
    ).round(2).reset_index()
    summary.columns = ["City","Avg max °C","Avg min °C",
                        "Avg rain mm","Avg humidity %",
                        "Avg wind km/h","Records"]
    st.dataframe(summary, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4 — RAW DATA
# ══════════════════════════════════════════════
with tab4:
    st.subheader("Raw data explorer")

    display_cols = ["city_name","date","year","month","season",
                    "temp_max","temp_min","temp_range",
                    "precipitation","windspeed","humidity_avg"]

    st.dataframe(
        filtered[display_cols].sort_values("date", ascending=False),
        use_container_width=True,
        height=400
    )

    st.markdown(f"**{len(filtered):,} rows** matching current filters")

    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download filtered data as CSV",
        data=csv,
        file_name="india_weather_filtered.csv",
        mime="text/csv",
    )
