"""Construtores de gráficos Plotly com tema consistente."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.theme import CHART_FONT, CHART_SEQUENCE, PALETTE


def _base_layout(fig: go.Figure, height: int = 300, showlegend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, x=0, font=dict(size=11)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=PALETTE["text_soft"])
    fig.update_yaxes(
        showgrid=True, gridcolor=PALETTE["border"], zeroline=False, color=PALETTE["text_soft"]
    )
    return fig


def donut(labels: list[str], values: list[float], center: str = "") -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=CHART_SEQUENCE[: len(labels)]),
            textinfo="percent",
            textfont=dict(size=12, color="#fff"),
            sort=False,
        )
    )
    fig.update_layout(
        height=270,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.18, x=0.1, font=dict(size=11)),
        annotations=[
            dict(text=center, x=0.5, y=0.5, font=dict(size=24, color=PALETTE["text"], family="Inter"), showarrow=False)
        ]
        if center
        else [],
    )
    return fig


def vbar_grouped(
    categories: list[str],
    series: dict[str, list[float]],
    suffix: str = "",
) -> go.Figure:
    fig = go.Figure()
    for i, (name, ys) in enumerate(series.items()):
        fig.add_bar(
            name=name,
            x=categories,
            y=ys,
            marker_color=CHART_SEQUENCE[i % len(CHART_SEQUENCE)],
            text=[f"{y:g}{suffix}" for y in ys],
            textposition="outside",
            textfont=dict(size=11, color=PALETTE["text"]),
        )
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
    return _base_layout(fig, height=320, showlegend=len(series) > 1)


def hbar(labels: list[str], values: list[float], suffix: str = "%") -> go.Figure:
    order = sorted(range(len(values)), key=lambda i: values[i])
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=PALETTE["primary"],
            text=[f"{v:g}{suffix}" for v in values],
            textposition="outside",
            textfont=dict(size=11, color=PALETTE["text"]),
        )
    )
    fig = _base_layout(fig, height=max(220, 46 * len(labels)))
    fig.update_xaxes(showgrid=False, visible=False)
    fig.update_yaxes(showgrid=False)
    return fig


def survey_bars(df: pd.DataFrame, label_col: str = "valor_texto", value_col: str = "percentual") -> go.Figure:
    if df.empty:
        return _base_layout(go.Figure())
    use_col = value_col if value_col in df.columns else "contagem"
    suffix = "%" if use_col == "percentual" else ""
    labels = df[label_col].astype(str).tolist()
    values = df[use_col].astype(float).tolist()
    return hbar(labels, values, suffix=suffix)


def survey_donut(df: pd.DataFrame, label_col: str = "valor_texto", value_col: str = "percentual") -> go.Figure:
    if df.empty:
        return donut(["Sem dados"], [100], "—")
    use_col = value_col if value_col in df.columns else "contagem"
    labels = df[label_col].astype(str).tolist()
    values = df[use_col].astype(float).tolist()
    idx = values.index(max(values))
    suffix = "%" if use_col == "percentual" else ""
    center = f"{values[idx]:.0f}{suffix}"
    return donut(labels, values, center)
