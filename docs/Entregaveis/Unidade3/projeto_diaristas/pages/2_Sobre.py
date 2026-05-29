"""Página Sobre — narrativa do PI 1."""

import streamlit as st

from dashboard import theme, ui

st.set_page_config(page_title="Sobre | Trabalho Doméstico Informal", layout="wide")
theme.inject_theme()
ui.render_sidebar()

theme.page_header(
    "Sobre o Projeto",
    "Projeto Integrador I — Trabalho Autônomo ou Informal · UniCEUB",
)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        """
        ### Visão

        O **Projeto Integrador I** investiga o espaço do problema da **Gig Economy**
        com recorte em **diaristas** e trabalho doméstico informal. O objetivo deste
        semestre não é construir o aplicativo final, mas entregar um **dashboard de
        análise da problemática** que evidencie, com dados, a existência de um problema
        real e validado.

        ### Metodologia

        Utilizamos **Design Thinking**, com foco nas etapas de **Empatia** (ouvir
        diaristas e contratantes) e **Definição** (delimitar o problema). Os dados
        cruzam pesquisa **macro** (PNAD Contínua / IBGE SIDRA) com pesquisa **micro**
        (Google Forms e entrevistas locais em Brasília, 2026).

        ### ODS 8 — Trabalho Decente

        O projeto está ancorado no **ODS 8**, investigando como a tecnologia pode
        transformar informalidade e vulnerabilidade em trabalho mais seguro e justo,
        incentivando formalização (MEI, eSocial doméstico) e remuneração equitativa.
        """
    )

with col2:
    with st.container(border=True):
        st.markdown('<p class="kpi-label">Diaristas estimadas (PNAD-C 1T2026)</p>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-value">1,82 mi</p>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-label" style="margin-top:.8rem">Domésticos sem carteira</p>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-value">76%</p>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-label" style="margin-top:.8rem">Respostas da pesquisa local</p>', unsafe_allow_html=True)
        st.markdown('<p class="kpi-value">127</p>', unsafe_allow_html=True)

st.markdown("### Equipe")
equipe = [
    ("Lucas Gonçalves Balduino", "Product Owner"),
    ("João Victor Rios", "Desenvolvedor Full-stack"),
    ("Alexsander Motta", "Analista de BI"),
    ("Beatriz Vasconcellos", "Pesquisadora UX"),
    ("Vinicius Inoue", "Analista de Qualidade"),
]
for nome, papel in equipe:
    st.markdown(f"- **{nome}** — {papel}")

st.markdown("### Roadmap")
st.markdown(
    """
    - **PI 1 (atual):** Dashboard de análise da problemática + pipeline ETL SIDRA
    - **PI 2:** Prototipação da plataforma e regras de negócio
    - **PI 3:** MVP e validação com usuários reais
    """
)

ui.footer("snapshot")
