"""
B2B AI Commerce Companion — Minimalist editorial design (Browser Company inspired)
Warm cream, ink typography, generous whitespace. Fully generative right panel.
"""
import sys
sys.path.insert(0, "/Users/utkarshkumar/Documents/Utkarsh 26 Workspace/10-19 Work/11 Projects/b2b-commerce-agent")

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

import re
import streamlit as st
import streamlit.components.v1 as components
from src.agent.react_agent import ReActAgent
from src.data.product_catalog import ProductCatalog
from src.data.solution_cart import SolutionCart
from src.data.models import ProductCategory

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ShopSense AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design tokens ─────────────────────────────────────────────────────────────
BG       = "#ECEAE3"          # warm cream (Browser Co.)
SURFACE  = "#F5F3EE"          # card/panel face
SURFACE2 = "#EDEBE4"          # alternate surface
INK      = "#1A1918"          # primary text
INK_MID  = "#706E68"          # secondary text
INK_DIM  = "#A8A59F"          # muted/labels
BORDER   = "rgba(26,25,24,0.1)"
BORDER_S = "rgba(26,25,24,0.18)"  # stronger border

# Category colors stay readable on cream
CATEGORIES = [
    {"id": "all",          "label": "All",           "color": "#1A1918"},
    {"id": "cameras",      "label": "Cameras",       "color": "#2563EB"},
    {"id": "video",        "label": "Video",         "color": "#7C3AED"},
    {"id": "accessories",  "label": "Accessories",   "color": "#059669"},
    {"id": "films",        "label": "Films & Media", "color": "#D97706"},
]
CAT_COLOR = {c["id"]: c["color"] for c in CATEGORIES}
CAT_LABEL = {c["id"]: c["label"] for c in CATEGORIES}

DEFAULT_HEADLINE = "Find your perfect camera,\nintelligently matched."
DEFAULT_SUBTITLE = "Consumer Electronics · AI-Curated"


# ── CSS ───────────────────────────────────────────────────────────────────────
def inject_css(in_session: bool = False):
    st.markdown(f"""
<style>
/* ── Google Fonts: EB Garamond for editorial headings ── */
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600&display=swap');

/* ── Reset ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.stApp {{ background: {BG}; }}
[data-testid="stAppViewContainer"] {{ background: {BG}; }}
[data-testid="stSidebar"] {{ display: none !important; }}
.block-container {{ padding: 0 !important; max-width: 100% !important; }}
div[data-testid="stVerticalBlock"] > div {{ gap: 0 !important; }}

/* ── Top nav ── */
.nav-bar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 16px 40px;
    background: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}
.nav-brand {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 18px; font-weight: 500; color: {INK}; letter-spacing: 0.01em;
    cursor: pointer;
}}
.nav-brand:hover {{ opacity: 0.7; }}

.nav-badge {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; color: {INK_DIM}; letter-spacing: 0.12em;
    text-transform: uppercase;
}}
.nav-user-name {{
    font-family: 'Inter', sans-serif;
    font-size: 12px; color: {INK_MID}; letter-spacing: 0.02em;
}}

/* ── Left column background ── */
div[data-testid="column"]:first-child {{
    background: {SURFACE};
    border-right: 1px solid {BORDER};
}}

/* ── Chat header ── */
.chat-header {{
    padding: 20px 24px 16px;
    border-bottom: 1px solid {BORDER};
}}
.chat-label {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 600; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.12em;
}}

/* ── Chat messages (native Streamlit container handles scroll) ── */
.chat-msg-user {{
    align-self: flex-end; max-width: 86%;
    background: {INK};
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px; font-size: 13.5px;
    color: #F5F3EE; line-height: 1.55;
    margin: 5px 0;
    font-family: 'Inter', sans-serif;
}}
.chat-msg-ai {{
    align-self: flex-start; max-width: 94%;
    background: {BG};
    border: 1px solid {BORDER};
    border-radius: 2px 12px 12px 12px;
    padding: 12px 16px; font-size: 13.5px;
    color: {INK}; line-height: 1.65;
    margin: 5px 0;
    font-family: 'Inter', sans-serif;
}}
.ai-label {{
    font-size: 9px; color: {INK_DIM}; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;
}}
.thinking-dots {{
    display: flex; gap: 5px; align-items: center;
    padding: 10px 14px;
    background: {BG}; border: 1px solid {BORDER};
    border-radius: 2px 12px 12px 12px;
    width: fit-content; margin: 5px 0;
}}
.thinking-dots span {{
    width: 5px; height: 5px; background: {INK_DIM};
    border-radius: 50%; animation: dots 1.2s ease-in-out infinite;
}}
.thinking-dots span:nth-child(2) {{ animation-delay: .2s; }}
.thinking-dots span:nth-child(3) {{ animation-delay: .4s; }}
@keyframes dots {{
    0%,60%,100% {{ opacity:.25; transform:scale(1); }}
    30% {{ opacity:1; transform:scale(1.3); }}
}}

/* ── Input area ── */
.input-wrap {{
    padding: 14px 20px;
    border-top: 1px solid {BORDER};
    background: {SURFACE};
}}
div[data-testid="stTextInput"] input {{
    background: transparent !important; border: none !important;
    color: {INK} !important; font-size: 13.5px !important;
    box-shadow: none !important; padding: 0 !important;
    font-family: 'Inter', sans-serif !important;
}}
div[data-testid="stTextInput"] > div > div {{
    background: {BG} !important;
    border: 1px solid {BORDER_S} !important;
    border-radius: 6px !important; padding: 10px 14px !important;
    transition: border-color .15s !important;
}}
div[data-testid="stTextInput"] > div > div:focus-within {{
    border-color: {INK} !important;
}}
div[data-testid="stTextInput"] label {{ display: none !important; }}

/* ── Hero section (right panel top) ── */
.hero-section {{
    padding: 40px 44px 32px;
    background: {BG};
    border-bottom: 1px solid {BORDER};
}}
.hero-eyebrow {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 600; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 14px;
}}
.hero-title {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 34px; font-weight: 500; color: {INK};
    line-height: 1.18; letter-spacing: -0.02em;
    white-space: pre-line; margin-bottom: 8px;
}}
.hero-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 12px; color: {INK_MID}; letter-spacing: 0.02em;
}}

/* ── AI Insight block ── */
.insight-block {{
    padding: 24px 44px;
    background: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}
.insight-label {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 600; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 10px;
}}
.insight-quote {{
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic; font-size: 16px; color: {INK};
    line-height: 1.6; margin-bottom: 12px;
}}
.insight-chips {{
    display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;
}}
.insight-chip {{
    font-family: 'Inter', sans-serif;
    font-size: 11px; color: {INK_MID};
    background: {BG}; border: 1px solid {BORDER_S};
    border-radius: 4px; padding: 4px 10px;
    letter-spacing: 0.01em;
}}

/* ── Segmented control / category tabs ── */
div[data-testid="stSegmentedControl"] {{
    background: transparent !important;
    padding: 12px 44px 10px !important;
    border-bottom: 1px solid {BORDER} !important;
}}
div[data-testid="stSegmentedControl"] > div {{
    background: transparent !important;
    border: none !important; border-radius: 0 !important;
    gap: 0 !important;
}}
div[data-testid="stSegmentedControl"] button {{
    color: {INK_DIM} !important; font-family: 'Inter', sans-serif !important;
    font-size: 11px !important; font-weight: 500 !important;
    letter-spacing: 0.05em !important; text-transform: uppercase !important;
    border-radius: 0 !important; border-bottom: 2px solid transparent !important;
    padding: 6px 14px !important; background: transparent !important;
}}
div[data-testid="stSegmentedControl"] button[aria-checked="true"] {{
    color: {INK} !important; border-bottom: 2px solid {INK} !important;
    background: transparent !important;
}}
div[data-testid="stSegmentedControl"] label {{ display: none !important; }}

/* ── Loading overlay ── */
.loading-overlay {{
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 16px; padding: 80px 40px;
    min-height: 320px;
}}
.loading-text {{
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic; font-size: 17px; color: {INK_MID};
}}
.loading-steps {{
    font-family: 'Inter', sans-serif;
    font-size: 11px; color: {INK_DIM}; margin-top: 4px;
    letter-spacing: 0.04em;
}}
@keyframes spin-slow {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}

/* ── Product card ── */
.product-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px; padding: 20px;
    position: relative; overflow: hidden;
    transition: border-color .2s ease;
}}
.product-card:hover {{ border-color: {BORDER_S}; }}
.product-card-bar {{
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px; border-radius: 4px 4px 0 0;
}}
.product-cat-label {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 10px;
}}
.product-name {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 16px; font-weight: 500; color: {INK};
    line-height: 1.3; margin-bottom: 4px;
}}
.product-sku {{
    font-family: 'Inter', sans-serif; font-size: 9px; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px;
}}
.product-desc {{
    font-family: 'Inter', sans-serif;
    font-size: 11.5px; color: {INK_MID}; line-height: 1.55;
    margin-bottom: 12px;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}}
.product-price-row {{
    display: flex; align-items: center; justify-content: space-between;
    margin-top: 12px; padding-top: 10px;
    border-top: 1px solid {BORDER};
}}
.product-price {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 20px; font-weight: 500; color: {INK};
}}
.product-stock {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; color: #059669; font-weight: 600; letter-spacing: 0.04em;
}}
.product-stock.out {{ color: #DC2626; }}
.rec-tag {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; font-weight: 600; color: {INK_MID};
    text-transform: uppercase; letter-spacing: 0.1em;
    border: 1px solid {BORDER_S}; border-radius: 3px;
    padding: 2px 7px; margin-bottom: 8px; width: fit-content;
}}

/* ── Cart summary bar ── */
.cart-bar {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 44px;
    background: {INK}; color: #F5F3EE;
    font-family: 'Inter', sans-serif; font-size: 12px;
}}
.cart-bar-total {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 19px; font-weight: 500;
}}

/* ── Solution bundle (cart list) ── */
.bundle-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px; padding: 18px 22px;
    margin: 0 44px 16px;
}}

/* ── Streamlit buttons — minimal ink style ── */
div[data-testid="stButton"] > button {{
    background: {INK} !important;
    color: #F5F3EE !important; border: none !important;
    border-radius: 4px !important; font-weight: 500 !important;
    font-size: 12px !important; padding: 8px 20px !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.03em !important;
    transition: opacity .15s !important;
}}
div[data-testid="stButton"] > button:hover {{
    opacity: 0.82 !important; transform: none !important;
}}

/* ── Expander ── */
div[data-testid="stExpander"] {{
    background: {BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 4px !important; margin: 4px 0 !important;
}}
div[data-testid="stExpander"] summary {{
    font-size: 11px !important; color: {INK_MID} !important;
    font-weight: 500 !important; font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.04em !important;
}}

/* ── Columns ── */
div[data-testid="column"] {{ padding: 0 !important; }}

/* ── Scrollbars ── */
::-webkit-scrollbar {{ width: 3px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {BORDER_S}; border-radius: 2px; }}

/* ── Initial hero ── */
.initial-hero {{
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; padding: 80px 40px 60px;
    background: {BG};
}}
.initial-eyebrow {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 600; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.14em; margin-bottom: 24px;
}}
.initial-title {{
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic; font-size: 48px; font-weight: 400; color: {INK};
    line-height: 1.15; letter-spacing: -0.02em;
    margin-bottom: 18px; max-width: 640px;
}}
.initial-sub {{
    font-family: 'Inter', sans-serif;
    font-size: 13px; color: {INK_MID}; max-width: 440px;
    line-height: 1.65; margin-bottom: 48px;
}}

/* ── Warning banner ── */
.warning-bar {{
    background: #FEF3C7; color: #92400E;
    padding: 8px 40px; font-size: 11px;
    border-bottom: 1px solid #FDE68A;
    font-family: 'Inter', sans-serif; letter-spacing: 0.01em;
}}

/* ── Modal / Dialog — cream theme ── */
/* Backdrop overlay */
[data-testid="stDialog"] > div {{
    background: rgba(26,25,24,0.5) !important;
    backdrop-filter: blur(2px);
}}
/* Dialog box itself */
[data-testid="stDialog"] [role="dialog"] {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER_S} !important;
    border-radius: 8px !important;
    box-shadow: 0 12px 48px rgba(26,25,24,0.22) !important;
    color: {INK} !important;
}}
/* Text nodes → ink (not white). Exclude buttons, which handle their own color) */
[data-testid="stDialog"] [role="dialog"] p,
[data-testid="stDialog"] [role="dialog"] small {{
    color: {INK};
}}
/* Confirm (primary) button — prominent outlined style */
[data-testid="stDialog"] [role="dialog"] button[data-testid="stBaseButton-primary"] {{
    border: 1.5px solid {INK} !important;
    border-radius: 3px !important;
    color: {INK} !important;
    font-weight: 600 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    letter-spacing: 0.02em !important;
}}
[data-testid="stDialog"] [role="dialog"] button[data-testid="stBaseButton-primary"]:hover {{
    background: {INK} !important;
    color: {SURFACE} !important;
}}
/* Cancel (secondary) button — outlined */
[data-testid="stDialog"] [role="dialog"] [data-testid="stBaseButton-secondary"] {{
    background: transparent !important;
    color: {INK_MID} !important;
    border: 1px solid {BORDER_S} !important;
    border-radius: 3px !important;
}}
[data-testid="stDialog"] [role="dialog"] [data-testid="stBaseButton-secondary"]:hover {{
    background: {BG} !important;
    color: {INK} !important;
}}
/* Title */
[data-testid="stDialog"] [role="dialog"] h2 {{
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 22px !important; font-weight: 500 !important;
    color: {INK} !important; letter-spacing: 0.01em !important;
}}
/* Close button */
[data-testid="stDialog"] [role="dialog"] > button {{
    color: {INK_MID} !important;
    background: transparent !important;
    border: none !important;
}}
/* Labels */
[data-testid="stDialog"] [role="dialog"] label {{
    font-family: 'Inter', sans-serif !important;
    font-size: 11px !important; color: {INK_MID} !important;
}}
/* Inputs and textareas */
[data-testid="stDialog"] [role="dialog"] input,
[data-testid="stDialog"] [role="dialog"] textarea {{
    background: {BG} !important;
    border-color: {BORDER_S} !important;
    color: {INK} !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    border-radius: 3px !important;
}}
[data-testid="stDialog"] [role="dialog"] input:focus,
[data-testid="stDialog"] [role="dialog"] textarea:focus {{
    border-color: {INK} !important;
    box-shadow: none !important;
}}
/* Horizontal rules */
[data-testid="stDialog"] [role="dialog"] hr {{
    border-color: {BORDER} !important;
}}

/* ── Recommendation cards (Generative UI) ── */
.rec-intro {{
    padding: 22px 44px 18px;
    background: {SURFACE};
    border-bottom: 1px solid {BORDER};
}}
.rec-intro-text {{
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic; font-size: 16px; color: {INK};
    line-height: 1.65; max-width: 640px;
}}
.rec-section-hdr {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; font-weight: 600; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.12em;
    padding: 16px 44px 8px;
}}
.rec-card {{
    position: relative;
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    margin: 0 44px 10px;
    overflow: hidden;
    transition: border-color .2s ease;
}}
.rec-card:hover {{ border-color: {BORDER_S}; }}
.rec-card-stripe {{
    position: absolute;
    top: 0; left: 0; bottom: 0; width: 3px;
}}
.rec-card-inner {{
    display: flex; align-items: stretch;
    padding: 22px 24px 20px 28px;
}}
.rec-card-left {{ flex: 1.6; min-width: 0; }}
.rec-card-divider {{
    width: 1px; background: {BORDER};
    align-self: stretch; margin: 0 24px; flex-shrink: 0;
}}
.rec-card-right {{
    flex: 1; display: flex;
    flex-direction: column; justify-content: space-between; min-width: 0;
}}
.rec-badge-row {{
    display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
}}
.rec-num {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 14px; font-style: italic; color: {INK_DIM};
}}
.rec-tag-pill {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {INK_MID}; background: {BG};
    border: 1px solid {BORDER_S};
    border-radius: 3px; padding: 2px 7px;
}}
.rec-cat-lbl {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px;
}}
.rec-prod-name {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 20px; font-weight: 500; color: {INK};
    line-height: 1.2; margin-bottom: 3px;
}}
.rec-prod-sku {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; color: {INK_DIM};
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px;
}}
.rec-spec-chips {{ display: flex; flex-wrap: wrap; gap: 5px; margin-top: 2px; }}
.spec-chip {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; color: {INK_MID};
    background: {BG}; border: 1px solid {BORDER};
    border-radius: 3px; padding: 3px 8px;
}}
.rec-why-label {{
    font-family: 'Inter', sans-serif;
    font-size: 9px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.1em;
    color: {INK_DIM}; margin-bottom: 8px;
}}
.why-bullet {{
    font-family: 'Inter', sans-serif;
    font-size: 11.5px; color: {INK_MID};
    line-height: 1.5; margin-bottom: 5px;
    padding-left: 10px; text-indent: -10px;
}}
.rec-price-area {{
    margin-top: auto; padding-top: 12px;
    border-top: 1px solid {BORDER};
}}
.rec-price-val {{
    font-family: 'EB Garamond', Georgia, serif;
    font-size: 24px; font-weight: 500; color: {INK}; line-height: 1;
}}
.rec-stock-lbl {{
    font-family: 'Inter', sans-serif;
    font-size: 10px; color: #059669;
    font-weight: 600; letter-spacing: 0.04em; margin-top: 3px;
}}
.rec-stock-out {{ color: #DC2626 !important; }}

/* ── Responsive: tablet ── */
@media (max-width: 1024px) {{
    .hero-title {{ font-size: 26px !important; }}
    .initial-title {{ font-size: 34px !important; }}
    .nav-bar {{ padding: 14px 24px; }}
    .hero-section {{ padding: 28px 28px 22px; }}
    .insight-block {{ padding: 18px 28px; }}
    div[data-testid="stSegmentedControl"] {{ padding: 10px 28px 8px !important; }}
}}

/* ── Responsive: mobile ── */
@media (max-width: 768px) {{
    .nav-bar {{ padding: 12px 16px; }}
    .hero-section {{ padding: 22px 20px 18px; }}
    .hero-title {{ font-size: 22px !important; }}
    .initial-title {{ font-size: 28px !important; }}
    .product-card {{ padding: 14px; }}
    div[data-testid="column"] {{ min-width: 100% !important; }}
}}
{"" if not in_session else f"""
/* ── Brand button (session mode) — plain text, no chrome ──
   Safe: in session, quick links are hidden, so first-col button = brand only */
[data-testid="stHorizontalBlock"]:first-child [data-testid="stColumn"]:first-child button {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 16px 0 16px 40px !important;
    height: auto !important;
    min-height: 0 !important;
    font-family: 'EB Garamond', Georgia, serif !important;
    font-size: 18px !important;
    font-weight: 500 !important;
    color: {INK} !important;
    letter-spacing: 0.01em !important;
    line-height: 1 !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    text-align: left !important;
    width: 100% !important;
}}
[data-testid="stHorizontalBlock"]:first-child [data-testid="stColumn"]:first-child button:hover,
[data-testid="stHorizontalBlock"]:first-child [data-testid="stColumn"]:first-child button:focus,
[data-testid="stHorizontalBlock"]:first-child [data-testid="stColumn"]:first-child button:active {{
    opacity: 0.65 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    color: {INK} !important;
}}
"""}
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages": [],
        "show_chat": False,
        "is_loading": False,
        "recommended_products": None,
        "solution_items": {},
        "hero_headline": DEFAULT_HEADLINE,
        "hero_subtitle": DEFAULT_SUBTITLE,
        "hero_context": "all",
        "layout_type": "grid",
        "cat_tabs": "all",
        "llm_warning": "",
        "mode_used": "demo",
        "ai_analysis": "",       # full final_answer for right panel blocks
        "analysis_chips": [],    # key insight chips
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_session()
catalog = ProductCatalog()


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_cat_color(cat_id: str) -> str:
    return CAT_COLOR.get(cat_id, INK_MID)


def compute_match_score(product, query: str = "") -> int:
    if not query:
        return 85
    q = query.lower()
    score = 55
    if q in product.name.lower():
        score += 30
    elif any(t in product.name.lower() for t in q.split() if len(t) > 3):
        score += 15
    if any(t in product.description.lower() for t in q.split() if len(t) > 3):
        score += 10
    if any(t in " ".join(product.tags) for t in q.split() if len(t) > 3):
        score += 8
    return min(score, 99)


def get_product_features(product) -> list:
    features = []
    specs = product.specifications or {}
    if "capacity_sqft" in specs:
        features.append(f"Covers {specs['capacity_sqft']:,} sq ft")
    if "capacity_va" in specs:
        features.append(f"{specs['capacity_va']:,} VA")
    if "runtime_min" in specs:
        features.append(f"{specs['runtime_min']} min runtime")
    if "sensors" in specs:
        features.append(f"{specs['sensors']} sensor channels")
    if "outlets" in specs:
        features.append(f"{specs['outlets']} outlets")
    return features[:3]


def get_filtered_products():
    recommended = st.session_state.recommended_products
    if recommended is None:
        return []
    active_cat = st.session_state.get("cat_tabs", "all")
    if active_cat and active_cat != "all":
        try:
            cat_enum = ProductCategory(active_cat)
            return [p for p in recommended if p.category == cat_enum]
        except ValueError:
            pass
    return recommended


def add_to_solution(product):
    sku = product.sku
    if sku in st.session_state.solution_items:
        st.session_state.solution_items[sku]["qty"] += 1
    else:
        st.session_state.solution_items[sku] = {
            "name": product.name,
            "price": product.price or 0,
            "category": product.category.value,
            "qty": 1,
        }


def remove_from_solution(sku: str):
    st.session_state.solution_items.pop(sku, None)


def _short_chat_reply(final_answer: str, n_products: int) -> str:
    """Extract a brief conversational reply for the chat panel."""
    clean = re.sub(r'^#+\s*', '', final_answer, flags=re.MULTILINE)
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
    clean = re.sub(r'^[\U0001F000-\U0001FFFF\u2600-\u27BF\U0001F300-\U0001FAFF]\s*', '', clean, flags=re.MULTILINE)
    lines = [l.strip() for l in clean.split('\n') if l.strip() and len(l.strip()) > 30]
    if not lines:
        return f"Found {n_products} solution{'s' if n_products != 1 else ''}. Full analysis shown on the right."
    first = lines[0].split('.')[0].strip()
    if len(first) > 160:
        first = first[:160] + "…"
    suffix = f" — {n_products} solution{'s' if n_products != 1 else ''} shown." if n_products else "."
    return first + suffix


def _build_chips(products, query: str) -> list:
    """Build quick-insight chips from products and query."""
    chips = []
    if not products:
        return chips
    prices = [p.price for p in products if p.price]
    if prices:
        chips.append(f"From ${min(prices):,.0f}")
    cats = list({p.category.value for p in products})
    if len(cats) == 1:
        chips.append(f"{CAT_LABEL.get(cats[0], cats[0].title())}")
    chips.append(f"{len(products)} product{'s' if len(products) != 1 else ''}")
    in_stock = sum(1 for p in products if p.in_stock)
    if in_stock < len(products):
        chips.append(f"{in_stock} in stock")
    return chips[:4]


# ── Order confirmation dialog ─────────────────────────────────────────────────
@st.dialog("Place Order")
def show_order_confirmation():
    # JS fixer: apply inline styles to dialog buttons AFTER Streamlit's cascade
    components.html(f"""<script>
    (function(){{
        const INK='{INK}', INK_MID='{INK_MID}', BORDER_S='{BORDER_S}', SURFACE='{SURFACE}';
        function styleButtons(){{
            const doc=window.parent.document;
            const dlg=doc.querySelector('[data-testid="stDialog"] [role="dialog"]');
            if(!dlg) return;
            const p=dlg.querySelector('button[data-testid="stBaseButton-primary"]');
            if(p&&!p.dataset.cc){{
                p.style.setProperty('border','1.5px solid '+INK,'important');
                p.style.setProperty('background','transparent','important');
                p.style.setProperty('color',INK,'important');
                p.style.setProperty('font-weight','600','important');
                p.style.setProperty('border-radius','3px','important');
                p.addEventListener('mouseenter',function(){{
                    this.style.setProperty('background',INK,'important');
                    this.style.setProperty('color',SURFACE,'important');
                }});
                p.addEventListener('mouseleave',function(){{
                    this.style.setProperty('background','transparent','important');
                    this.style.setProperty('color',INK,'important');
                }});
                p.dataset.cc='1';
            }}
            const c=dlg.querySelector('[data-testid="stBaseButton-secondary"]');
            if(c&&!c.dataset.cc){{
                c.style.setProperty('background','transparent','important');
                c.style.setProperty('color',INK_MID,'important');
                c.style.setProperty('border','1px solid '+BORDER_S,'important');
                c.style.setProperty('border-radius','3px','important');
                c.dataset.cc='1';
            }}
        }}
        let t=0; const iv=setInterval(()=>{{styleButtons();if(++t>30)clearInterval(iv);}},80);
    }})();
    </script>""", height=0)

    items = st.session_state.solution_items
    if not items:
        st.markdown("Your solution is empty.")
        return

    total = sum(v["price"] * v["qty"] for v in items.values())
    count = sum(v["qty"] for v in items.values())

    st.markdown(
        f"<div style='background:{SURFACE};border:1px solid {BORDER};"
        f"border-radius:4px;padding:14px 18px;margin-bottom:16px;font-family:Inter,sans-serif;'>"
        f"<div style='font-size:9px;color:{INK_DIM};font-weight:600;text-transform:uppercase;"
        f"letter-spacing:0.12em;margin-bottom:6px;'>Order Summary</div>"
        f"<div style='font-family:EB Garamond,Georgia,serif;font-size:28px;color:{INK};'>${total:,.0f}</div>"
        f"<div style='font-size:11px;color:{INK_MID};margin-top:2px;'>{count} product{'s' if count != 1 else ''} · Est. 5–7 business days</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    for sku, item in items.items():
        color = get_cat_color(item["category"])
        col_info, col_qty, col_price = st.columns([5, 2, 2])
        with col_info:
            st.markdown(
                f"<div style='font-size:9px;color:{color};text-transform:uppercase;font-weight:600;"
                f"letter-spacing:0.08em;'>{item['category']}</div>"
                f"<div style='font-family:EB Garamond,Georgia,serif;font-size:15px;color:{INK};'>{item['name']}</div>",
                unsafe_allow_html=True,
            )
        with col_qty:
            st.markdown(f"<div style='font-size:11px;color:{INK_MID};padding-top:12px;'>×{item['qty']}</div>",
                        unsafe_allow_html=True)
        with col_price:
            st.markdown(
                f"<div style='font-size:13px;color:{INK};text-align:right;padding-top:10px;"
                f"font-family:EB Garamond,Georgia,serif;'>${item['price'] * item['qty']:,.0f}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:6px 0;'>",
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        name = st.text_input("Full name", value="Priya Sharma", key="o_name")
    with c2:
        email = st.text_input("Email", value="priya@shopsense.demo", key="o_email")
    c3, c4 = st.columns(2)
    with c3:
        phone = st.text_input("Phone", value="+91 98765 43210", key="o_ph")
    with c4:
        st.text_input("Country", value="India", key="o_country")
    st.text_area("Shipping address", value="42 MG Road\nBengaluru, Karnataka 560001",
                 key="o_ship", height=64)
    st.markdown("<br>", unsafe_allow_html=True)
    ca, cb = st.columns([3, 1])
    with ca:
        if st.button(f"Confirm order · ${total:,.0f}", use_container_width=True,
                     key="confirm_order", type="primary"):
            st.success(f"Order placed — confirmation sent to {email}.")
            st.balloons()
    with cb:
        if st.button("Cancel", use_container_width=True, key="cancel_order"):
            st.rerun()


# ── Nav ───────────────────────────────────────────────────────────────────────
def render_nav():
    mode = st.session_state.get("mode_used", "demo")
    mode_map = {"moonshot": "Kimi K2", "anthropic": "Claude", "demo": "Demo"}
    mode_name = mode_map.get(mode, "Demo")

    col_brand, col_center, col_user = st.columns([3, 4, 3])

    in_session = st.session_state.get("show_chat", False)

    with col_brand:
        # Brand name IS the home — clickable button in session, plain text on home screen
        if in_session:
            if st.button("ShopSense", key="brand_home_btn"):
                for k in ("show_chat", "messages", "recommended_products", "solution_items",
                          "llm_warning", "ai_analysis", "analysis_chips"):
                    if k in ("messages", "analysis_chips"):
                        st.session_state[k] = []
                    elif k == "solution_items":
                        st.session_state[k] = {}
                    elif k == "show_chat":
                        st.session_state[k] = False
                    else:
                        st.session_state[k] = ""
                st.session_state.recommended_products = None
                st.rerun()
        else:
            st.markdown(
                f'<div style="padding:16px 0 16px 40px;">'
                f'<span class="nav-brand">ShopSense</span></div>',
                unsafe_allow_html=True,
            )

    with col_center:
        # Mode badge only visible in session (not on home screen)
        if in_session:
            st.markdown(
                f'<div style="display:flex;align-items:center;justify-content:center;'
                f'height:52px;"><span class="nav-badge">{mode_name}</span></div>',
                unsafe_allow_html=True,
            )

    with col_user:
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:flex-end;'
            f'padding:0 40px 0 0;height:52px;gap:10px;">'
            f'<span class="nav-user-name">Priya Sharma</span>'
            f'<div style="width:28px;height:28px;border-radius:50%;background:{INK};'
            f'color:#F5F3EE;font-size:11px;font-weight:600;display:flex;align-items:center;'
            f'justify-content:center;font-family:Inter,sans-serif;">P</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(f'<div style="border-bottom:1px solid {BORDER};margin-top:-8px;"></div>',
                unsafe_allow_html=True)

    # Warning banner only shown in session, not on the clean home screen
    if in_session:
        warning = st.session_state.get("llm_warning", "")
        if warning:
            st.markdown(f'<div class="warning-bar">⚠ {warning}</div>',
                        unsafe_allow_html=True)


# ── Chat panel ────────────────────────────────────────────────────────────────
def render_chat_panel():
    st.markdown(
        f'<div class="chat-header"><div class="chat-label">AI Advisor</div></div>',
        unsafe_allow_html=True,
    )

    # ── Native Streamlit scrollable container ──────────────────────────────
    with st.container(height=520, border=False):
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(
                    f'<div class="chat-msg-user">{msg["content"]}</div>',
                    unsafe_allow_html=True,
                )
            else:
                steps = msg.get("steps", [])
                if steps:
                    label = f"Reasoning · {len(steps)} step{'s' if len(steps) != 1 else ''}"
                    with st.expander(label, expanded=False):
                        for i, step in enumerate(steps, 1):
                            if step.get("thought"):
                                st.markdown(
                                    f"<div style='font-size:11.5px;color:{INK_MID};font-family:Inter,sans-serif;'>"
                                    f"<span style='color:{INK};font-weight:600;'>Thought {i}</span><br>"
                                    f"{step['thought']}</div>",
                                    unsafe_allow_html=True,
                                )
                            if step.get("action") and step["action"] not in ("respond", ""):
                                action_str = step["action"]
                                params = step.get("action_params", {})
                                params_str = ", ".join(f"{k}={repr(v)}" for k, v in params.items()) if params else ""
                                st.markdown(
                                    f"<div style='font-size:10.5px;color:{INK_MID};margin-top:5px;"
                                    f"font-family:Inter,sans-serif;'>"
                                    f"<span style='color:{INK};font-weight:600;'>→ {action_str}</span>"
                                    f"({params_str})</div>",
                                    unsafe_allow_html=True,
                                )
                            if step.get("observation"):
                                st.markdown(
                                    f"<div style='font-size:10.5px;color:{INK_DIM};margin-top:3px;"
                                    f"font-family:Inter,sans-serif;'>{step['observation']}</div>",
                                    unsafe_allow_html=True,
                                )
                            if i < len(steps):
                                st.markdown(f"<hr style='border:none;border-top:1px solid {BORDER};margin:6px 0;'>",
                                            unsafe_allow_html=True)

                content_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', msg["content"])
                content_html = content_html.replace("\n", "<br>")
                st.markdown(
                    f'<div class="chat-msg-ai">'
                    f'<div class="ai-label">◈ Advisor</div>'
                    f'{content_html}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        if st.session_state.is_loading:
            st.markdown(
                '<div class="thinking-dots"><span></span><span></span><span></span></div>',
                unsafe_allow_html=True,
            )

    # ── Input pinned below ─────────────────────────────────────────────────
    st.markdown('<div class="input-wrap">', unsafe_allow_html=True)
    with st.form(key="chat_form", clear_on_submit=True):
        col_inp, col_send = st.columns([7, 1])
        with col_inp:
            user_input = st.text_input(
                "msg", placeholder="Describe what you're looking for…",
                label_visibility="collapsed",
            )
        with col_send:
            submitted = st.form_submit_button("→")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted and user_input.strip():
        _handle_query(user_input.strip())


# ── Product card ──────────────────────────────────────────────────────────────
def render_product_card(product, query: str = "", is_top: bool = False):
    color = get_cat_color(product.category.value)
    cat_label = CAT_LABEL.get(product.category.value, product.category.value.title())
    features = get_product_features(product)
    score = compute_match_score(product, query)
    in_solution = product.sku in st.session_state.solution_items

    rec_tag = f'<div class="rec-tag">Top match</div>' if is_top else ""

    st.markdown(f"""
<div class="product-card">
  <div class="product-card-bar" style="background:{color};"></div>
  {rec_tag}
  <div class="product-cat-label" style="color:{color};">{cat_label}</div>
  <div class="product-name">{product.name}</div>
  <div class="product-sku">{product.sku}</div>
  <div class="product-desc">{product.description}</div>
  <div class="product-price-row">
    <span class="product-price">${product.price:,.0f}</span>
    <span class="product-stock {'out' if not product.in_stock else ''}">
      {'In Stock' if product.in_stock else 'Out of Stock'}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    if product.in_stock:
        btn_label = "✓ Added" if in_solution else "Add to cart"
        if st.button(btn_label, key=f"add_{product.sku}", use_container_width=True):
            if in_solution:
                remove_from_solution(product.sku)
            else:
                add_to_solution(product)
            st.rerun()

    with st.expander("Specs", expanded=False):
        if features:
            for f in features:
                st.markdown(
                    f"<div style='font-size:11px;color:{INK_MID};font-family:Inter,sans-serif;"
                    f"margin:2px 0;'>· {f}</div>",
                    unsafe_allow_html=True,
                )
        specs = product.specifications or {}
        if specs:
            rows = "".join(
                f"<tr><td style='padding:4px 0;font-size:10.5px;color:{INK_DIM};font-family:Inter,sans-serif;'>"
                f"{k.replace('_',' ').title()}</td>"
                f"<td style='padding:4px 0;font-size:10.5px;color:{INK};text-align:right;"
                f"font-family:Inter,sans-serif;'>{v}</td></tr>"
                for k, v in list(specs.items())[:5]
            )
            st.markdown(
                f"<table style='width:100%;border-collapse:collapse;margin-top:6px;'>{rows}</table>",
                unsafe_allow_html=True,
            )


# ── Hero ──────────────────────────────────────────────────────────────────────
def render_hero():
    headline = st.session_state.hero_headline
    subtitle = st.session_state.hero_subtitle
    ctx = st.session_state.hero_context
    layout = st.session_state.get("layout_type", "grid")

    cat_icons = {"cameras": "Cameras", "video": "Video", "accessories": "Accessories",
                 "films": "Films & Media"}
    if layout == "compare":
        eyebrow = "Side-by-Side · Comparison"
    elif layout == "bundle":
        eyebrow = "Complete Solution · Bundle"
    elif ctx and ctx not in ("all", "default"):
        eyebrow = f"{CAT_LABEL.get(ctx, ctx.title())} · Recommendations"
    else:
        eyebrow = "AI-Curated · For Priya Sharma"

    st.markdown(f"""
<div class="hero-section">
  <div class="hero-eyebrow">{eyebrow}</div>
  <div class="hero-title">{headline}</div>
  <div class="hero-sub">{subtitle}</div>
</div>
""", unsafe_allow_html=True)


# ── Generative UI helpers ─────────────────────────────────────────────────────
def extract_intro_text(analysis: str) -> str:
    """Pull the intro paragraph before the first 'Option N' heading."""
    opt_m = re.search(r'(?:#{1,3}\s*|\*{2})?[Oo]ption\s+\d+', analysis)
    raw = analysis[:opt_m.start()].strip() if opt_m else analysis
    clean = re.sub(r'^#+\s*', '', raw, flags=re.MULTILINE)
    clean = re.sub(r'\*\*(.*?)\*\*', r'\1', clean)
    clean = re.sub(r'^[\U0001F000-\U0001FFFF\u2600-\u27BF\U0001F300-\U0001FAFF]\s*', '', clean, flags=re.MULTILINE)
    paras = [p.strip() for p in clean.split('\n\n') if p.strip() and len(p.strip()) > 30]
    if not paras:
        return ""
    text = paras[0].split('\n')[0].strip()
    return (text[:280] + "…") if len(text) > 280 else text


def parse_recommendation_blocks(analysis: str, products: list) -> list:
    """
    Parse the AI final_answer into a list of option dicts:
      { option_num, option_label, product, bullets, is_top }
    Falls back gracefully when no 'Option N' structure is detected.
    """
    if not products:
        return []

    # Capture the full heading line — parse label/product from it separately
    opt_pat = re.compile(
        r'^(?:\*{1,2}|#{1,4}\s*)?[Oo]ption\s+(\d+)([^\n]*)\n',
        re.MULTILINE,
    )
    matches = list(opt_pat.finditer(analysis))

    if not matches:
        # No explicit options — assign products sequentially with generic labels
        labels = ["Best Match", "Also Consider", "Budget Choice", "Premium Pick"]
        return [
            {
                "option_num": i + 1,
                "option_label": labels[i] if i < len(labels) else f"Option {i + 1}",
                "product": p,
                "bullets": [],
                "is_top": i == 0,
            }
            for i, p in enumerate(products)
        ]

    blocks: list = []
    seen_skus: set = set()

    for i, m in enumerate(matches):
        opt_num = int(m.group(1))
        heading_rest = m.group(2) or ""

        # Parse label and product hint from the heading remainder
        # e.g. " — Best Fit: ThermoMax HX3000** (SKU: COOL-003)"
        heading_clean = re.sub(r'\*+', '', heading_rest).strip()
        dash_parts = re.split(r'\s*[—–\-]+\s*', heading_clean, maxsplit=1)
        after_dash = dash_parts[1].strip() if len(dash_parts) > 1 else ""
        # Remove trailing SKU clause for hint parsing
        after_dash_no_sku = re.sub(r'\s*\(SKU[^)]*\)', '', after_dash).strip()
        colon_parts = after_dash_no_sku.split(":", 1)
        opt_label = colon_parts[0].strip() or ""
        prod_hint = colon_parts[1].strip() if len(colon_parts) > 1 else ""

        # Section text from end of heading to start of next heading (or EOF)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(analysis)
        section = analysis[start:end]

        # Extract bullet points from section
        bullets = []
        for line in section.split('\n'):
            line = line.strip()
            if line and line[0] in ('-', '•', '*', '·') and len(line) > 3:
                clean_b = re.sub(r'^[-•*·]\s*', '', line)
                clean_b = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_b).strip()
                if len(clean_b) > 10:
                    bullets.append(clean_b)

        # Match product — check heading line first for SKU, then section
        product = None
        sku_m = re.search(r'\(SKU[:\s]+([A-Z]+-\d+(?:-[A-Z]+)?)\)',
                          heading_rest + "\n" + section, re.IGNORECASE)
        if sku_m:
            sku = sku_m.group(1).upper()
            for p in products:
                if p.sku.upper() == sku and p.sku not in seen_skus:
                    product = p
                    break

        # Fall back to product name hint
        if not product and prod_hint:
            hint_lower = prod_hint.lower()
            for p in products:
                if p.sku not in seen_skus and (
                    hint_lower in p.name.lower()
                    or any(w in p.name.lower() for w in hint_lower.split() if len(w) > 4)
                ):
                    product = p
                    break

        # Fall back to index among unseen products
        if not product:
            remaining = [p for p in products if p.sku not in seen_skus]
            if remaining:
                idx = opt_num - 1
                product = remaining[idx] if idx < len(remaining) else remaining[0]

        if product:
            seen_skus.add(product.sku)
            blocks.append({
                "option_num": opt_num,
                "option_label": opt_label or ("Best Match" if i == 0 else "Also Consider"),
                "product": product,
                "bullets": bullets[:3],
                "is_top": opt_num == 1,
            })

    # Attach any remaining products as "Also Available"
    for p in products:
        if p.sku not in seen_skus:
            n = len(blocks) + 1
            blocks.append({
                "option_num": n,
                "option_label": "Also Available",
                "product": p,
                "bullets": [],
                "is_top": False,
            })
            seen_skus.add(p.sku)

    return blocks


def render_recommendation_card(block: dict, query: str = ""):
    """Render one AI recommendation as a full-width generative card."""
    product = block["product"]
    opt_num = block["option_num"]
    opt_label = block.get("option_label", "Recommendation")
    bullets = block.get("bullets", [])

    color = get_cat_color(product.category.value)
    cat_label_str = CAT_LABEL.get(product.category.value, product.category.value.title())
    features = get_product_features(product)
    in_solution = product.sku in st.session_state.solution_items

    opt_num_str = f"{opt_num:02d}"
    spec_chips = "".join(f'<span class="spec-chip">{f}</span>' for f in features)

    bullets_html = ""
    if bullets:
        bullets_html = (
            '<div class="rec-why-label">Why this fits</div>'
            + "".join(f'<div class="why-bullet">· {b}</div>' for b in bullets[:3])
        )

    stock_class = "" if product.in_stock else "rec-stock-out"
    stock_text = "In Stock" if product.in_stock else "Out of Stock"
    price_str = f"${product.price:,.0f}"

    # Build as a single compact string — avoids Markdown code-block mis-detection
    # (Markdown treats 4+ leading spaces as a code block)
    card_html = (
        f'<div class="rec-card">'
        f'<div class="rec-card-stripe" style="background:{color};"></div>'
        f'<div class="rec-card-inner">'
        f'<div class="rec-card-left">'
        f'<div class="rec-badge-row">'
        f'<span class="rec-num">{opt_num_str}</span>'
        f'<span class="rec-tag-pill">{opt_label}</span>'
        f'</div>'
        f'<div class="rec-cat-lbl" style="color:{color};">{cat_label_str}</div>'
        f'<div class="rec-prod-name">{product.name}</div>'
        f'<div class="rec-prod-sku">{product.sku}</div>'
        f'<div class="rec-spec-chips">{spec_chips}</div>'
        f'</div>'
        f'<div class="rec-card-divider"></div>'
        f'<div class="rec-card-right">'
        f'{bullets_html}'
        f'<div class="rec-price-area">'
        f'<div class="rec-price-val">{price_str}</div>'
        f'<div class="rec-stock-lbl {stock_class}">{stock_text}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)

    if product.in_stock:
        _, col_btn = st.columns([3, 1])
        with col_btn:
            lbl = "✓ In cart" if in_solution else "Add to cart"
            if st.button(lbl, key=f"rec_{product.sku}", use_container_width=True):
                if in_solution:
                    remove_from_solution(product.sku)
                else:
                    add_to_solution(product)
                st.rerun()


def _render_compare_half(block: dict):
    """Render a single product inside the compare two-column layout."""
    product = block["product"]
    opt_label = block.get("option_label", "Option")
    bullets = block.get("bullets", [])

    color = get_cat_color(product.category.value)
    cat_label_str = CAT_LABEL.get(product.category.value, product.category.value.title())
    features = get_product_features(product)
    in_solution = product.sku in st.session_state.solution_items

    spec_chips = "".join(f'<span class="spec-chip">{f}</span>' for f in features)
    bullets_html = "".join(f'<div class="why-bullet">· {b}</div>' for b in bullets[:2]) if bullets else ""
    why_hdr = (
        f'<div class="rec-why-label" style="margin-top:10px;">Why this fits</div>'
        if bullets_html else ""
    )

    price_str = f"${product.price:,.0f}"
    stk_color = "#059669" if product.in_stock else "#DC2626"
    stk_text = "In Stock" if product.in_stock else "Out of Stock"
    # Compact single-line HTML avoids Markdown code-block mis-detection
    half_html = (
        f'<div style="background:{SURFACE};border:1px solid {BORDER};border-top:3px solid {color};border-radius:4px;padding:20px;margin-bottom:4px;">'
        f'<div style="font-size:9px;font-weight:600;color:{INK_DIM};font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">{opt_label}</div>'
        f'<div style="font-size:9px;font-weight:600;color:{color};font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">{cat_label_str}</div>'
        f'<div style="font-family:EB Garamond,Georgia,serif;font-size:18px;color:{INK};line-height:1.2;margin-bottom:3px;">{product.name}</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:9px;color:{INK_DIM};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">{product.sku}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:8px;">{spec_chips}</div>'
        f'{why_hdr}{bullets_html}'
        f'<div style="border-top:1px solid {BORDER};padding-top:10px;margin-top:12px;">'
        f'<div style="font-family:EB Garamond,Georgia,serif;font-size:22px;color:{INK};">{price_str}</div>'
        f'<div style="font-size:10px;font-family:Inter,sans-serif;font-weight:600;margin-top:2px;color:{stk_color};">{stk_text}</div>'
        f'</div></div>'
    )
    st.markdown(half_html, unsafe_allow_html=True)

    if product.in_stock:
        lbl = "✓ In cart" if in_solution else "Add to cart"
        if st.button(lbl, key=f"cmp_{product.sku}", use_container_width=True):
            if in_solution:
                remove_from_solution(product.sku)
            else:
                add_to_solution(product)
            st.rerun()


def render_generative_recommendation(products, analysis: str, query: str, layout: str):
    """
    The heart of Generative UI.
    Parses the AI analysis and renders visual recommendation blocks — no raw markdown.
    """
    # ── Intro text ────────────────────────────────────────────────────────────
    intro = extract_intro_text(analysis)
    if intro:
        st.markdown(
            f'<div class="rec-intro"><div class="rec-intro-text">{intro}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Bundle layout (category-grouped) — stays as-is ───────────────────────
    if layout == "bundle":
        render_bundle_layout(products, query)
        return

    # ── Parse AI blocks ───────────────────────────────────────────────────────
    blocks = parse_recommendation_blocks(analysis, products)

    # ── Compare: two-column option cards + spec table ─────────────────────────
    if layout == "compare" and len(blocks) >= 2:
        st.markdown('<div class="rec-section-hdr">Side-by-side comparison</div>',
                    unsafe_allow_html=True)
        col_a, col_vs, col_b = st.columns([10, 1, 10])
        with col_a:
            _render_compare_half(blocks[0])
        with col_vs:
            st.markdown(
                f"<div style='display:flex;align-items:center;justify-content:center;"
                f"height:100%;padding-top:80px;font-size:12px;font-weight:600;"
                f"color:{INK_DIM};font-family:Inter,sans-serif;letter-spacing:0.08em;'>VS</div>",
                unsafe_allow_html=True,
            )
        with col_b:
            _render_compare_half(blocks[1])

        # Spec comparison table
        a, b = blocks[0]["product"], blocks[1]["product"]
        if a.specifications and b.specifications:
            all_keys = sorted(set(list(a.specifications.keys()) + list(b.specifications.keys())))
            rows_html = ""
            for k in all_keys[:6]:
                va = a.specifications.get(k, "—")
                vb = b.specifications.get(k, "—")
                rows_html += (
                    f"<tr style='border-bottom:1px solid {BORDER};'>"
                    f"<td style='padding:7px 12px;font-size:11px;color:{INK_MID};"
                    f"font-family:Inter,sans-serif;'>{k.replace('_', ' ').title()}</td>"
                    f"<td style='padding:7px 12px;font-size:11px;color:{INK};text-align:right;"
                    f"font-family:Inter,sans-serif;'>{va}</td>"
                    f"<td style='padding:7px 12px;font-size:11px;color:{INK};text-align:right;"
                    f"font-family:Inter,sans-serif;'>{vb}</td></tr>"
                )
            st.markdown(
                f"<div style='padding:0 44px 16px;'>"
                f"<div style='font-size:10px;color:{INK_DIM};text-transform:uppercase;"
                f"letter-spacing:0.12em;font-weight:600;font-family:Inter,sans-serif;"
                f"margin:16px 0 8px;'>Spec Comparison</div>"
                f"<table style='width:100%;border-collapse:collapse;background:{SURFACE};"
                f"border:1px solid {BORDER};border-radius:4px;overflow:hidden;'>"
                f"<thead><tr style='border-bottom:1px solid {BORDER_S};background:{BG};'>"
                f"<th style='padding:8px 12px;font-size:10px;color:{INK_DIM};text-align:left;"
                f"font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:0.1em;'>Spec</th>"
                f"<th style='padding:8px 12px;font-size:10px;color:{INK};text-align:right;"
                f"font-family:Inter,sans-serif;'>{a.name.split()[0]}</th>"
                f"<th style='padding:8px 12px;font-size:10px;color:{INK};text-align:right;"
                f"font-family:Inter,sans-serif;'>{b.name.split()[0]}</th>"
                f"</tr></thead><tbody>{rows_html}</tbody></table></div>",
                unsafe_allow_html=True,
            )

        # Any remaining blocks after the first two
        if len(blocks) > 2:
            st.markdown('<div class="rec-section-hdr">Also considered</div>',
                        unsafe_allow_html=True)
            for block in blocks[2:]:
                render_recommendation_card(block, query)
        return

    # ── Standard: vertical list of recommendation cards ───────────────────────
    st.markdown('<div class="rec-section-hdr">Recommendations for you</div>',
                unsafe_allow_html=True)
    for block in blocks:
        render_recommendation_card(block, query)


# ── Layouts ───────────────────────────────────────────────────────────────────
def render_grid_layout(products, query: str = ""):
    top_sku = (
        st.session_state.recommended_products[0].sku
        if st.session_state.recommended_products else None
    )
    cols_per_row = 3
    for i in range(0, len(products), cols_per_row):
        row = products[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, p in enumerate(row):
            with cols[j]:
                is_top = (p.sku == top_sku) and i == 0 and j == 0
                render_product_card(p, query=query, is_top=is_top)


def render_compare_layout(products, query: str = ""):
    if len(products) < 2:
        render_grid_layout(products, query)
        return

    a, b = products[0], products[1]
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        render_product_card(a, query=query, is_top=True)
    with col_vs:
        st.markdown(
            f"<div style='display:flex;align-items:center;justify-content:center;height:100%;"
            f"font-size:12px;font-weight:600;color:{INK_DIM};padding-top:80px;"
            f"font-family:Inter,sans-serif;letter-spacing:0.08em;'>VS</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        render_product_card(b, query=query)

    if a.specifications and b.specifications:
        all_keys = sorted(set(list(a.specifications.keys()) + list(b.specifications.keys())))
        st.markdown(
            f"<div style='margin:20px 0 8px;font-size:10px;color:{INK_DIM};"
            f"text-transform:uppercase;letter-spacing:0.12em;font-weight:600;"
            f"font-family:Inter,sans-serif;'>Spec Comparison</div>",
            unsafe_allow_html=True,
        )
        rows_html = ""
        for k in all_keys[:6]:
            va = a.specifications.get(k, "—")
            vb = b.specifications.get(k, "—")
            rows_html += (
                f"<tr style='border-bottom:1px solid {BORDER};'>"
                f"<td style='padding:7px 12px;font-size:11px;color:{INK_MID};"
                f"font-family:Inter,sans-serif;'>{k.replace('_',' ').title()}</td>"
                f"<td style='padding:7px 12px;font-size:11px;color:{INK};text-align:right;"
                f"font-family:Inter,sans-serif;'>{va}</td>"
                f"<td style='padding:7px 12px;font-size:11px;color:{INK};text-align:right;"
                f"font-family:Inter,sans-serif;'>{vb}</td>"
                f"</tr>"
            )
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;background:{SURFACE};"
            f"border:1px solid {BORDER};border-radius:4px;overflow:hidden;'>"
            f"<thead><tr style='border-bottom:1px solid {BORDER_S};background:{BG};'>"
            f"<th style='padding:8px 12px;font-size:10px;color:{INK_DIM};text-align:left;"
            f"font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:0.1em;'>Spec</th>"
            f"<th style='padding:8px 12px;font-size:10px;color:{INK};text-align:right;"
            f"font-family:Inter,sans-serif;'>{a.name.split()[0]}</th>"
            f"<th style='padding:8px 12px;font-size:10px;color:{INK};text-align:right;"
            f"font-family:Inter,sans-serif;'>{b.name.split()[0]}</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )

    if len(products) > 2:
        st.markdown(
            f"<div style='margin:20px 0 8px;font-size:10px;color:{INK_DIM};"
            f"text-transform:uppercase;letter-spacing:0.12em;font-weight:600;"
            f"font-family:Inter,sans-serif;'>Also considered</div>",
            unsafe_allow_html=True,
        )
        extra = products[2:]
        cols = st.columns(min(len(extra), 3))
        for i, p in enumerate(extra[:3]):
            with cols[i]:
                render_product_card(p, query=query)


def render_bundle_layout(products, query: str = ""):
    cat_icons = {"cameras": "📷", "video": "🎥", "accessories": "🎒", "films": "🎞"}
    by_cat: dict = {}
    for p in products:
        if p.category.value not in by_cat:
            by_cat[p.category.value] = p

    if not by_cat:
        render_grid_layout(products, query)
        return

    total = sum(p.price or 0 for p in by_cat.values())

    for cat_name, p in by_cat.items():
        color = get_cat_color(cat_name)
        icon = cat_icons.get(cat_name, "·")
        cat_label_str = CAT_LABEL.get(cat_name, cat_name.title())
        in_sol = p.sku in st.session_state.solution_items
        desc_short = p.description[:90] + ("…" if len(p.description) > 90 else "")
        stk_color = "#059669" if p.in_stock else "#DC2626"
        stk_text = "In stock" if p.in_stock else "Out of stock"

        # Two-column card: info fills left, price+action on right — one visual unit
        col_info, col_action = st.columns([5, 1])
        with col_info:
            st.markdown(
                f'<div style="background:{SURFACE};border:1px solid {BORDER};'
                f'border-left:2px solid {color};border-radius:4px;'
                f'padding:16px 20px;margin:0 0 8px 44px;">'
                f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:6px;">'
                f'<span style="font-size:13px;line-height:1;">{icon}</span>'
                f'<span style="font-size:9px;font-weight:600;color:{color};font-family:Inter,sans-serif;'
                f'text-transform:uppercase;letter-spacing:0.1em;">{cat_label_str}</span>'
                f'</div>'
                f'<div style="font-family:EB Garamond,Georgia,serif;font-size:16px;color:{INK};'
                f'margin-bottom:3px;line-height:1.25;">{p.name}</div>'
                f'<div style="font-size:11px;color:{INK_MID};font-family:Inter,sans-serif;'
                f'line-height:1.5;">{desc_short}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_action:
            st.markdown(
                f'<div style="padding:16px 4px 6px;margin-right:44px;text-align:right;">'
                f'<div style="font-family:EB Garamond,Georgia,serif;font-size:20px;color:{INK};">${p.price:,.0f}</div>'
                f'<div style="font-size:9px;font-weight:600;color:{stk_color};'
                f'font-family:Inter,sans-serif;text-transform:uppercase;letter-spacing:0.06em;margin-top:3px;">{stk_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if p.in_stock:
                lbl = "✓ Added" if in_sol else "+ Add"
                if st.button(lbl, key=f"badd_{p.sku}", use_container_width=True):
                    if in_sol:
                        remove_from_solution(p.sku)
                    else:
                        add_to_solution(p)
                    st.rerun()

    all_in = all(p.sku in st.session_state.solution_items for p in by_cat.values())
    st.markdown(f"""
<div style="background:{INK};border-radius:4px;padding:18px 22px;margin:8px 44px 4px;">
  <div style="font-family:Inter,sans-serif;font-size:10px;color:{INK_DIM};
              text-transform:uppercase;letter-spacing:0.12em;margin-bottom:4px;color:rgba(245,243,238,0.5);">Bundle Total</div>
  <div style="font-family:EB Garamond,Georgia,serif;font-size:32px;color:#F5F3EE;">${total:,.0f}</div>
  <div style="font-size:11px;color:rgba(245,243,238,0.5);font-family:Inter,sans-serif;margin-top:3px;">
    {len(by_cat)} categories · Est. 5–7 day delivery ·
    {"All items in cart" if all_in else f"{sum(1 for p in by_cat.values() if p.sku in st.session_state.solution_items)}/{len(by_cat)} added"}
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown(f'<div style="padding:4px 44px 0;">', unsafe_allow_html=True)
    if not all_in:
        if st.button("Add complete bundle →", key="add_all_bundle", use_container_width=True):
            for p in by_cat.values():
                add_to_solution(p)
            st.rerun()
    else:
        if st.button("Place order →", key="bundle_place_order", use_container_width=True):
            show_order_confirmation()
    st.markdown('</div>', unsafe_allow_html=True)


# ── Cart bar + bundle summary ─────────────────────────────────────────────────
def render_cart_bar():
    items = st.session_state.solution_items
    if not items:
        return

    total = sum(v["price"] * v["qty"] for v in items.values())
    count = sum(v["qty"] for v in items.values())
    cat_counts: dict = {}
    for item in items.values():
        c = item["category"]
        cat_counts[c] = cat_counts.get(c, 0) + item["qty"]
    cat_str = " · ".join(f"{CAT_LABEL.get(c, c.title())} ×{n}" for c, n in cat_counts.items())

    st.markdown(
        f'<div class="cart-bar">'
        f'<div><div style="font-size:9px;color:rgba(245,243,238,0.5);font-family:Inter,sans-serif;'
        f'text-transform:uppercase;letter-spacing:0.12em;margin-bottom:2px;">Your Solution</div>'
        f'<div style="font-size:12px;color:rgba(245,243,238,0.7);font-family:Inter,sans-serif;">{cat_str}</div></div>'
        f'<div class="cart-bar-total">${total:,.0f}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_clear, col_order = st.columns([1, 2])
    with col_clear:
        if st.button("Clear", key="cart_clear", use_container_width=True):
            st.session_state.solution_items = {}
            st.rerun()
    with col_order:
        if st.button("Place order →", key="cart_order", use_container_width=True):
            show_order_confirmation()


def render_solution_bundle():
    items = st.session_state.solution_items
    if not items:
        return

    total = sum(v["price"] * v["qty"] for v in items.values())
    count = sum(v["qty"] for v in items.values())

    items_html = ""
    for sku, item in items.items():
        color = get_cat_color(item["category"])
        items_html += (
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"padding:8px 0;border-bottom:1px solid {BORDER};'>"
            f"<div><div style='font-size:9px;color:{color};font-weight:600;text-transform:uppercase;"
            f"letter-spacing:0.08em;font-family:Inter,sans-serif;'>{item['category']}</div>"
            f"<div style='font-family:EB Garamond,Georgia,serif;font-size:14px;color:{INK};'>{item['name']}</div></div>"
            f"<div style='font-family:EB Garamond,Georgia,serif;font-size:14px;color:{INK};'>${item['price'] * item['qty']:,.0f}</div>"
            f"</div>"
        )

    st.markdown(f"""
<div class="bundle-card">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
    <div style="font-family:Inter,sans-serif;font-size:10px;font-weight:600;color:{INK_DIM};
                text-transform:uppercase;letter-spacing:0.12em;">Solution Bundle</div>
    <div style="font-size:10px;color:{INK_DIM};font-family:Inter,sans-serif;">{count} item{'s' if count != 1 else ''}</div>
  </div>
  {items_html}
  <div style="display:flex;align-items:center;justify-content:space-between;margin-top:10px;">
    <div style="font-family:Inter,sans-serif;font-size:11px;color:{INK_MID};">Total</div>
    <div style="font-family:EB Garamond,Georgia,serif;font-size:20px;color:{INK};">${total:,.0f}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Place order →", key="bundle_order_btn", use_container_width=True):
            show_order_confirmation()
    with c2:
        if st.button("Clear", key="bundle_clear", use_container_width=True):
            st.session_state.solution_items = {}
            st.rerun()


# ── Product panel ─────────────────────────────────────────────────────────────
def render_product_panel():
    render_hero()

    if st.session_state.is_loading:
        st.markdown(f"""
<div class="loading-overlay">
  <div style="font-size:28px;animation:spin-slow 3s linear infinite;">◈</div>
  <div class="loading-text">Building your recommendation…</div>
  <div class="loading-steps">Searching catalog · Analysing requirements · Ranking matches</div>
</div>
""", unsafe_allow_html=True)
        return

    products = st.session_state.recommended_products
    if products is None:
        return  # Initial state — hero handles empty state

    analysis = st.session_state.get("ai_analysis", "")
    query = next(
        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), ""
    )
    layout = st.session_state.get("layout_type", "grid")

    if not products:
        st.markdown(
            f"<div style='padding:40px 44px;text-align:center;color:{INK_DIM};"
            f"font-family:EB Garamond,Georgia,serif;font-style:italic;font-size:16px;'>"
            f"No products matched your requirements.</div>",
            unsafe_allow_html=True,
        )
        return

    render_generative_recommendation(products, analysis, query, layout)
    render_cart_bar()
    render_solution_bundle()


# ── Initial hero (before first query) ────────────────────────────────────────
def render_initial_hero():
    st.markdown(f"""
<div class="initial-hero">
  <div class="initial-eyebrow">ShopSense AI · Consumer Electronics</div>
  <div class="initial-title">The smarter way<br>to shop electronics.</div>
  <div class="initial-sub">
    Describe what you're looking for — from cameras to accessories —
    and get AI-curated recommendations in seconds.
  </div>
</div>
""", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        with st.form(key="initial_form", clear_on_submit=True):
            query = st.text_input(
                "query",
                placeholder="e.g. Best DSLR camera for a beginner…",
                label_visibility="collapsed",
            )
            submitted = st.form_submit_button("Find products →", use_container_width=True)
            if submitted and query.strip():
                st.session_state.show_chat = True
                _handle_query(query.strip())

        quick_queries = [
            "Best mirrorless under $1,000",
            "Action cameras",
            "Compare Canon vs Sony",
            "Starter kit for beginners",
            "Full studio bundle",
        ]
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-top:16px;">',
            unsafe_allow_html=True,
        )
        cols = st.columns(len(quick_queries))
        for i, q in enumerate(quick_queries):
            with cols[i]:
                if st.button(q, key=f"pill_{i}", use_container_width=True):
                    st.session_state.show_chat = True
                    _handle_query(q)
        st.markdown('</div>', unsafe_allow_html=True)


# ── Query handlers ────────────────────────────────────────────────────────────
def _handle_query(query: str):
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.is_loading = True
    st.rerun()


def run_agent(query: str):
    solution = SolutionCart()
    for sku, item in st.session_state.solution_items.items():
        solution.add_item(sku, item["qty"])

    agent = ReActAgent(catalog, solution)
    result = agent.run(query, history=st.session_state.messages)

    st.session_state.llm_warning = result.llm_error if result.llm_error else ""

    if result.products:
        st.session_state.recommended_products = result.products

    st.session_state.hero_headline = result.hero_headline
    st.session_state.hero_subtitle = result.hero_subtitle
    st.session_state.hero_context = result.category_context
    st.session_state.layout_type = result.layout_type
    st.session_state.mode_used = result.mode_used

    # Store full analysis for right panel blocks
    st.session_state.ai_analysis = result.final_answer

    # Build insight chips from products
    st.session_state.analysis_chips = _build_chips(result.products or [], query)

    # Set category tab to match context
    if result.category_context != "all":
        st.session_state["cat_tabs"] = result.category_context

    return result


# ── Main ──────────────────────────────────────────────────────────────────────
_in_session = st.session_state.get("show_chat", False)
inject_css(in_session=_in_session)
render_nav()

if st.session_state.is_loading:
    query = next(
        (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
        "",
    )
    if query:
        result = run_agent(query)
        steps_dicts = [s.to_dict() for s in result.steps]
        # Short chat reply; full analysis on right panel
        short_reply = _short_chat_reply(result.final_answer, len(result.products or []))
        st.session_state.messages.append({
            "role": "assistant",
            "content": short_reply,
            "steps": steps_dicts,
        })
    st.session_state.is_loading = False
    st.session_state.show_chat = True
    st.rerun()

if not st.session_state.show_chat:
    render_initial_hero()
else:
    left_col, right_col = st.columns([4, 7])
    with left_col:
        render_chat_panel()
    with right_col:
        render_product_panel()
