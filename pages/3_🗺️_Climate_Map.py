"""
Climate Map page — geographic overview of every city in the series.
--------------------------------------------------------------------
Plots the 8 published cities on a map of South Asia, colored and sized
by their computed 30-year trend metrics (warming rate, precipitation
trend). Reuses the same fetch/trend utilities as the Dashboard page so
the numbers here always match what's reported in the individual city
articles.

Each city's data is fetched once and cached (see utils.fetch_historical_weather),
so the map is slow only on the very first load after a cache reset.
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import fetch_historical_weather, trend_line

st.set_page_config(page_title="Climate Map", page_icon="🗺️", layout="wide")

BASE_URL = "https://southasiaclimate.github.io/south-asia-climate-trends/"

# Coordinates + published article for every city currently in the series.
# Add a new row here whenever a new city report goes live — the map
# picks it up automatically, no other code changes needed.
# Coordinates + published article for every city currently in the series.
# Stored as tuples (not dicts) so this can be passed straight into a
# @st.cache_data function, which requires hashable arguments.
# Add a new row here whenever a new city report goes live — the map
# picks it up automatically, no other code changes needed.
# Format: (city, country, lat, lon, article_filename)
CITIES = (
    ("Karachi",   "Pakistan",   24.8607, 67.0011, "karachi-warming-trend.html"),
    ("Delhi",     "India",      28.6139, 77.2090, "delhi-warming-trend.html"),
    ("Dhaka",     "Bangladesh", 23.8103, 90.4125, "dhaka-warming-trend.html"),
    ("Colombo",   "Sri Lanka",  6.9271,  79.8612, "colombo-warming-trend.html"),
    ("Kathmandu", "Nepal",      27.7172, 85.3240, "kathmandu-warming-trend.html"),
    ("Lahore",    "Pakistan",   31.5497, 74.3436, "lahore-warming-trend.html"),
    ("Islamabad", "Pakistan",   33.6844, 73.0479, "islamabad-warming-trend.html"),
    ("Mumbai",    "India",      19.0760, 72.8777, "mumbai-climate-trends.html"),
)

START_YEAR = 1996
END_YEAR = date.today().year - 1


@st.cache_data(show_spinner=False, ttl=86400)
def build_city_trends(cities, start_year, end_year):
    """Fetch + compute annual warming rate and precip trend for every city.
    Cached for a day so re-running the app doesn't re-hit the API for
    cities that haven't changed. `cities` must be a tuple of tuples
    (city, country, lat, lon, url) — kept hashable for st.cache_data."""
    rows = []
    for city, country, lat, lon, url in cities:
        try:
            df = fetch_historical_weather(lat, lon, start_year, end_year)
        except Exception:
            continue  # skip a city rather than break the whole map on one failed fetch

        yearly = df.groupby("year").agg(
            mean_temp=("temperature_2m_mean", "mean"),
            total_precip=("precipitation_sum", "sum"),
        ).reset_index()
        years = yearly["year"].values.astype(float)

        _, temp_slope = trend_line(years, yearly["mean_temp"].values)
        _, precip_slope = trend_line(years, yearly["total_precip"].values)

        rows.append({
            "City": city,
            "Country": country,
            "lat": lat,
            "lon": lon,
            "url": BASE_URL + url,
            "Warming rate (°C/decade)": round(temp_slope * 10, 2) if temp_slope is not None else None,
            "Precip trend (mm/decade)": round(precip_slope * 10, 1) if precip_slope is not None else None,
            "Latest annual mean temp (°C)": round(yearly["mean_temp"].iloc[-1], 1),
            "Latest annual precip (mm)": round(yearly["total_precip"].iloc[-1]),
        })
    return pd.DataFrame(rows)


st.title("🗺️ South Asia Climate Map")
st.caption(
    f"All {len(CITIES)} cities in this series, plotted by their {START_YEAR}–{END_YEAR} "
    "trend — the same 30-year methodology used in every city report."
)

metric = st.sidebar.radio(
    "Color cities by",
    ["Warming rate (°C/decade)", "Precip trend (mm/decade)"],
    help="Switches both the marker color and which metric drives marker size.",
)
color_scale = "RdYlBu_r" if "Warming" in metric else "BrBG"

with st.spinner(f"Computing {START_YEAR}–{END_YEAR} trends for {len(CITIES)} cities..."):
    df = build_city_trends(CITIES, START_YEAR, END_YEAR)

if df.empty:
    st.error("Couldn't fetch data for any city right now — try refreshing in a moment.")
    st.stop()

fig = px.scatter_geo(
    df,
    lat="lat",
    lon="lon",
    color=metric,
    size=df[metric].abs(),
    size_max=32,
    hover_name="City",
    hover_data={
        "lat": False,
        "lon": False,
        "Country": True,
        "Warming rate (°C/decade)": True,
        "Precip trend (mm/decade)": True,
        "Latest annual mean temp (°C)": True,
        "Latest annual precip (mm)": True,
    },
    color_continuous_scale=color_scale,
    scope="asia",
)
fig.update_geos(
    lataxis_range=[4, 38],
    lonaxis_range=[60, 95],
    showcountries=True,
    countrycolor="#B8B2A0",
    showland=True,
    landcolor="#F6F4EF",
    showocean=True,
    oceancolor="#DCE9EA",
    showlakes=False,
    coastlinecolor="#8A8A8A",
)
fig.update_layout(
    height=560,
    margin=dict(l=0, r=0, t=10, b=0),
    paper_bgcolor="#F6F4EF",
    font=dict(family="Inter, sans-serif", color="#1A1A1A"),
    coloraxis_colorbar=dict(title=metric.split(" (")[0]),
)
st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("City-by-city trend data")
st.caption("Click through to any city's full report for the season-by-season breakdown.")

display_df = df[[
    "City", "Country", "Warming rate (°C/decade)", "Precip trend (mm/decade)",
    "Latest annual mean temp (°C)", "Latest annual precip (mm)",
]].sort_values("Warming rate (°C/decade)", ascending=False).reset_index(drop=True)

st.dataframe(display_df, use_container_width=True, hide_index=True)

cols = st.columns(4)
for i, row in df.sort_values("City").reset_index(drop=True).iterrows():
    with cols[i % 4]:
        st.link_button(f"{row['City']} report →", row["url"], use_container_width=True)

st.divider()
st.markdown(
    "**Data source:** [Open-Meteo Historical Weather API](https://open-meteo.com/) "
    f"(ERA5/ERA5-Land reanalysis), {START_YEAR}–{END_YEAR}. Trend rates are computed with the "
    "same linear regression used throughout this site — see the "
    "[South Asia climate trend report](https://southasiaclimate.github.io/south-asia-climate-trends/south-asia-climate-trend-report.html) "
    "for the narrative version of this comparison."
)
