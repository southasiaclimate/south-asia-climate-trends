"""
Dashboard page — Climate Trend Visualizer
--------------------------------------------
Lets a user search any city, pulls decades of historical daily weather
data (free, no API key) from Open-Meteo's Archive API, and visualizes
long-term climate trends:
  - Annual mean temperature trend (with linear regression line)
  - Annual total precipitation trend
  - Number of "extreme heat" days per year (customizable threshold)
  - Seasonal / monsoon breakdown

This page picks up a city automatically if it was searched on the
Home page (via the search box there), otherwise defaults to Rawalpindi.
"""

import sys
import os
import streamlit as st
import plotly.graph_objects as go
from datetime import date

# Allow importing utils.py from the project root (one level up from pages/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import geocode_city, fetch_historical_weather, trend_line, assign_season

st.set_page_config(page_title="Climate Trend Visualizer", layout="wide")

# ---------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------

# If the Home page search bar set a city, use it as the default here
default_city = st.session_state.get("selected_city", "Rawalpindi")

st.sidebar.title("🌍 Climate Trend Settings")
city_input = st.sidebar.text_input("Search a city", default_city)
end_year_default = date.today().year - 1
start_year = st.sidebar.number_input("Start year", min_value=1950, max_value=end_year_default, value=1995)
end_year = st.sidebar.number_input("End year", min_value=1951, max_value=end_year_default, value=end_year_default)
heat_threshold = st.sidebar.slider("Extreme heat threshold (°C, daily max)", 30, 50, 40)
season_scheme = st.sidebar.radio(
    "Seasonal scheme",
    ["South Asia Monsoon", "Generic 4-season"],
    help="South Asia Monsoon uses the Pakistan/India Met Dept calendar: "
         "Winter (Dec–Feb), Pre-Monsoon (Mar–May), Monsoon (Jun–Sep), Post-Monsoon (Oct–Nov)."
)

st.title("📈 Climate Trend Visualizer")
st.caption("Historical climate trends for any city, powered by Open-Meteo Archive data.")

# ---------------------------------------------------------------
# Geocode + fetch
# ---------------------------------------------------------------

if city_input:
    matches = geocode_city(city_input)
    if not matches:
        st.warning("No location found. Try a different spelling or a nearby major city.")
        st.stop()

    options = {f"{m['name']}, {m.get('admin1', '')}, {m['country']}": m for m in matches}
    choice = st.sidebar.selectbox("Confirm location", list(options.keys()))
    place = options[choice]
    lat, lon = place["latitude"], place["longitude"]

    with st.spinner(f"Fetching {start_year}–{end_year} data for {choice}..."):
        df = fetch_historical_weather(lat, lon, int(start_year), int(end_year))

    # ---------------------------------------------------------------
    # Aggregate to yearly stats
    # ---------------------------------------------------------------
    yearly = df.groupby("year").agg(
        mean_temp=("temperature_2m_mean", "mean"),
        total_precip=("precipitation_sum", "sum"),
        extreme_heat_days=("temperature_2m_max", lambda s: (s >= heat_threshold).sum()),
    ).reset_index()

    years = yearly["year"].values.astype(float)

    # ---------------------------------------------------------------
    # Layout: 3 charts
    # ---------------------------------------------------------------
    col1, col2 = st.columns(2)

    # Temperature trend
    with col1:
        temp_trend, temp_slope = trend_line(years, yearly["mean_temp"].values)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=yearly["year"], y=yearly["mean_temp"],
                                   mode="lines+markers", name="Annual Mean Temp"))
        if temp_trend is not None:
            fig1.add_trace(go.Scatter(x=yearly["year"], y=temp_trend,
                                       mode="lines", name="Trend", line=dict(dash="dash")))
        fig1.update_layout(title=f"Annual Mean Temperature — {choice}",
                            xaxis_title="Year", yaxis_title="°C", height=420)
        st.plotly_chart(fig1, use_container_width=True)
        if temp_slope is not None:
            st.metric("Warming rate", f"{temp_slope*10:.2f} °C / decade")

    # Precipitation trend
    with col2:
        precip_trend, precip_slope = trend_line(years, yearly["total_precip"].values)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=yearly["year"], y=yearly["total_precip"], name="Annual Precipitation"))
        if precip_trend is not None:
            fig2.add_trace(go.Scatter(x=yearly["year"], y=precip_trend,
                                       mode="lines", name="Trend", line=dict(dash="dash", color="orange")))
        fig2.update_layout(title=f"Annual Total Precipitation — {choice}",
                            xaxis_title="Year", yaxis_title="mm", height=420)
        st.plotly_chart(fig2, use_container_width=True)
        if precip_slope is not None:
            st.metric("Precipitation trend", f"{precip_slope*10:+.1f} mm / decade")

    # Extreme heat days
    st.subheader(f"🔥 Days per year with max temp ≥ {heat_threshold}°C")
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=yearly["year"], y=yearly["extreme_heat_days"], marker_color="crimson"))
    fig3.update_layout(xaxis_title="Year", yaxis_title="Days", height=350)
    st.plotly_chart(fig3, use_container_width=True)

    # ---------------------------------------------------------------
    # Seasonal / monsoon breakdown — the differentiator vs. generic weather sites
    # ---------------------------------------------------------------
    st.divider()
    st.header("🌦️ Seasonal & Monsoon Trend Breakdown")
    st.caption(
        "How each season has shifted over time — this is the kind of local, "
        "long-horizon insight most weather sites don't show."
    )

    df["month"] = df["time"].dt.month
    df["season"] = df["month"].apply(lambda m: assign_season(m, season_scheme))

    season_order = (
        ["Winter (Dec-Feb)", "Pre-Monsoon / Hot (Mar-May)", "Monsoon (Jun-Sep)", "Post-Monsoon (Oct-Nov)"]
        if season_scheme == "South Asia Monsoon"
        else ["Winter (Dec-Feb)", "Spring (Mar-May)", "Summer (Jun-Aug)", "Autumn (Sep-Nov)"]
    )

    seasonal_yearly = df.groupby(["year", "season"]).agg(
        mean_temp=("temperature_2m_mean", "mean"),
        total_precip=("precipitation_sum", "sum"),
    ).reset_index()

    tab_labels = st.tabs(season_order)
    for season_name, tab in zip(season_order, tab_labels):
        with tab:
            season_df = seasonal_yearly[seasonal_yearly["season"] == season_name].sort_values("year")
            if season_df.empty:
                st.info("No data available for this season in the selected range.")
                continue

            s_years = season_df["year"].values.astype(float)
            c1, c2 = st.columns(2)

            with c1:
                s_temp_trend, s_temp_slope = trend_line(s_years, season_df["mean_temp"].values)
                fig_s1 = go.Figure()
                fig_s1.add_trace(go.Scatter(x=season_df["year"], y=season_df["mean_temp"],
                                             mode="lines+markers", name="Mean Temp"))
                if s_temp_trend is not None:
                    fig_s1.add_trace(go.Scatter(x=season_df["year"], y=s_temp_trend,
                                                 mode="lines", name="Trend", line=dict(dash="dash")))
                fig_s1.update_layout(title=f"{season_name} — Mean Temperature",
                                      xaxis_title="Year", yaxis_title="°C", height=380)
                st.plotly_chart(fig_s1, use_container_width=True)
                if s_temp_slope is not None:
                    st.metric(f"{season_name} warming rate", f"{s_temp_slope*10:.2f} °C / decade")

            with c2:
                s_precip_trend, s_precip_slope = trend_line(s_years, season_df["total_precip"].values)
                fig_s2 = go.Figure()
                fig_s2.add_trace(go.Bar(x=season_df["year"], y=season_df["total_precip"], name="Total Precip"))
                if s_precip_trend is not None:
                    fig_s2.add_trace(go.Scatter(x=season_df["year"], y=s_precip_trend,
                                                 mode="lines", name="Trend",
                                                 line=dict(dash="dash", color="orange")))
                fig_s2.update_layout(title=f"{season_name} — Total Precipitation",
                                      xaxis_title="Year", yaxis_title="mm", height=380)
                st.plotly_chart(fig_s2, use_container_width=True)
                if s_precip_slope is not None:
                    st.metric(f"{season_name} precipitation trend", f"{s_precip_slope*10:+.1f} mm / decade")

    st.divider()
    st.markdown(
        "**Data source:** [Open-Meteo Historical Weather API](https://open-meteo.com/) "
        "(ERA5/ERA5-Land reanalysis). Free for non-commercial and most commercial use — "
        "check their license before heavy production traffic."
    )
else:
    st.info("Enter a city name in the sidebar to get started.")
