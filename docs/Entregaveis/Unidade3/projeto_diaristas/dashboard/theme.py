"""Tema visual moderno — paleta e CSS inspirados no protótipo HTML/CSS de alta fidelidade."""

from __future__ import annotations

import streamlit as st

# Paleta principal — alinhada ao protótipo PrototipoPI1/styles.css
PALETTE = {
    "bg": "#f0f4f8",
    "surface": "#ffffff",
    "sidebar": "#0f1d2e",
    "sidebar_soft": "#16284a",
    "primary": "#1a5fa8",
    "primary_dark": "#1a3c6e",
    "accent_green": "#22a05b",
    "accent_amber": "#f5a623",
    "accent_red": "#e0186b",
    "text": "#0d1f36",
    "text_soft": "#5a738a",
    "text_faint": "#8ea8bf",
    "border": "#dde6ef",
    "sidebar_text": "#cbd8e4",
    "sidebar_muted": "#9db8cc",
}

# Sequência de cores para gráficos — paleta monocromática azul do protótipo
CHART_SEQUENCE = ["#1a5fa8", "#b8cee8", "#dce8f5", "#1a3c6e", "#8ea8bf", "#5a738a"]

CHART_FONT = dict(family="Inter, sans-serif", size=12, color=PALETTE["text"])


def inject_theme() -> None:
    """Injeta o CSS global do dashboard."""
    p = PALETTE
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            html, body, [class*="css"], .stApp, button, input, textarea {{
                font-family: "Inter", sans-serif !important;
            }}
            .stApp {{ background: {p["bg"]}; }}

            /* esconde menu/rodapé padrão do Streamlit */
            #MainMenu, footer {{ visibility: hidden; }}
            .block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }}

            /* ---- Texto de alto contraste no conteúdo ---- */
            [data-testid="stAppViewContainer"] h1,
            [data-testid="stAppViewContainer"] h2,
            [data-testid="stAppViewContainer"] h3,
            [data-testid="stAppViewContainer"] h4,
            [data-testid="stAppViewContainer"] p,
            [data-testid="stAppViewContainer"] li,
            [data-testid="stAppViewContainer"] span,
            [data-testid="stAppViewContainer"] label {{
                color: {p["text"]};
            }}
            [data-testid="stAppViewContainer"] .stCaption,
            [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {{
                color: {p["text_soft"]} !important;
            }}

            /* ---- Sidebar escura ---- */
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, {p["sidebar"]} 0%, #0b1526 100%) !important;
                border-right: 1px solid rgba(255,255,255,0.06);
            }}
            [data-testid="stSidebar"] * {{ color: {p["sidebar_text"]}; }}
            [data-testid="stSidebar"] .stCaption {{ color: {p["sidebar_muted"]} !important; }}
            [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ color: {p["sidebar_text"]} !important; }}
            [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.08); }}
            [data-testid="stSidebar"] a {{ color: {p["sidebar_text"]} !important; text-decoration: none; }}

            /* esconde navegação automática duplicada do Streamlit */
            [data-testid="stSidebarNav"] {{ display: none; }}

            /* links de navegação custom (page_link) como itens de menu */
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
                background: transparent !important;
                border-radius: 8px; padding: .5rem .7rem !important; margin: .1rem 0;
                border-left: 3px solid transparent;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] *,
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p {{
                color: {p["sidebar_muted"]} !important;
                font-weight: 400 !important; font-size: 13px !important;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
                background: rgba(255,255,255,0.06) !important;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover *,
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover p {{
                color: #fff !important;
            }}
            /* link ativo */
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {{
                background: {p["primary"]} !important;
                border-left-color: {p["primary"]} !important;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] *,
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] p {{
                color: #fff !important;
                font-weight: 600 !important;
            }}

            .brand {{
                display: flex; align-items: center; gap: .6rem;
                padding: .2rem 0 1.2rem 0;
                border-bottom: 1px solid rgba(255,255,255,0.08);
                margin-bottom: .6rem;
            }}
            .brand-logo {{
                width: 36px; height: 36px; border-radius: 10px;
                background: {p["primary"]};
                display: flex; align-items: center; justify-content: center;
                font-weight: 800; color: #fff; font-size: .95rem;
            }}
            .brand-name {{ font-weight: 700; font-size: 13px; line-height: 1.1; color: #fff; }}
            .brand-sub {{ font-size: 11px; color: {p["sidebar_muted"]}; }}
            .side-section {{
                font-size: 10px; letter-spacing: .10em; text-transform: uppercase;
                color: {p["sidebar_muted"]}; margin: 1rem 0 .4rem 0; font-weight: 600;
            }}
            .side-author {{ font-size: .82rem; color: {p["sidebar_muted"]}; line-height: 1.5; }}

            /* ---- Cabeçalho da página ---- */
            .page-head {{ margin-bottom: 1.2rem; }}
            .page-head h1 {{
                font-size: 28px; font-weight: 800; margin: 0; color: {p["text"]};
                line-height: 1.2;
            }}
            .page-head .page-category {{
                font-size: 11px; text-transform: uppercase; letter-spacing: .12em;
                color: {p["primary"]}; font-weight: 600; margin: 0 0 4px 0;
            }}
            .page-head p {{ color: {p["text_soft"]}; margin: .2rem 0 0 0; font-size: .92rem; }}

            /* ---- Cartões nativos (st.container border) ---- */
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background: {p["surface"]};
                border: 1px solid {p["border"]} !important;
                border-radius: 14px !important;
                box-shadow: 0 2px 12px rgba(10, 40, 80, .08);
                padding: 0 !important;
            }}
            [data-testid="stVerticalBlockBorderWrapper"] > div {{
                padding: 22px 24px;
            }}

            /* ---- KPI ---- */
            .kpi-card-wrapper {{
                border-top: 3px solid {p["primary"]} !important;
            }}
            .kpi-label {{
                font-size: 12px; font-weight: 600; letter-spacing: .04em;
                text-transform: uppercase; color: {p["text_soft"]}; margin: 0;
                line-height: 1.4;
            }}
            .kpi-value {{
                font-size: 30px; font-weight: 800; color: {p["primary"]};
                margin: 4px 0 0 0; line-height: 1;
            }}
            .kpi-delta {{ font-size: .78rem; font-weight: 600; margin-top: .25rem; }}
            .kpi-delta.up {{ color: {p["accent_green"]}; }}
            .kpi-delta.flat {{ color: {p["text_faint"]}; }}

            /* ---- Títulos de cartão ---- */
            .card-eyebrow {{
                font-size: 10px; font-weight: 700; letter-spacing: .12em;
                text-transform: uppercase; color: {p["primary"]}; margin: 0 0 .1rem 0;
            }}
            .card-title {{ font-size: 17px; font-weight: 700; color: {p["text"]}; margin: 0 0 .2rem 0; }}
            .card-note {{ font-size: .82rem; color: {p["text_soft"]}; margin: .4rem 0 0 0; }}

            /* ---- Lista (top itens) ---- */
            .rank-row {{
                display:flex; align-items:center; justify-content:space-between;
                padding:.55rem 0; border-bottom:1px solid {p["border"]};
            }}
            .rank-row:last-child {{ border-bottom:none; }}
            .rank-left {{ display:flex; align-items:center; gap:.6rem; }}
            .rank-badge {{
                width:30px; height:30px; border-radius:8px; flex:none;
                display:flex; align-items:center; justify-content:center;
                font-weight:700; font-size:.8rem; color:#fff; background:{p["primary"]};
            }}
            .rank-name {{ font-weight:600; font-size:.9rem; color:{p["text"]}; }}
            .rank-sub {{ font-size:.76rem; color:{p["text_faint"]}; }}
            .rank-value {{ font-weight:700; color:{p["primary_dark"]}; font-size:.95rem; }}

            /* ---- Tags (preocupações) — estilo texto bold como no protótipo ---- */
            .concerns-list {{
                display: flex; flex-wrap: wrap; gap: 10px;
                padding: 8px 0; list-style: none; margin: 0;
            }}
            .concern {{
                font-weight: 800; color: {p["primary_dark"]}; letter-spacing: .03em;
            }}
            .concern.accent {{ color: {p["text_faint"]}; }}
            .concern.xl {{ font-size: 22px; }}
            .concern.lg {{ font-size: 17px; }}
            .concern.md {{ font-size: 14px; }}
            .concern.sm {{ font-size: 12px; }}

            /* ---- Abas pílula ---- */
            .stTabs [data-baseweb="tab-list"] {{
                gap:.35rem; background:{p["surface"]}; border:1px solid {p["border"]};
                border-radius:12px; padding:.35rem; margin-bottom:1.1rem;
            }}
            .stTabs [data-baseweb="tab"] {{
                color:{p["text_soft"]} !important; font-weight:600; font-size:.88rem;
                border-radius:8px; padding:.5rem 1.1rem;
                transition: background .15s, color .15s;
            }}
            .stTabs [aria-selected="true"] {{ background:{p["primary"]} !important; color:#fff !important; }}

            /* Pills / Segmented Control active text color */
            [data-testid="stSegmentedControl"] button[aria-checked="true"] p,
            [data-testid="stSegmentedControl"] button[aria-checked="true"] div,
            [data-testid="stSegmentedControl"] button[aria-checked="true"] span,
            [data-testid="stPills"] button[aria-checked="true"] p,
            [data-testid="stPills"] button[aria-checked="true"] div,
            [data-testid="stPills"] button[aria-checked="true"] span {{
                color: #ffffff !important;
            }}

            /* métricas nativas */
            [data-testid="stMetricValue"] {{ color:{p["primary"]} !important; font-weight:800 !important; }}
            [data-testid="stMetricLabel"] p {{ color:{p["text_soft"]} !important; }}

            /* botões */
            [data-testid="stSidebar"] .stButton button {{
                background:{p["primary"]}; color:#fff; border:none; border-radius:8px;
                font-weight:600; font-size:12px; padding:9px 14px;
                transition: background .15s;
            }}
            [data-testid="stSidebar"] .stButton button:hover {{ background:{p["primary_dark"]}; color:#fff; }}

            .footer-note {{
                margin-top:1.5rem; padding:1.1rem 1.3rem; background:{p["sidebar"]};
                border:1px solid rgba(255,255,255,0.06); border-radius:14px;
                color:{p["sidebar_muted"]}; font-size:.82rem; line-height:1.6;
            }}
            .footer-note * {{ color: {p["sidebar_muted"]}; }}
            .footer-note a {{ color:{p["sidebar_muted"]}; font-weight:600; text-decoration:none; }}
            .footer-note a:hover {{ color: #fff; }}
            .footer-note strong {{ color:{p["sidebar_text"]}; }}

            /* ---- Expander (Ver dados) ---- */
            [data-testid="stExpander"] {{
                border-color: {p["border"]} !important;
                border-radius: 8px !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-head"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
