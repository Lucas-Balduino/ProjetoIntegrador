"""Dashboard — Trabalho Doméstico Informal (Projeto Integrador I).

Análise da problemática de diaristas e trabalho doméstico informal (ODS 8),
cruzando PNAD Contínua (IBGE SIDRA) com pesquisa de campo local.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard import charts, data_loader, queries, theme, ui


# --------------------------------------------------------------------------- #
# Render por aba
# --------------------------------------------------------------------------- #
def _survey_grid(payload: dict[str, Any], publico: str, eyebrow: str) -> None:
    chart_specs = queries.list_survey_charts(payload, publico=publico)
    if not chart_specs:
        ui.empty_card("Sem dados de pesquisa para este perfil. Rode o ETL de formulários.")
        return
    cols = st.columns(2)
    for i, (slug, title) in enumerate(chart_specs):
        df = queries.survey_distribution(payload, slug, publico=publico)
        if df.empty:
            continue
        fig = charts.survey_donut(df) if len(df) <= 4 else charts.survey_bars(df)
        with cols[i % 2]:
            ui.chart_card(eyebrow, title, fig, table=df[[c for c in ("valor_texto", "contagem", "percentual") if c in df.columns]])


def render_overview(payload: dict[str, Any]) -> None:
    inf_geral = queries.taxa_informalidade_geral(payload)
    inf_dom = queries.informalidade_domestica(payload)
    rend = queries.rendimento_formal_informal(payload)
    horas = queries.horas_formal_informal(payload)
    split = queries.split_diarista_mensalista(payload)

    left, right = st.columns([3, 2])
    with left:
        fig = charts.vbar_grouped(
            ["Rendimento (R$)", "Horas/semana"],
            {
                "Formal / com carteira": [rend["formal"], horas["formal"]],
                "Informal / sem carteira": [rend["informal"], horas["informal"]],
            },
        )
        ui.chart_card(
            "PNAD-C · tabelas 5440 / 6374",
            "Rendimento e jornada: formal vs informal",
            fig,
            note="Trabalhadores formais ganham mais e cumprem jornada mais regular. "
            "Informais combinam menor remuneração e jornada mais instável.",
        )
    with right:
        fig = charts.donut(
            ["Informal", "Formal"], [inf_geral["informal"], inf_geral["formal"]],
            f"{inf_geral['informal']:.0f}%",
        )
        ui.chart_card("PNAD-C · tabela 8529", "Informalidade no mercado de trabalho", fig)

    c1, c2, c3 = st.columns(3)
    with c1:
        fig = charts.donut(
            ["Sem carteira", "Com carteira"], [inf_dom["informal"], inf_dom["formal"]],
            f"{inf_dom['informal']:.0f}%",
        )
        ui.chart_card("PNAD-C · tabela 4097", "Trabalho doméstico", fig)
    with c2:
        fig = charts.donut(
            ["2+ domicílios (diarista)", "1 domicílio (mensalista)"],
            [split["diarista"], split["mensalista"]],
            f"{split['diarista']:.0f}%",
        )
        ui.chart_card("PNAD-C · tabela 6383", "Perfil de atuação doméstica", fig)
    with c3:
        ui.tag_card(
            "PESQUISA LOCAL",
            "Principais preocupações",
            queries.preocupacoes(payload),
            note="Termos recorrentes nas respostas abertas de diaristas e contratantes.",
        )


def render_diaristas(payload: dict[str, Any]) -> None:
    rend = queries.rendimento_formal_informal(payload)
    mei = queries.mei_status(payload)
    c1, c2 = st.columns(2)
    with c1:
        fig = charts.vbar_grouped(
            ["Rendimento médio (R$)"],
            {"Com carteira": [rend["formal"]], "Sem carteira": [rend["informal"]]},
        )
        ui.chart_card("PNAD-C · tabela 5440", "Rendimento doméstico por vínculo", fig)
    with c2:
        if not mei.empty:
            ui.chart_card("PESQUISA LOCAL", "Status de MEI (diaristas)", charts.survey_donut(mei), table=mei)
        else:
            ui.empty_card("Sem dados de MEI na pesquisa.")
    _survey_grid(payload, "diarista", "PESQUISA · DIARISTAS")


def render_contratantes(payload: dict[str, Any]) -> None:
    canal = queries.canal_contratacao(payload)
    if not canal.empty:
        ui.chart_card("PESQUISA LOCAL", "Canais de contratação", charts.survey_bars(canal), table=canal)
    _survey_grid(payload, "contratante", "PESQUISA · CONTRATANTES")


def render_pesquisa(payload: dict[str, Any], active: dict[str, bool]) -> None:
    ui.tag_card(
        "ANÁLISE QUALITATIVA",
        "Mapa de preocupações da pesquisa de campo",
        queries.preocupacoes(payload),
        note="Tamanho do termo proporcional à frequência nas respostas abertas.",
    )
    publicos = [p for p, on in active.items() if on] or ["diarista", "contratante"]
    for publico in publicos:
        st.markdown(f'<p class="card-eyebrow" style="margin-top:1rem">PERFIL · {publico.upper()}</p>', unsafe_allow_html=True)
        _survey_grid(payload, publico, f"PESQUISA · {publico.upper()}")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(
        page_title="Trabalho Doméstico Informal",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    theme.inject_theme()
    active = ui.render_sidebar()

    payload = data_loader.load_marts()
    if not data_loader.marts_available(payload):
        theme.page_header("Trabalho Doméstico Informal", "Projeto Integrador I — UniCEUB")
        data_loader.show_data_missing_help()
        return

    theme.page_header(
        "Dashboard analítico · ODS 8",
        f"Projeto Integrador I — UniCEUB · PNAD-C e pesquisa de campo · {queries.periodo_label(payload)}",
    )
    ui.kpi_row(queries.kpi_summary(payload))

    tab_overview, tab_diaristas, tab_contratantes, tab_pesquisa = st.tabs(
        ["Visão geral", "Diaristas", "Contratantes", "Pesquisa local"]
    )
    with tab_overview:
        render_overview(payload)
    with tab_diaristas:
        render_diaristas(payload)
    with tab_contratantes:
        render_contratantes(payload)
    with tab_pesquisa:
        render_pesquisa(payload, active)

    ui.footer(payload.get("source", ""))


if __name__ == "__main__":
    main()
