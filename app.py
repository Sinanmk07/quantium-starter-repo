"""Dash app: Pink Morsel sales over time with region filter and styling."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, callback, dcc, html

DATA_PATH = Path(__file__).resolve().parent / "data" / "pink_morsel_sales.csv"
PRICE_CHANGE = pd.Timestamp("2021-01-15")

REGION_OPTIONS = [
    {"label": "North", "value": "north"},
    {"label": "East", "value": "east"},
    {"label": "South", "value": "south"},
    {"label": "West", "value": "west"},
    {"label": "All", "value": "all"},
]

_df = pd.read_csv(DATA_PATH, parse_dates=["Date"])


def build_figure(region: str) -> go.Figure:
    if region == "all":
        daily = _df.groupby("Date", as_index=False)["Sales"].sum()
        series_label = "Total daily sales (all regions)"
        y_title = "Total sales ($)"
    else:
        sub = _df[_df["Region"].str.lower() == region.lower()]
        daily = sub.groupby("Date", as_index=False)["Sales"].sum()
        series_label = f"Daily sales — {region.title()}"
        y_title = "Sales ($)"

    daily = daily.sort_values("Date", kind="mergesort")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Sales"],
            mode="lines",
            name=series_label,
            line={"width": 2.5, "color": "#c2185b"},
            hovertemplate="%{x|%Y-%m-%d}<br>$%{y:,.0f}<extra></extra>",
        )
    )
    fig.add_shape(
        type="line",
        x0=PRICE_CHANGE,
        x1=PRICE_CHANGE,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line={"width": 1, "dash": "dash", "color": "rgba(80,60,70,0.55)"},
    )
    fig.add_annotation(
        x=PRICE_CHANGE,
        y=1,
        xref="x",
        yref="paper",
        text="15 Jan 2021 · price increase",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font={"size": 11, "color": "#5c4550"},
    )
    fig.update_layout(
        margin={"l": 58, "r": 20, "t": 12, "b": 44},
        plot_bgcolor="rgba(250,248,250,0.95)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        showlegend=False,
        xaxis={
            "title": "Date",
            "showgrid": True,
            "gridcolor": "rgba(194,24,91,0.08)",
            "zeroline": False,
            "title_font": {"size": 13, "color": "#4a3540"},
            "tickfont": {"color": "#5c4a52"},
        },
        yaxis={
            "title": y_title,
            "showgrid": True,
            "gridcolor": "rgba(194,24,91,0.08)",
            "zeroline": False,
            "tickformat": ",.0f",
            "title_font": {"size": 13, "color": "#4a3540"},
            "tickfont": {"color": "#5c4a52"},
        },
    )
    return fig


app = Dash(
    __name__,
    external_stylesheets=[
        "https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&display=swap",
    ],
)
app.title = "Pink Morsel sales — Soul Foods"

app.layout = html.Div(
    className="app-shell",
    children=[
        html.Div(
            className="app-inner",
            children=[
                html.Header(
                    className="hero",
                    children=[
                        html.Div("Soul Foods analytics", className="hero-badge"),
                        html.H1("Pink Morsel sales visualiser"),
                        html.P(
                            "Explore daily Pink Morsel revenue before and after the "
                            "15 January 2021 price change. Pick a region or view all."
                        ),
                    ],
                ),
                html.Div(
                    className="control-card",
                    children=[
                        html.Label("Region", className="control-heading", htmlFor="region-radio"),
                        dcc.RadioItems(
                            id="region-radio",
                            options=REGION_OPTIONS,
                            value="all",
                            className="region-radio",
                            inputStyle={"marginRight": "0.25rem"},
                        ),
                    ],
                ),
                html.Div(
                    className="chart-card",
                    children=[
                        dcc.Graph(id="sales-line", style={"height": "500px"}),
                    ],
                ),
                html.P(
                    "Transaction-derived data · line sorted by date",
                    className="footer-note",
                ),
            ],
        ),
    ],
    style={"fontFamily": "'DM Sans', ui-sans-serif, system-ui, sans-serif"},
)


@callback(Output("sales-line", "figure"), Input("region-radio", "value"))
def update_chart(region: str) -> go.Figure:
    return build_figure(region or "all")


server = app.server

if __name__ == "__main__":
    app.run(debug=True)
