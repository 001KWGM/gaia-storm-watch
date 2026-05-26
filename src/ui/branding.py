GAIA_DARK = "#2D3A4C"
GAIA_GREY = "#606A72"
GAIA_LIGHT_GREY = "#ABB9BD"
GAIA_BG = "#DBE5E5"
GAIA_GOLD = "#E4C21C"
GAIA_WHITE = "#F7FAFA"


def css() -> str:
    return f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stApp {{ background: linear-gradient(180deg, {GAIA_BG} 0%, #F7FAFA 55%); }}
    h1, h2, h3 {{ color: {GAIA_DARK}; letter-spacing: -0.02em; }}
    .block-container {{ padding-top: 2rem; max-width: 1320px; }}
    .gaia-hero {{
        background: {GAIA_DARK}; color: white; padding: 1.4rem 1.6rem; border-radius: 20px;
        border-left: 8px solid {GAIA_GOLD}; margin-bottom: 1rem;
    }}
    .gaia-hero h1 {{ color: white; margin-bottom: 0.1rem; }}
    .gaia-hero p {{ color: #E7EEEE; font-size: 1.03rem; }}
    .gaia-card {{
        background: rgba(255,255,255,0.82); padding: 1rem; border-radius: 18px;
        border: 1px solid rgba(45,58,76,0.12); box-shadow: 0 6px 18px rgba(45,58,76,0.07);
    }}
    .gaia-small {{ color: {GAIA_GREY}; font-size: 0.88rem; }}
    .gaia-warning {{
        background: #FFF8D6; border-left: 6px solid {GAIA_GOLD}; border-radius: 12px;
        padding: 0.9rem 1rem; color: {GAIA_DARK}; margin: 0.8rem 0 1rem 0;
    }}
    .metric-label {{ color: {GAIA_GREY}; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; }}
    .metric-value {{ color: {GAIA_DARK}; font-weight: 700; font-size: 1.6rem; }}
    div[data-testid="stMetric"] {{ background: rgba(255,255,255,0.78); border: 1px solid rgba(45,58,76,0.1); border-radius: 16px; padding: 0.8rem; }}
    .stButton>button {{ background: {GAIA_GOLD}; color: {GAIA_DARK}; font-weight: 700; border: 0; border-radius: 12px; }}
    </style>
    """
