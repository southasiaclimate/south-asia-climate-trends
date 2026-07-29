"""
Shared functions used by Home.py and the pages in pages/.
Keeping these in one place avoids copy-pasting the same fetch/geocode
logic into every page.
"""

import os
import re
import numpy as np
import pandas as pd
import requests
import streamlit as st


@st.cache_data(show_spinner=False)
def geocode_city(city_name: str):
    """Convert a city name into lat/lon using Open-Meteo's free geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 5, "language": "en", "format": "json"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("results", [])


@st.cache_data(show_spinner=False)
def fetch_historical_weather(lat: float, lon: float, start_year: int, end_year: int):
    """Pull daily historical weather from Open-Meteo Archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{start_year}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": "temperature_2m_mean,temperature_2m_max,precipitation_sum",
        "timezone": "auto",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()["daily"]
    df = pd.DataFrame(data)
    df["time"] = pd.to_datetime(df["time"])
    df["year"] = df["time"].dt.year
    return df


def trend_line(x, y):
    """Simple linear regression trend line. Returns (fitted_values, slope_per_year)."""
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return None, None
    coeffs = np.polyfit(x[mask], y[mask], 1)
    trend = np.poly1d(coeffs)
    return trend(x), coeffs[0]


def assign_season(month: int, scheme: str) -> str:
    """Map a month to a season label based on the chosen regional scheme."""
    if scheme == "South Asia Monsoon":
        if month in (12, 1, 2):
            return "Winter (Dec-Feb)"
        elif month in (3, 4, 5):
            return "Pre-Monsoon / Hot (Mar-May)"
        elif month in (6, 7, 8, 9):
            return "Monsoon (Jun-Sep)"
        else:
            return "Post-Monsoon (Oct-Nov)"
    else:
        if month in (12, 1, 2):
            return "Winter (Dec-Feb)"
        elif month in (3, 4, 5):
            return "Spring (Mar-May)"
        elif month in (6, 7, 8):
            return "Summer (Jun-Aug)"
        else:
            return "Autumn (Sep-Nov)"


@st.cache_data(show_spinner=False, ttl=3600)
def quick_city_trend(name: str, lat: float, lon: float, years_back: int = 12):
    """Lightweight recent warming-rate estimate for a city, used in the
    Home page's city ticker strip. Uses a shorter window than the full
    Dashboard analysis, purely so the ticker loads fast."""
    end_year = pd.Timestamp.today().year - 1
    start_year = end_year - years_back
    df = fetch_historical_weather(lat, lon, start_year, end_year)
    yearly = df.groupby("year")["temperature_2m_mean"].mean().reset_index()
    years = yearly["year"].values.astype(float)
    temps = yearly["temperature_2m_mean"].values
    _, slope = trend_line(years, temps)
    latest_temp = yearly["temperature_2m_mean"].iloc[-1] if len(yearly) else None
    return {
        "name": name,
        "latest_mean_temp": latest_temp,
        "decade_trend": slope * 10 if slope is not None else None,
    }


def load_posts():
    """Load markdown blog posts (with simple front-matter) from /posts."""
    posts_dir = os.path.join(os.path.dirname(__file__), "posts")
    posts = []
    if not os.path.isdir(posts_dir):
        return posts
    for fname in sorted(os.listdir(posts_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(posts_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        meta = {}
        body = content
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if match:
            front, body = match.groups()
            for line in front.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()

        posts.append({
            "filename": fname,
            "title": meta.get("title", fname),
            "date": meta.get("date", ""),
            "city": meta.get("city", ""),
            "country": meta.get("country", ""),
            "image": meta.get("image", ""),
            "external_url": meta.get("external_url", ""),
            "tags": meta.get("tags", ""),
            "body": body.strip(),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts
