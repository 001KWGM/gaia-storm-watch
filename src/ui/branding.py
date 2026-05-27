GAIA_DARK = "#2D3A4C"
GAIA_GREY = "#606A72"
GAIA_LIGHT_GREY = "#ABB9BD"
GAIA_BG = "#DBE5E5"
GAIA_GOLD = "#E4C21C"
GAIA_WHITE = "#F7FAFA"
GAIA_PANEL = "#FFFFFF"


def css() -> str:
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Montserrat:wght@600;700;800&display=swap');
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stApp {{
        background:
            radial-gradient(circle at 10% -10%, rgba(228,194,28,0.20), rgba(228,194,28,0.00) 28rem),
            linear-gradient(180deg, {GAIA_BG} 0%, #F7FAFA 58%, #FFFFFF 100%);
        color: {GAIA_DARK};
        font-family: Inter, Arial, sans-serif;
    }}
    .block-container {{ padding-top: 1.5rem; max-width: 1360px; }}
    h1, h2, h3, h4 {{ color: {GAIA_DARK}; letter-spacing: -0.025em; font-family: Montserrat, Inter, Arial, sans-serif; }}
    h1 {{ font-size: 3.1rem; line-height: 1.02; }}
    h2 {{ margin-top: 1.35rem; }}
    .gaia-hero {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, {GAIA_DARK} 0%, #1F2B39 70%);
        color: white;
        padding: 2.0rem 2.2rem;
        border-radius: 28px;
        border: 1px solid rgba(255,255,255,0.12);
        box-shadow: 0 16px 36px rgba(45,58,76,0.22);
        margin-bottom: 1.0rem;
    }}
    .gaia-hero:after {{
        content: "";
        position:absolute;
        right:-7rem;
        top:-7rem;
        width:18rem;
        height:18rem;
        background: rgba(228,194,28,0.20);
        border-radius:50%;
    }}
    .gaia-hero h1 {{ color: white; margin: 0 0 0.3rem 0; max-width: 900px; }}
    .gaia-hero p {{ color: #E7EEEE; font-size: 1.05rem; max-width: 900px; }}
    .gaia-hero .tags span {{
        display:inline-block;
        margin:0.35rem 0.35rem 0 0;
        padding:0.28rem 0.58rem;
        border-radius:999px;
        border:1px solid rgba(255,255,255,0.18);
        background:rgba(255,255,255,0.08);
        color:#F8FBFB;
        font-size:0.78rem;
        text-transform:uppercase;
        letter-spacing:0.06em;
    }}
    .gaia-card {{
        background: rgba(255,255,255,0.86);
        padding: 1.0rem;
        border-radius: 22px;
        border: 1px solid rgba(45,58,76,0.12);
        box-shadow: 0 10px 28px rgba(45,58,76,0.08);
    }}
    .gaia-card h3 {{ margin-top: 0; }}
    .gaia-small {{ color: {GAIA_GREY}; font-size: 0.88rem; }}
    .gaia-warning {{
        background: #FFF8D6;
        border-left: 6px solid {GAIA_GOLD};
        border-radius: 16px;
        padding: 0.95rem 1.05rem;
        color: {GAIA_DARK};
        margin: 0.9rem 0 1.05rem 0;
        box-shadow: 0 8px 20px rgba(45,58,76,0.06);
    }}
    .gaia-legal {{
        background: rgba(255,255,255,0.70);
        border: 1px solid rgba(45,58,76,0.12);
        border-radius: 18px;
        padding: 1.0rem 1.1rem;
        color: {GAIA_GREY};
        font-size: 0.92rem;
    }}
    .metric-label {{ color: {GAIA_GREY}; font-size: 0.80rem; text-transform: uppercase; letter-spacing: 0.065em; }}
    .metric-value {{ color: {GAIA_DARK}; font-weight: 800; font-size: 1.72rem; }}
    div[data-testid="stMetric"] {{ background: rgba(255,255,255,0.80); border: 1px solid rgba(45,58,76,0.1); border-radius: 18px; padding: 0.8rem; }}
    .stButton>button, .stDownloadButton>button {{ background: {GAIA_GOLD}; color: {GAIA_DARK}; font-weight: 800; border: 0; border-radius: 14px; }}
    .story-panel {{
        background: rgba(45,58,76,0.97);
        color: white;
        padding: 1.18rem 1.25rem;
        border-radius: 22px;
        border-bottom: 5px solid {GAIA_GOLD};
        margin: 0.7rem 0 1.05rem 0;
    }}
    .story-panel h3 {{ color: white; margin-top: 0; }}
    .story-panel p {{ color: #E7EEEE; }}
    .caption-box {{
        color: {GAIA_GREY};
        font-size: 0.84rem;
        line-height: 1.35;
        padding: 0.5rem 0.65rem;
        margin: 0.25rem 0 1rem 0;
        border-left: 4px solid {GAIA_GOLD};
        background: rgba(255,255,255,0.62);
        border-radius: 0 12px 12px 0;
    }}
    .cam-card {{ min-height: 230px; margin-bottom: 0.65rem; }}
    .source-pill {{ display:inline-block; padding:0.22rem 0.55rem; border-radius:999px; background:#EEF3F3; margin:0.12rem; color:{GAIA_DARK}; font-size:0.82rem; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 0.3rem; }}
    .stTabs [data-baseweb="tab"] {{ background: rgba(255,255,255,0.55); border-radius: 999px; padding: 0.45rem 0.85rem; }}
    .stTabs [aria-selected="true"] {{ background: {GAIA_DARK}; color: white; }}
    </style>
    """
