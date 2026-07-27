"""
Blog page — lists posts from /posts (via utils.load_posts), with
country-based filtering (South Asia) and a card grid showing an
excerpt + a placeholder banner image for each post. Clicking "Read
article" opens the full post.
"""

import sys
import os
import re
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_posts

st.set_page_config(page_title="Blog — Climate Trends", layout="wide")

# ---------------------------------------------------------------
# Styling — matches the Home page palette
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
    .stApp { background: var(--cloud); }
    .block-container { max-width: 1150px; }

    .blog-title {
        font-family: 'Fraunces', serif;
        font-weight: 700;
        font-size: 2.3rem;
        color: var(--navy);
        margin-bottom: 0.2rem;
    }
    .blog-caption {
        font-family: 'Inter', sans-serif;
        color: #565656;
        margin-bottom: 1.2rem;
    }

    /* Country filter pills */
    div[role="radiogroup"] {
        gap: 0.4rem;
    }
    div[role="radiogroup"] label {
        background: white;
        border: 1.5px solid #E6E2D8;
        border-radius: 20px;
        padding: 0.35rem 0.9rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
    }

    /* Story cards */
    .blog-card {
        background: white;
        border: 1px solid #E6E2D8;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 1.3rem;
        box-shadow: 0 2px 10px rgba(16, 27, 45, 0.05);
    }
    .blog-banner {
        height: 110px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.4rem;
    }
    .blog-card-body {
        padding: 1rem 1.2rem 1.2rem 1.2rem;
    }
    .blog-tag {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.66rem;
        color: var(--slate-teal);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .blog-card-title {
        font-family: 'Fraunces', serif;
        font-weight: 600;
        font-size: 1.08rem;
        color: var(--ink);
        margin: 0.3rem 0 0.4rem 0;
        line-height: 1.3;
    }
    .blog-excerpt {
        font-family: 'Inter', sans-serif;
        font-size: 0.86rem;
        color: #565656;
        line-height: 1.5;
        margin-bottom: 0.6rem;
    }
    .blog-meta {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.68rem;
        color: #9A9A9A;
    }

    div[data-testid="stButton"] button {
        background: var(--navy);
        color: var(--cloud);
        border: none;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }
    div[data-testid="stButton"] button:hover {
        background: var(--ochre);
        color: var(--navy);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Country metadata: flag emoji + banner gradient per country
# ---------------------------------------------------------------
COUNTRIES = {
    "Afghanistan": {"flag": "🇦🇫", "gradient": "linear-gradient(135deg,#7a6a53,#a68a5b)"},
    "Bangladesh": {"flag": "🇧🇩", "gradient": "linear-gradient(135deg,#0b6b3a,#0f9d58)"},
    "Bhutan": {"flag": "🇧🇹", "gradient": "linear-gradient(135deg,#8a2a2a,#c98a2a)"},
    "India": {"flag": "🇮🇳", "gradient": "linear-gradient(135deg,#c96a2a,#2a6b4a)"},
    "Maldives": {"flag": "🇲🇻", "gradient": "linear-gradient(135deg,#1a6b8a,#2aa6c9)"},
    "Nepal": {"flag": "🇳🇵", "gradient": "linear-gradient(135deg,#8a1a2a,#c92a4a)"},
    "Pakistan": {"flag": "🇵🇰", "gradient": "linear-gradient(135deg,#0b3d1e,#1a6b3a)"},
    "Sri Lanka": {"flag": "🇱🇰", "gradient": "linear-gradient(135deg,#8a4a1a,#c9862a)"},
}
DEFAULT_BANNER = {"flag": "🌦️", "gradient": "linear-gradient(160deg,#101B2D,#2E5A5E)"}


def make_excerpt(body: str, length: int = 140) -> str:
    """Strip basic markdown and return a short plain-text excerpt."""
    text = re.sub(r"[#*`_\[\]]", "", body)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:length].rsplit(" ", 1)[0] + "…" if len(text) > length else text


# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.markdown('<div class="blog-title">📝 Climate Trend Blog</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="blog-caption">Data-driven articles on climate and weather trends '
    'across South Asia.</div>',
    unsafe_allow_html=True,
)

posts = load_posts()

# Slug = filename without the .md extension, used in the shareable URL
for p in posts:
    p["slug"] = p["filename"].removesuffix(".md")

# Determine which post (if any) is selected — check the URL query param
# first (so links are shareable/bookmarkable), then fall back to session
# state (so the "Read article" button click still works within the app).
query_post = st.query_params.get("post")
if query_post:
    st.session_state["selected_post_slug"] = query_post

# ---------------------------------------------------------------
# Detail view (a specific article is selected)
# ---------------------------------------------------------------
if st.session_state.get("selected_post_slug"):
    selected = next((p for p in posts if p["slug"] == st.session_state["selected_post_slug"]), None)
    if selected:
        if st.button("← Back to all articles"):
            st.session_state["selected_post_slug"] = None
            st.query_params.clear()
            st.rerun()

        banner = COUNTRIES.get(selected["country"], DEFAULT_BANNER)
        st.markdown(
            f"""<div style="background:{banner['gradient']};height:140px;border-radius:14px;
            display:flex;align-items:center;justify-content:center;font-size:3rem;margin-bottom:1rem;">
            {banner['flag']}</div>""",
            unsafe_allow_html=True,
        )

        st.header(selected["title"])
        meta_line = []
        if selected["date"]:
            meta_line.append(f"📅 {selected['date']}")
        if selected["country"]:
            meta_line.append(f"🌏 {selected['country']}")
        if selected["city"]:
            meta_line.append(f"📍 {selected['city']}")
        if selected["tags"]:
            meta_line.append(f"🏷️ {selected['tags']}")
        if meta_line:
            st.caption(" · ".join(meta_line))

        st.caption(
            f"🔗 Shareable link: `?post={selected['slug']}` "
            "(add this to your Blog page URL to link directly to this article)"
        )

        st.markdown(selected["body"])
        st.divider()
        st.page_link("pages/1_📊_Dashboard.py", label="→ Explore this data on the Dashboard", icon="📊")
    else:
        st.session_state["selected_post_slug"] = None
        st.query_params.clear()
        st.rerun()

# ---------------------------------------------------------------
# Grid view (browse all articles, filterable by country)
# ---------------------------------------------------------------
else:
    if not posts:
        st.info("No posts yet — add markdown files to the `posts/` folder.")
    else:
        # Only show countries that actually have at least one post, so the
        # filter row isn't cluttered with empty categories while you're
        # still building out content.
        available_countries = sorted({p["country"] for p in posts if p["country"]})
        filter_options = ["All"] + available_countries
        chosen = st.radio(
            "Filter by country",
            filter_options,
            horizontal=True,
            label_visibility="collapsed",
        )

        filtered = posts if chosen == "All" else [p for p in posts if p["country"] == chosen]

        if not filtered:
            st.info(f"No articles yet for {chosen}. Check back soon.")
        else:
            cols = st.columns(3)
            for i, post in enumerate(filtered):
                banner = COUNTRIES.get(post["country"], DEFAULT_BANNER)
                with cols[i % 3]:
                    st.markdown(
                        f"""
                        <div class="blog-card">
                            <div class="blog-banner" style="background:{banner['gradient']};">
                                {banner['flag']}
                            </div>
                            <div class="blog-card-body">
                                <div class="blog-tag">{post['country'] or 'REPORT'}</div>
                                <div class="blog-card-title">{post['title']}</div>
                                <div class="blog-excerpt">{make_excerpt(post['body'])}</div>
                                <div class="blog-meta">{post['date']} &middot; {post['city']}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button("Read article", key=f"read_{post['filename']}", use_container_width=True):
                        st.session_state["selected_post_slug"] = post["slug"]
                        st.query_params["post"] = post["slug"]
                        st.rerun()
