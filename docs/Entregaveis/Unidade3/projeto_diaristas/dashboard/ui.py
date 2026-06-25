"""Componentes de interface reutilizáveis do dashboard."""

from __future__ import annotations

import re
from itertools import count
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_KEY_SEQ = count()

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


def _slug(*parts: str) -> str:
    raw = "_".join(str(p) for p in parts if p)
    return re.sub(r"[^\w]+", "_", raw.lower()).strip("_")[:80]


def chart_key(*parts: str) -> str:
    """Chave única e estável-por-render para widgets de gráfico."""
    return f"{_slug(*parts)}_{next(_KEY_SEQ)}"


# --------------------------------------------------------------------------- #
# KPI
# --------------------------------------------------------------------------- #
def kpi_row(items: list[tuple[str, str, str]]) -> None:
    """items: lista de (valor, rótulo, dica)."""
    cols = st.columns(len(items))
    for col, (value, label, hint) in zip(cols, items):
        with col:
            with st.container(border=True):
                # O CSS injetado procura pelo .kpi-label para colorir o top-border do container
                st.markdown(
                    """
                    <style>
                    div[data-testid="stVerticalBlockBorderWrapper"]:has(.kpi-label) {
                        border-top: 3px solid #1a5fa8 !important;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(f'<p class="kpi-label">{label}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="kpi-value">{value}</p>', unsafe_allow_html=True)
                st.markdown(f'<p class="kpi-delta flat">{hint}</p>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Cartão com gráfico
# --------------------------------------------------------------------------- #
def chart_card(
    eyebrow: str,
    title: str,
    fig: go.Figure,
    note: str = "",
    table: pd.DataFrame | None = None,
) -> None:
    key = chart_key(eyebrow, title)
    with st.container(border=True):
        if eyebrow:
            st.markdown(f'<p class="card-eyebrow">{eyebrow}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="card-title">{title}</p>', unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch", config=PLOTLY_CONFIG, key=key)
        if note:
            st.markdown(f'<p class="card-note">{note}</p>', unsafe_allow_html=True)
        if table is not None and not table.empty:
            with st.expander("Ver dados"):
                st.dataframe(table, hide_index=True, width="stretch", key=f"tbl_{key}")


# --------------------------------------------------------------------------- #
# Lista ranqueada
# --------------------------------------------------------------------------- #
def rank_card(eyebrow: str, title: str, rows: Iterable[tuple[str, str, str]]) -> None:
    """rows: (rank/sigla, nome, valor)."""
    with st.container(border=True):
        st.markdown(f'<p class="card-eyebrow">{eyebrow}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="card-title">{title}</p>', unsafe_allow_html=True)
        html = ['<div>']
        for badge, name, value in rows:
            html.append(
                f'<div class="rank-row"><div class="rank-left">'
                f'<div class="rank-badge">{badge}</div>'
                f'<div class="rank-name">{name}</div></div>'
                f'<div class="rank-value">{value}</div></div>'
            )
        html.append("</div>")
        st.markdown("".join(html), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Nuvem de tags
# --------------------------------------------------------------------------- #
def tag_card(eyebrow: str, title: str, tags: list[tuple[str, str]], note: str = "") -> None:
    with st.container(border=True):
        st.markdown(f'<p class="card-eyebrow">{eyebrow}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="card-title">{title}</p>', unsafe_allow_html=True)
        chips = "".join(f'<li class="concern {size}">{label}</li>' for label, size in tags)
        st.markdown(f'<ul class="concerns-list">{chips}</ul>', unsafe_allow_html=True)
        if note:
            st.markdown(f'<p class="card-note">{note}</p>', unsafe_allow_html=True)


def empty_card(message: str) -> None:
    with st.container(border=True):
        st.info(message)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #


def render_sidebar() -> None:
    """Renderiza branding e navegação."""
    st.sidebar.markdown(
        '<div class="brand">'
        '<div class="brand-logo">PI</div>'
        '<div><div class="brand-name">Projeto Integrador I</div>'
        '<div class="brand-sub">Trabalho Doméstico Informal</div></div>'
        "</div>",
        unsafe_allow_html=True,
    )
    for target, label in [
        ("app.py", "Visão geral"),
        ("pages/2_Sobre.py", "Sobre"),
        ("pages/3_Fontes.py", "Fontes"),
        ("pages/4_Equipe.py", "Equipe"),
    ]:
        try:
            st.sidebar.page_link(target, label=label)
        except Exception:
            pass


def footer(source: str) -> None:
    label = {"local": "dados ETL locais", "snapshot": "snapshot versionado", "missing": "sem dados"}.get(
        source, source
    )
    st.markdown(
        '<div class="footer-note">'
        "<strong>Projeto Integrador I — UniCEUB.</strong> Análise da problemática do "
        "trabalho doméstico informal (ODS 8), cruzando PNAD Contínua (IBGE SIDRA) com "
        f"pesquisa de campo em Brasília, 2026. Fonte de dados: {label}.<br>"
        '<a href="https://sidra.ibge.gov.br/pesquisa/pnadct/tabelas" target="_blank">IBGE SIDRA</a> &middot; '
        '<a href="https://github.com/Lucas-Balduino/ProjetoIntegrador" target="_blank">Repositório do Projeto</a>'
        "</div>",
        unsafe_allow_html=True,
    )
