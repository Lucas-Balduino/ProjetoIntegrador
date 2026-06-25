"""Construtores de gráficos Plotly com tema consistente."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.theme import CHART_FONT, CHART_SEQUENCE, PALETTE


def _base_layout(fig: go.Figure, height: int = 300, showlegend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height + (50 if showlegend else 0),
        margin=dict(l=10, r=10, t=10, b=60 if showlegend else 10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        showlegend=showlegend,
        legend=dict(orientation="h", yanchor="top", y=-0.1, x=0, font=dict(size=11, color=PALETTE["text"])),
        hoverlabel=dict(
            bgcolor="rgba(15,29,46,0.92)",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#fff",
            bordercolor="rgba(15,29,46,0.92)",
        ),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=PALETTE["text_soft"])
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(221,230,239,0.5)", zeroline=False, color=PALETTE["text_soft"]
    )
    return fig


def donut(labels: list[str], values: list[float], center: str = "") -> go.Figure:
    text_colors = ["#ffffff", "#0d1f36", "#0d1f36", "#ffffff", "#0d1f36", "#ffffff"]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.76,
            marker=dict(colors=CHART_SEQUENCE[: len(labels)]),
            textinfo="percent",
            textfont=dict(size=11, color=text_colors[: len(labels)]),
            sort=False,
        )
    )
    annotations = []
    if center:
        annotations.append(
            dict(
                text=f"<b>{center}</b>",
                x=0.5, y=0.5,
                font=dict(size=20, color=PALETTE["primary"], family="Inter"),
                showarrow=False,
            )
        )
    fig.update_layout(
        height=330,
        margin=dict(l=10, r=10, t=10, b=80),
        paper_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05, x=0, font=dict(size=11, color=PALETTE["text"])),
        annotations=annotations,
        hoverlabel=dict(
            bgcolor="rgba(15,29,46,0.92)",
            font_size=12,
            font_family="Inter, sans-serif",
            font_color="#fff",
            bordercolor="rgba(15,29,46,0.92)",
        ),
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
            marker_line_width=0,
            text=[f"{y:g}{suffix}" for y in ys],
            textposition="outside",
            textfont=dict(size=11, color=PALETTE["text"]),
        )
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.1)
    fig.update_traces(marker=dict(cornerradius=6))
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
            marker_line_width=0,
            text=[f"{v:g}{suffix}" for v in values],
            textposition="outside",
            textfont=dict(size=11, color=PALETTE["text"]),
        )
    )
    fig.update_traces(marker=dict(cornerradius=6))
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
