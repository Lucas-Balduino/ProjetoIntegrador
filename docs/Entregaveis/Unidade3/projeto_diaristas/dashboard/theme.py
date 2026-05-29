"""Tema visual moderno — paleta e CSS inspirados em dashboards analíticos."""

from __future__ import annotations

import streamlit as st

# Paleta principal
PALETTE = {
    "bg": "#eef2f7",
    "surface": "#ffffff",
    "sidebar": "#0f1e35",
    "sidebar_soft": "#16284a",
    "primary": "#2f6df6",
    "primary_dark": "#1d4ed8",
    "accent_green": "#22c55e",
    "accent_amber": "#f5a623",
    "accent_red": "#ef4444",
    "text": "#0f1b2d",
    "text_soft": "#5b6b80",
    "text_faint": "#8a98ab",
    "border": "#e3e9f2",
    "sidebar_text": "#e8eef7",
    "sidebar_muted": "#8ea3c4",
}

# Sequência de cores para gráficos (verde/azul/âmbar como na referência)
CHART_SEQUENCE = ["#2f6df6", "#22c55e", "#f5a623", "#8b5cf6", "#0ea5e9", "#ef4444"]

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
            [data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,0.10); }}
            [data-testid="stSidebar"] a {{ color: {p["sidebar_text"]} !important; text-decoration: none; }}

            /* esconde navegação automática duplicada do Streamlit */
            [data-testid="stSidebarNav"] {{ display: none; }}

            /* links de navegação custom (page_link) como itens de menu */
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
                background: transparent !important;
                border-radius: 9px; padding: .5rem .7rem !important; margin: .1rem 0;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] *,
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p {{
                color: {p["sidebar_text"]} !important;
                font-weight: 600 !important; font-size: .9rem !important;
            }}
            [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
                background: rgba(255,255,255,0.08) !important;
            }}

            .brand {{
                display: flex; align-items: center; gap: .6rem;
                padding: .2rem 0 1rem 0;
            }}
            .brand-logo {{
                width: 38px; height: 38px; border-radius: 10px;
                background: linear-gradient(135deg, {p["primary"]}, {p["accent_green"]});
                display: flex; align-items: center; justify-content: center;
                font-weight: 800; color: #fff; font-size: 1rem;
            }}
            .brand-name {{ font-weight: 700; font-size: 1rem; line-height: 1.1; }}
            .brand-sub {{ font-size: .72rem; color: {p["sidebar_muted"]}; }}
            .side-section {{
                font-size: .7rem; letter-spacing: .09em; text-transform: uppercase;
                color: {p["sidebar_muted"]}; margin: 1rem 0 .4rem 0; font-weight: 600;
            }}
            .side-author {{ font-size: .82rem; color: {p["sidebar_muted"]}; line-height: 1.5; }}

            /* ---- Cabeçalho da página ---- */
            .page-head {{ margin-bottom: 1.2rem; }}
            .page-head h1 {{
                font-size: 1.6rem; font-weight: 800; margin: 0; color: {p["text"]};
            }}
            .page-head p {{ color: {p["text_soft"]}; margin: .2rem 0 0 0; font-size: .92rem; }}

            /* ---- Cartões nativos (st.container border) ---- */
            [data-testid="stVerticalBlockBorderWrapper"] {{
                background: {p["surface"]};
                border: 1px solid {p["border"]} !important;
                border-radius: 16px !important;
                box-shadow: 0 1px 2px rgba(16,27,45,.04), 0 8px 24px rgba(16,27,45,.05);
            }}

            /* ---- KPI ---- */
            .kpi-label {{
                font-size: .74rem; font-weight: 600; letter-spacing: .04em;
                text-transform: uppercase; color: {p["text_faint"]}; margin: 0;
            }}
            .kpi-value {{
                font-size: 2.1rem; font-weight: 800; color: {p["text"]};
                margin: .15rem 0 0 0; line-height: 1.1;
            }}
            .kpi-delta {{ font-size: .78rem; font-weight: 600; margin-top: .25rem; }}
            .kpi-delta.up {{ color: {p["accent_green"]}; }}
            .kpi-delta.flat {{ color: {p["text_faint"]}; }}

            /* ---- Títulos de cartão ---- */
            .card-eyebrow {{
                font-size: .68rem; font-weight: 700; letter-spacing: .08em;
                text-transform: uppercase; color: {p["primary"]}; margin: 0 0 .1rem 0;
            }}
            .card-title {{ font-size: 1.05rem; font-weight: 700; color: {p["text"]}; margin: 0 0 .2rem 0; }}
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

            /* ---- Tags (preocupações) ---- */
            .tag {{
                display:inline-block; padding:.4rem .85rem; margin:.22rem;
                border-radius:999px; background:#eaf0fe; color:{p["primary_dark"]}; font-weight:600;
            }}
            .tag.xl {{ font-size:1.25rem; }} .tag.lg {{ font-size:1.05rem; }}
            .tag.md {{ font-size:.92rem; }}  .tag.sm {{ font-size:.8rem; opacity:.85; }}

            /* ---- Abas pílula ---- */
            .stTabs [data-baseweb="tab-list"] {{
                gap:.35rem; background:{p["surface"]}; border:1px solid {p["border"]};
                border-radius:12px; padding:.35rem; margin-bottom:1.1rem;
            }}
            .stTabs [data-baseweb="tab"] {{
                color:{p["text_soft"]} !important; font-weight:600; font-size:.88rem;
                border-radius:9px; padding:.5rem 1.1rem;
            }}
            .stTabs [aria-selected="true"] {{ background:{p["primary"]} !important; color:#fff !important; }}

            /* métricas nativas */
            [data-testid="stMetricValue"] {{ color:{p["primary_dark"]} !important; font-weight:800 !important; }}
            [data-testid="stMetricLabel"] p {{ color:{p["text_soft"]} !important; }}

            /* botões */
            [data-testid="stSidebar"] .stButton button {{
                background:{p["primary"]}; color:#fff; border:none; border-radius:10px; font-weight:600;
            }}
            [data-testid="stSidebar"] .stButton button:hover {{ background:{p["primary_dark"]}; color:#fff; }}

            .footer-note {{
                margin-top:1.5rem; padding:1.1rem 1.3rem; background:{p["surface"]};
                border:1px solid {p["border"]}; border-radius:14px;
                color:{p["text_soft"]}; font-size:.82rem; line-height:1.6;
            }}
            .footer-note a {{ color:{p["primary"]}; font-weight:600; text-decoration:none; }}
            .footer-note strong {{ color:{p["text"]}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-head"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
