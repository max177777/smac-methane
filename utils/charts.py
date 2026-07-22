from __future__ import annotations
"""
Chart helpers. Themed to the editorial palette used across the app.
- Plotly for interactive time series (hover, zoom)
- Altair for static bar/sector charts (cleaner editorial feel)
"""

import altair as alt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Palette (matches the SMAC editorial theme)
PAPER = "#f4efe6"
INK = "#1a1f1a"
INK_SOFT = "#3a4239"
LINE_SOFT = "#c4bca8"
MOSS = "#2d4a36"
COPPER = "#b5612a"
RUST = "#7a3a1a"
SKY = "#5d7a8c"


def time_series_plotly(df: pd.DataFrame, y_col: str = "ch4_tonnes",
                        title: str = "", height: int = 320) -> go.Figure:
    """Monthly time series with area fill. df must have 'date' and y_col columns."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[y_col],
        mode="lines",
        line=dict(color=MOSS, width=2),
        fill="tozeroy",
        fillcolor="rgba(45,74,54,0.12)",
        name="CH₄ tonnes",
        hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} t CH₄<extra></extra>",
    ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=20, b=10),
        plot_bgcolor=PAPER,
        paper_bgcolor=PAPER,
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        title=dict(text=title, font=dict(size=14, color=INK_SOFT)) if title else None,
        xaxis=dict(
            showgrid=False, showline=True, linecolor=INK, linewidth=1,
            tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=LINE_SOFT, gridwidth=0.5,
            zeroline=False, showline=True, linecolor=INK, linewidth=1,
            tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT),
            tickformat=",.0f",
        ),
        showlegend=False,
        hoverlabel=dict(bgcolor=PAPER, bordercolor=INK, font=dict(family="JetBrains Mono, monospace", color=INK)),
    )
    return fig


def multi_series_plotly(df_long: pd.DataFrame, height: int = 320) -> go.Figure:
    """Compare multiple series. df_long must have date, ch4_tonnes, and series columns."""
    palette = [MOSS, COPPER, SKY, RUST, INK_SOFT]
    fig = go.Figure()
    for i, (name, sub) in enumerate(df_long.groupby("series", sort=False)):
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["ch4_tonnes"], mode="lines", name=name,
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"<b>{name}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} t CH₄<extra></extra>",
        ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        xaxis=dict(showgrid=False, showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT)),
        yaxis=dict(showgrid=True, gridcolor=LINE_SOFT, gridwidth=0.5, zeroline=False,
                   showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT),
                   tickformat=",.0f"),
        legend=dict(orientation="h", y=1.10, x=0, font=dict(size=11, family="JetBrains Mono, monospace")),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=INK, font=dict(family="JetBrains Mono, monospace", color=INK)),
    )
    return fig


def horizontal_bar_altair(df: pd.DataFrame, label_col: str, value_col: str,
                           value_label: str = "Value", height: int = 280,
                           color_field: str | None = None) -> alt.Chart:
    """Horizontal bar chart, editorial styling."""
    base = alt.Chart(df).encode(
        y=alt.Y(f"{label_col}:N", sort="-x",
                axis=alt.Axis(title=None, labelFontSize=12,
                              labelFont="Inter", labelColor=INK,
                              labelLimit=200)),
        x=alt.X(f"{value_col}:Q",
                axis=alt.Axis(title=value_label, titleFontSize=10,
                              titleFont="JetBrains Mono", titleColor=INK_SOFT,
                              labelFontSize=10, labelFont="JetBrains Mono",
                              labelColor=INK_SOFT, format=",.0f",
                              gridColor=LINE_SOFT, gridDash=[2, 2])),
        tooltip=[label_col, alt.Tooltip(value_col, format=",.0f")],
    )
    if color_field:
        bars = base.mark_bar(height=18).encode(color=alt.Color(f"{color_field}:N", scale=alt.Scale(
            domain=["copper", "moss", "rust", "sky", "neutral"],
            range=[COPPER, MOSS, RUST, SKY, INK_SOFT]
        ), legend=None))
    else:
        bars = base.mark_bar(height=18, color=MOSS)
    return bars.properties(height=height, background=PAPER).configure_view(strokeWidth=0)


def sector_bar_altair(sectors: list[tuple[str, int]], height: int = 240) -> alt.Chart:
    """Sector decomposition bar chart."""
    df = pd.DataFrame(sectors, columns=["sector", "pct"])
    # First sector gets copper, second moss, others fade
    palette = [COPPER, MOSS, RUST, SKY, INK_SOFT, LINE_SOFT]
    df["color"] = [palette[i] if i < len(palette) else INK_SOFT for i in range(len(df))]

    chart = alt.Chart(df).mark_bar(height=18).encode(
        y=alt.Y("sector:N", sort="-x",
                axis=alt.Axis(title=None, labelFontSize=12, labelFont="Inter",
                              labelColor=INK, labelLimit=200)),
        x=alt.X("pct:Q",
                axis=alt.Axis(title="% of national CH₄", titleFontSize=10,
                              titleFont="JetBrains Mono", titleColor=INK_SOFT,
                              labelFontSize=10, labelFont="JetBrains Mono",
                              labelColor=INK_SOFT, gridColor=LINE_SOFT, gridDash=[2, 2])),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=["sector", alt.Tooltip("pct", title="Share %")],
    ).properties(height=height, background=PAPER).configure_view(strokeWidth=0)
    return chart


def yoy_bar_altair(df: pd.DataFrame, label_col: str = "location",
                    value_col: str = "yoy_pct", height: int = 280) -> alt.Chart:
    """YoY bar chart with diverging colours (rising = copper, falling = moss)."""
    df = df.copy()
    df["color"] = df[value_col].apply(lambda x: COPPER if x > 0 else MOSS)
    chart = alt.Chart(df).mark_bar(height=14).encode(
        y=alt.Y(f"{label_col}:N", sort=alt.SortField(field=value_col, order="descending"),
                axis=alt.Axis(title=None, labelFontSize=11, labelFont="Inter",
                              labelColor=INK)),
        x=alt.X(f"{value_col}:Q",
                axis=alt.Axis(title="YoY change (%)", titleFontSize=10,
                              titleFont="JetBrains Mono", titleColor=INK_SOFT,
                              labelFontSize=10, labelFont="JetBrains Mono",
                              labelColor=INK_SOFT, gridColor=LINE_SOFT, gridDash=[2, 2])),
        color=alt.Color("color:N", scale=None, legend=None),
        tooltip=[label_col, alt.Tooltip(value_col, format=".2f", title="YoY %")],
    ).properties(height=height, background=PAPER).configure_view(strokeWidth=0)
    return chart


def sparkline_plotly(df: pd.DataFrame, y_col: str = "ch4_tonnes", height: int = 60) -> go.Figure:
    """Tiny sparkline for cards."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df[y_col], mode="lines",
        line=dict(color=MOSS, width=1.4),
        fill="tozeroy", fillcolor="rgba(45,74,54,0.10)",
        hoverinfo="skip",
    ))
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=4, b=4),
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def comparison_plotly(df_long: pd.DataFrame, value_label: str = "CH₄ tonnes",
                      unit: str = "t CH₄", height: int = 360) -> go.Figure:
    """Overlay multiple subnational series for head-to-head comparison.
    df_long must have columns: date, value, series.
    """
    palette = [MOSS, COPPER, SKY, RUST, INK_SOFT, "#8a6d3b", "#436c70", "#9c5454"]
    fig = go.Figure()
    for i, (name, sub) in enumerate(df_long.groupby("series", sort=False)):
        fig.add_trace(go.Scatter(
            x=sub["date"], y=sub["value"], mode="lines", name=str(name),
            line=dict(color=palette[i % len(palette)], width=2),
            hovertemplate=f"<b>{name}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} {unit}<extra></extra>",
        ))
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        xaxis=dict(showgrid=False, showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT)),
        yaxis=dict(title=dict(text=value_label, font=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT)),
                   showgrid=True, gridcolor=LINE_SOFT, gridwidth=0.5, zeroline=False,
                   showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT),
                   tickformat=",.0f"),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(size=11, family="JetBrains Mono, monospace")),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=INK, font=dict(family="JetBrains Mono, monospace", color=INK)),
    )
    return fig


# Stable sector palette + stacking order (editorial earthy tones)
SECTOR_ORDER = [
    "fossil-fuel-operations", "agriculture", "waste", "land-use-change",
    "manufacturing", "power", "transportation", "mineral-extraction",
    "other-energy-use", "other",
]
SECTOR_COLORS = {
    "fossil-fuel-operations": COPPER,
    "agriculture": MOSS,
    "waste": RUST,
    "land-use-change": SKY,
    "manufacturing": "#8a6d3b",
    "power": "#436c70",
    "transportation": "#9c5454",
    "mineral-extraction": INK_SOFT,
    "other-energy-use": LINE_SOFT,
    "other": "#b8ad95",
}


def sector_stack_plotly(df_long: pd.DataFrame, normalize: bool = False,
                        height: int = 400) -> go.Figure:
    """Stacked bar comparing sector composition across regions.
    df_long must have columns: region, sector, value.
    normalize=True renders 100%-stacked (share of each region's total).
    Responsive — render with use_container_width=True so it follows the page.
    """
    d = df_long.copy()
    if normalize:
        totals = d.groupby("region")["value"].transform("sum")
        d["value"] = d["value"] / totals.replace(0, pd.NA) * 100

    order = (d.groupby("region")["value"].sum()
             .sort_values(ascending=False).index.tolist())
    suffix = "%" if normalize else " t CH₄"
    fig = go.Figure()
    for sector in SECTOR_ORDER:
        sub = d[d["sector"] == sector]
        if sub.empty:
            continue
        sub = sub.set_index("region").reindex(order).reset_index()
        fig.add_trace(go.Bar(
            x=sub["region"], y=sub["value"], name=sector,
            width=0.6,
            marker_color=SECTOR_COLORS.get(sector, INK_SOFT),
            marker_line=dict(color=PAPER, width=1),
            hovertemplate=f"<b>%{{x}}</b><br>{sector}: %{{y:,.1f}}{suffix}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack", height=height, bargap=0.35,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        xaxis=dict(showgrid=False, showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=11, family="Inter, sans-serif", color=INK)),
        yaxis=dict(title=dict(text="share of CH₄ (%)" if normalize else "CH₄ (t)",
                              font=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT)),
                   showgrid=True, gridcolor=LINE_SOFT, gridwidth=0.5, zeroline=False,
                   showline=True, linecolor=INK, linewidth=1,
                   tickfont=dict(size=10, family="JetBrains Mono, monospace", color=INK_SOFT),
                   tickformat=",.0f"),
        legend=dict(orientation="h", y=1.10, x=0, font=dict(size=10, family="JetBrains Mono, monospace")),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=INK, font=dict(family="JetBrains Mono, monospace", color=INK)),
    )
    return fig


def sector_pies_plotly(df_long: pd.DataFrame, height: int = 300) -> go.Figure:
    """A row of donut charts — one per region — showing sector composition (share).
    df_long must have columns: region, sector, value.
    Colours/legend match sector_stack_plotly. Responsive — render with
    use_container_width=True so the row of donuts follows the page width.
    """
    order = (df_long.groupby("region")["value"].sum()
             .sort_values(ascending=False).index.tolist())
    n = len(order)
    fig = make_subplots(
        rows=1, cols=n,
        specs=[[{"type": "domain"}] * n],
        subplot_titles=order,
        horizontal_spacing=0.03,
    )
    for i, reg in enumerate(order):
        sub = df_long[df_long["region"] == reg]
        present = [s for s in SECTOR_ORDER if s in set(sub["sector"])]
        sub = sub.set_index("sector").loc[present].reset_index()
        fig.add_trace(go.Pie(
            labels=sub["sector"], values=sub["value"],
            hole=0.5, sort=False, direction="clockwise",
            marker=dict(colors=[SECTOR_COLORS.get(s, INK_SOFT) for s in sub["sector"]],
                        line=dict(color=PAPER, width=1.5)),
            textinfo="percent", texttemplate="%{percent:.0%}",
            textposition="inside", insidetextorientation="horizontal",
            textfont=dict(size=10, family="JetBrains Mono, monospace", color=PAPER),
            hovertemplate=f"<b>{reg}</b><br>%{{label}}: %{{percent}}<extra></extra>",
            showlegend=False,
        ), row=1, col=i + 1)

    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        plot_bgcolor=PAPER, paper_bgcolor=PAPER,
        font=dict(family="Inter, sans-serif", size=12, color=INK),
        hoverlabel=dict(bgcolor=PAPER, bordercolor=INK,
                        font=dict(family="JetBrains Mono, monospace", color=INK)),
    )
    # subplot titles -> serif, ink
    fig.update_annotations(font=dict(size=13, family="Fraunces, serif", color=INK))
    return fig
