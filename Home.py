"""
Home page — landing page for the site, with custom styling.
Streamlit automatically turns this file (the one you run with
`streamlit run Home.py`) into the Home page, and every .py file
inside pages/ becomes another page, listed in the sidebar automatically.
"""

import streamlit as st

st.set_page_config(
    page_title="South Asia Climate Trends",
    page_icon="🌏",
    layout="wide",
)
# ---------------------------------------------------------------
# Custom styling
# Palette: deep monsoon-sky navy + slate teal + ochre (dried-wheat
# gold) accent — pulled from the region's sky and land, not a
# generic template palette.
# Type: Fraunces (serif, has real character) for display headings,
# Inter for body text, IBM Plex Mono for data/eyebrow labels — the
# monospace nods to station-readout / data-ticker typography, since
# this is a data-driven meteorology site.
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');

    :root {
        --navy: #101B2D;
        --slate-teal: #2E5A5E;
        --ochre: #D9A441;
        --cloud: #F6F4EF;
        --ink: #1A1A1A;
    }

    .stApp {
        background: var(--cloud);
    }

    /* Hide default Streamlit top padding so the hero sits higher */
    .block-container {
        padding-top: 2rem;
        max-width: 1100px;
    }

    /* Hero card */
    .hero {
        position: relative;
        background: linear-gradient(160deg, var(--navy) 0%, var(--slate-teal) 100%);
        border-radius: 18px;
        padding: 3.5rem 3rem 3rem 3rem;
        overflow: hidden;
        margin-bottom: 2.5rem;
    }
    .hero-isobars {
        position: absolute;
        top: -20%;
        right: -10%;
        width: 65%;
        height: 140%;
        opacity: 0.35;
        pointer-events: none;
    }
    .eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.78rem;
        letter-spacing: 0.14em;
        color: var(--ochre);
        text-transform: uppercase;
        margin-bottom: 0.9rem;
        position: relative;
        z-index: 1;
    }
    .hero h1 {
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 2.9rem;
        line-height: 1.15;
        color: var(--cloud);
        margin: 0 0 1rem 0;
        position: relative;
        z-index: 1;
        max-width: 75%;
    }
    .hero p.sub {
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #D8DEE0;
        max-width: 62%;
        line-height: 1.6;
        position: relative;
        z-index: 1;
    }
    .stat-row {
        display: flex;
        gap: 2.5rem;
        margin-top: 1.8rem;
        position: relative;
        z-index: 1;
    }
    .stat-num {
        font-family: 'Fraunces', serif;
        font-size: 1.7rem;
        color: var(--ochre);
        font-weight: 600;
    }
    .stat-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.7rem;
        color: #AEB8BA;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Section heading */
    .section-eyebrow {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        color: var(--slate-teal);
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .search-label {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.1rem;
        letter-spacing: 0.08em;
        color: var(--slate-teal);
        text-transform: uppercase;
        margin-bottom: 0.6rem;
        font-weight: 600;
    }

    div[data-testid="stTextInput"] input {
        font-size: 1.25rem;
        padding: 0.9rem 1rem;
        height: 3.2rem;
        border-radius: 10px;
    }

    div[data-testid="stButton"] button {
        font-size: 1.1rem;
        height: 3.2rem;
        border-radius: 10px;
    }
    
    div[data-testid="stTextInput"] input {
        font-size: 1.25rem;
        padding: 0.9rem 1rem;
        height: 3.2rem;
        border-radius: 10px;
        border: 2px solid var(--slate-teal);
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--ochre);
        box-shadow: 0 0 0 3px rgba(217, 164, 65, 0.25);
    }

    div[data-testid="stButton"] button {
        font-size: 1.1rem;
        height: 3.2rem;
        border-radius: 10px;
        background: var(--ochre);
        color: var(--navy);
        font-weight: 700;
        border: none;
    }

    div[data-testid="stButton"] button:hover {
        background: #C4922E;
        color: white;
    }
-----------------------------------------------------
    /* Nav cards */
    .nav-card {
        background: white;
        border: 2px solid #E6E2D8;
        border-top: 5px solid var(--slate-teal);
        border-radius: 14px;
        padding: 1.8rem 1.8rem 1.4rem 1.8rem;
        height: 100%;
        box-shadow: 0 3px 12px rgba(16, 27, 45, 0.06);
        transition: all 0.2s ease;
    }
    .nav-card:hover {
        border-color: var(--ochre);
        border-top: 5px solid var(--ochre);
        box-shadow: 0 8px 24px rgba(217, 164, 65, 0.2);
        transform: translateY(-4px);
    }
    .nav-card .icon {
        font-size: 2.2rem;
        margin-bottom: 0.6rem;
        display: inline-block;
        background: var(--cloud);
        width: 56px;
        height: 56px;
        line-height: 56px;
        text-align: center;
        border-radius: 12px;
    }
    
--------------------------------------
div[data-testid="stPageLink"] a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        background: var(--ochre);
        color: var(--navy) !important;
        padding: 0.9rem 1.3rem;
        height: 3.2rem;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 1.1rem;
        text-decoration: none !important;
        margin-top: 0.5rem;
        border: none;
        transition: background 0.15s ease, color 0.15s ease;
    }

    div[data-testid="stPageLink"] a:hover {
        background: #C4922E;
        color: white !important;
    }

    div[data-testid="stPageLink"] p {
        margin: 0;
        color: inherit !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
    }
-----------------------------------------------------------------
    /* Footer */
    .footer-note {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        color: #8A8A8A;
        letter-spacing: 0.02em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Hero
# ---------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <svg class="hero-isobars" viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">
            <g fill="none" stroke="#D9A441" stroke-width="1.4">
                <path d="M -20 260 Q 100 200 200 250 T 420 220" opacity="0.9"/>
                <path d="M -20 300 Q 100 240 200 290 T 420 260" opacity="0.7"/>
                <path d="M -20 340 Q 100 280 200 330 T 420 300" opacity="0.5"/>
                <path d="M -20 380 Q 100 320 200 370 T 420 340" opacity="0.3"/>
                <path d="M -20 220 Q 100 160 200 210 T 420 180" opacity="0.4"/>
            </g>
        </svg>
        <div class="eyebrow">STATION DATA &middot; 1995&ndash;2025 &middot; SOUTH ASIA</div>
        <h1>SOUTH ASIA CLIMATE TRENDS</h1>
    <p class="sub">
    Interactive trend data and reported analysis on how temperature,
    monsoon rainfall, and extreme heat have shifted across South
    Asia &mdash; built on reanalysis climate records, read by a
    meteorologist.
     </p>
        <div class="stat-row">
            <div><div class="stat-num">30+</div><div class="stat-label">Years of data</div></div>
            <div><div class="stat-num">ERA5</div><div class="stat-label">Reanalysis source</div></div>
            <div><div class="stat-num">4</div><div class="stat-label">Monsoon seasons tracked</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------
# Search box
# ---------------------------------------------------------------
#st.markdown('<div class="section-eyebrow">SEARCH A CITY</div>', unsafe_allow_html=True)
st.markdown('<div class="search-label">SEARCH A CITY</div>', unsafe_allow_html=True)

col_search, col_go = st.columns([5, 1])
with col_search:
    city_query = st.text_input(
        "Search a city",
        placeholder="e.g. Delhi, Karachi, Dhaka, Mumbai ...",
        label_visibility="collapsed",
    )
with col_go:
    go_clicked = st.button("View trends →", use_container_width=True)

if go_clicked and city_query:
    st.session_state["selected_city"] = city_query
    st.switch_page("pages/1_📊_Dashboard.py")

# ---------------------------------------------------------------
# Navigation cards
# ---------------------------------------------------------------
st.markdown('<div class="section-eyebrow">EXPLORE</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown(
        """
        <div class="nav-card">
            <div class="icon">📊</div>
            <h3>Dashboard</h3>
            <p>Search any city and see its temperature and rainfall trends,
            seasonal &amp; monsoon breakdowns, and extreme-heat-day counts,
            charted from three decades of data.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/1_📊_Dashboard.py", label="Open the Dashboard", icon="📊")

with col2:
    st.markdown(
        """
        <div class="nav-card">
            <div class="icon">📝</div>
            <h3>Blog</h3>
            <p>Written analysis on specific places and patterns &mdash;
            Karachi's rising heat, Pakistan's shifting monsoon, and more
            reporting drawn straight from the data.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.page_link("pages/2_📝_Blog.py", label="Read the Blog", icon="📝")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="footer-note">
    DATA SOURCE: <a href="https://open-meteo.com/en/docs/historical-weather-api"
    target="_blank" style="color: var(--slate-teal); font-weight: 600;">
    Open-Meteo Historical Weather API</a> (ERA5 / ERA5-Land reanalysis,
    Copernicus/ECMWF) &middot; Built by a Meteorologist/Climate Data Expert.
    </div>
    """,
    unsafe_allow_html=True,
)
