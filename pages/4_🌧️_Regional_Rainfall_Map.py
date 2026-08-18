"""
Regional Rainfall Map page — a filled spatial map of annual average
precipitation across South Asia, in the style of published climatology
maps (e.g. IPCC/research-paper rainfall maps): a continuous color surface
over the landmass, banded into standard mm ranges, with country borders.

This is deliberately different from the Climate Map page (which plots
8 cities colored by their decade-over-decade trend). This page shows
the actual annual rainfall VALUE — not a trend — across a grid spanning
the whole region, so it visually matches typical "annual average
precipitation" reference maps.

Because it queries a grid of points (not 8 fixed cities), it's far more
API-intensive. Points falling outside the target countries' borders are
skipped entirely (no ocean fetches), and everything is cached hard.
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
from shapely.geometry import shape, Point

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import fetch_historical_weather

st.set_page_config(page_title="Regional Rainfall Map", page_icon="🌧️", layout="wide")

GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-boundaries-world-110m/main/countries.geojson"
SOUTH_ASIA_COUNTRIES = ["Afghanistan", "Pakistan", "India", "Nepal", "Bhutan", "Bangladesh", "Sri Lanka", "Myanmar"]

LAT_MIN, LAT_MAX = 5, 38
LON_MIN, LON_MAX = 60, 95

# Bin edges (mm/year) and colors modeled on standard published South Asia
# annual-precipitation maps: red/orange = dry, through yellow-green, to
# blue/purple = very wet.
BIN_EDGES = [0, 100, 200, 400, 600, 800, 1000, 1500, 2000, 2500, 3000, 3600]
BIN_COLORS = [
    "#d7191c", "#f4a261", "#fdae61", "#fee08b", "#ffffbf", "#e6f598",
    "#abdda4", "#66c2a5", "#3288bd", "#5e4fa2", "#3d2b56",
]
BIN_LABELS = ["0-100", "100-200", "200-400", "400-600", "600-800", "800-1000",
              "1000-1500", "1500-2000", "2000-2500", "2500-3000", ">3000"]


@st.cache_data(show_spinner=False, ttl=30 * 86400)
def load_country_shapes():
    """Fetch + cache the lightweight country-borders dataset, filtered to
    South Asia. Returns (list of shapely geometries, border line traces
    as flat lon/lat lists with None separators for plotting)."""
    resp = requests.get(GEOJSON_URL, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    geoms = []
    lons, lats = [], []
    for feature in data["features"]:
        if feature["properties"].get("name") not in SOUTH_ASIA_COUNTRIES:
            continue
        geom = shape(feature["geometry"])
        geoms.append(geom)

        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for poly in polys:
            x, y = poly.exterior.coords.xy
            lons.extend(list(x) + [None])
            lats.extend(list(y) + [None])

    return geoms, lons, lats


def point_in_south_asia(lon, lat, geoms):
    pt = Point(lon, lat)
    return any(pt.intersects(g) for g in geoms)


@st.cache_data(show_spinner=False, ttl=30 * 86400)
def build_rainfall_grid(step_deg, start_year, end_year, _geoms):
    """Build a lat/lon grid, keep only points inside South Asia's borders,
    fetch each land point's mean annual total precipitation, and return a
    dataframe of results plus any per-point failures.

    `_geoms` is prefixed with underscore so Streamlit doesn't try to hash
    the shapely objects for caching — step/year args do the cache-keying.
    """
    lats = np.arange(LAT_MIN, LAT_MAX + 0.01, step_deg)
    lons = np.arange(LON_MIN, LON_MAX + 0.01, step_deg)

    land_points = [
        (lat, lon) for lat in lats for lon in lons
        if point_in_south_asia(lon, lat, _geoms)
    ]

    def fetch_point(lat, lon):
        for attempt in range(2):
            try:
                df = fetch_historical_weather(lat, lon, start_year, end_year)
                yearly_precip = df.groupby("year")["precipitation_sum"].sum()
                return (lat, lon, float(yearly_precip.mean()), None)
            except Exception as e:
                if attempt == 0:
                    time.sleep(1.5)
                else:
                    return (lat, lon, None, str(e))

    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch_point, lat, lon) for lat, lon in land_points]
        for i, fut in enumerate(as_completed(futures)):
            results.append(fut.result())

    df = pd.DataFrame(results, columns=["lat", "lon", "annual_precip_mm", "error"])
    return df, lats, lons


st.title("🌧️ South Asia — Annual Average Precipitation")
st.caption(
    "A continuous rainfall-value surface across the region, in the style of published "
    "climatology maps. Unlike the Climate Map page, this shows the actual annual rainfall "
    "amount — not a warming/precipitation trend."
)

with st.sidebar:
    st.header("🌧️ Rainfall Map Settings")
    resolution_label = st.select_slider(
        "Grid resolution",
        options=["Coarse (fast)", "Medium", "Fine (slow)"],
        value="Coarse (fast)",
        help="Finer resolution looks smoother but queries far more points — "
             "each step down roughly doubles the number of API calls.",
    )
    step_deg = {"Coarse (fast)": 3.0, "Medium": 2.0, "Fine (slow)": 1.25}[resolution_label]

    end_year_default = pd.Timestamp.today().year - 1
    years_back = st.slider(
        "Years to average over", 5, 30, 10,
        help="A shorter window is faster to compute and still representative of the "
             "current rainfall pattern; use 30 for the same window as the rest of the site.",
    )
    start_year = end_year_default - years_back + 1

    st.caption(f"Averaging {start_year}–{end_year_default}. Approx. grid spacing: {step_deg}°.")
    generate = st.button("🌏 Generate map", type="primary", use_container_width=True)

if "rainfall_grid" not in st.session_state:
    st.session_state.rainfall_grid = None

if generate:
    with st.spinner("Loading country borders..."):
        geoms, border_lons, border_lats = load_country_shapes()

    with st.spinner(
        f"Fetching {start_year}–{end_year_default} rainfall for a {resolution_label.split(' ')[0].lower()} "
        "grid across South Asia — this can take a couple of minutes on first run..."
    ):
        grid_df, lats, lons = build_rainfall_grid(step_deg, start_year, end_year_default, tuple(geoms))
    st.session_state.rainfall_grid = (grid_df, lats, lons, border_lons, border_lats, start_year, end_year_default)

if st.session_state.rainfall_grid is None:
    st.info("Choose a resolution in the sidebar and click **Generate map** to build the rainfall surface. "
            "First run takes 30 seconds to a few minutes depending on resolution; results are cached after that.")
    st.stop()

grid_df, lats, lons, border_lons, border_lats, s_year, e_year = st.session_state.rainfall_grid

failures = grid_df[grid_df["error"].notna()]
if len(failures) > 0:
    with st.expander(f"⚠️ {len(failures)} of {len(grid_df)} grid points failed to load", expanded=False):
        st.dataframe(failures[["lat", "lon", "error"]], use_container_width=True, hide_index=True)

valid = grid_df[grid_df["annual_precip_mm"].notna()]
if valid.empty:
    st.error("No grid points returned data — try again in a moment (likely a temporary rate limit).")
    st.stop()

# Reshape scattered (lat, lon, value) points onto the regular grid for go.Contour
z = np.full((len(lats), len(lons)), np.nan)
lat_idx = {round(v, 4): i for i, v in enumerate(lats)}
lon_idx = {round(v, 4): i for i, v in enumerate(lons)}
for _, row in valid.iterrows():
    i = lat_idx.get(round(row["lat"], 4))
    j = lon_idx.get(round(row["lon"], 4))
    if i is not None and j is not None:
        z[i, j] = row["annual_precip_mm"]

# Build a hard-stepped colorscale from the bin edges so the fill reads as
# discrete bands (matching published rainfall-map legends) rather than a
# smooth gradient.
zmax = BIN_EDGES[-1]
colorscale = []
for k in range(len(BIN_EDGES) - 1):
    pos_start = BIN_EDGES[k] / zmax
    pos_end = BIN_EDGES[k + 1] / zmax
    colorscale.append([pos_start, BIN_COLORS[k]])
    colorscale.append([pos_end, BIN_COLORS[k]])
colorscale[0][0] = 0.0
colorscale[-1][0] = 1.0

fig = go.Figure()

fig.add_trace(go.Contour(
    x=lons, y=lats, z=z,
    colorscale=colorscale,
    zmin=0, zmax=zmax,
    connectgaps=False,
    contours=dict(coloring="fill", showlines=False),
    colorbar=dict(
        title="mm/year",
        tickvals=[(BIN_EDGES[k] + BIN_EDGES[k + 1]) / 2 for k in range(len(BIN_EDGES) - 1)],
        ticktext=BIN_LABELS,
        len=0.85,
    ),
    hovertemplate="Lat %{y:.1f}, Lon %{x:.1f}<br>%{z:.0f} mm/year<extra></extra>",
))

fig.add_trace(go.Scatter(
    x=border_lons, y=border_lats, mode="lines",
    line=dict(color="#1A1A1A", width=1),
    hoverinfo="skip", showlegend=False,
))

fig.update_layout(
    height=680,
    xaxis=dict(title="Longitude", range=[LON_MIN, LON_MAX], scaleanchor="y", constrain="domain"),
    yaxis=dict(title="Latitude", range=[LAT_MIN, LAT_MAX]),
    paper_bgcolor="#F6F4EF",
    plot_bgcolor="#FFFFFF",
    font=dict(family="Inter, sans-serif", color="#1A1A1A"),
    margin=dict(l=10, r=10, t=10, b=10),
    title=dict(text=f"Annual Average Precipitation — South Asia ({s_year}–{e_year})", x=0.02),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    f"Grid spacing ≈ {step_deg}° · {len(valid)} land points sampled · "
    "Ocean and non-South-Asia areas are masked out using country border polygons, not fetched."
)

st.divider()
st.markdown(
    "**Data source:** [Open-Meteo Historical Weather API](https://open-meteo.com/) "
    f"(ERA5/ERA5-Land reanalysis), averaged {s_year}–{e_year}. Country borders: "
    "[Natural Earth 110m via datasets/geo-boundaries-world-110m](https://github.com/datasets/geo-boundaries-world-110m) "
    "(public domain). This is a coarse-grid approximation for visual pattern, not a "
    "peer-reviewed climatology product — spacing between sample points is "
    f"~{step_deg}°, so small-scale local variation (e.g. mountain rain-shadow effects) "
    "won't be fully resolved."
)
