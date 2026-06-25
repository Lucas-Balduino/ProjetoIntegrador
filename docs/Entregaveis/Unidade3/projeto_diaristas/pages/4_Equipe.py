"""Página Equipe — Membros do PI 1."""

import streamlit as st

from dashboard import theme, ui

st.set_page_config(page_title="Equipe | Trabalho Doméstico Informal", layout="wide")
theme.inject_theme()
ui.render_sidebar()

theme.page_header(
    "Equipe do Projeto",
    "Conheça os desenvolvedores e pesquisadores envolvidos",
)

equipe = [
    ("Lucas Gonçalves", "Product Owner", "https://github.com/Lucas-Balduino"),
    ("João Victor Rios", "Desenvolvedor Full-stack", "https://github.com/Jvriosbrito"),
    ("Alexsander Motta", "Analista de BI", "https://github.com/APKOY"),
    ("Beatriz Vasconcellos", "Pesquisadora UX", "https://github.com/beatrizve16"),
    ("Vinicius Inoue", "Analista de Qualidade", "https://github.com/vinikenceub"),
]

for nome, papel, github in equipe:
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{nome}**")
            st.caption(papel)
        with col2:
            st.markdown(
                f'<a href="{github}" target="_blank" style="text-decoration: none; background: #1a5fa8; color: white; padding: 6px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block; text-align: center; width: 100%;">Ver GitHub</a>',
                unsafe_allow_html=True,
            )

st.markdown("<br>", unsafe_allow_html=True)
ui.footer("snapshot")
