"""Dash app: Pink Morsel sales over time (processed CSV from data pipeline)."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html

DATA_PATH = Path(__file__).resolve().parent / "data" / "pink_morsel_sales.csv"
PRICE_CHANGE = pd.Timestamp("2021-01-15")


def build_figure() -> go.Figure:
    df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
    daily = (
        df.groupby("Date", as_index=False)["Sales"]
        .sum()
        .sort_values("Date", kind="mergesort")
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Sales"],
            mode="lines",
            name="Total daily sales",
            line={"width": 2, "color": "#c2185b"},
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
        line={"width": 1, "dash": "dash", "color": "#666"},
    )
    fig.add_annotation(
        x=PRICE_CHANGE,
        y=1,
        xref="x",
        yref="paper",
        text="15 Jan 2021: price increase",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font={"size": 12, "color": "#333"},
    )
    fig.update_layout(
        margin={"l": 56, "r": 24, "t": 16, "b": 48},
        plot_bgcolor="#fafafa",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
        showlegend=False,
        xaxis={
            "title": "Date",
            "showgrid": True,
            "gridcolor": "#e0e0e0",
        },
        yaxis={
            "title": "Total sales ($)",
            "showgrid": True,
            "gridcolor": "#e0e0e0",
            "tickformat": ",.0f",
        },
    )
    return fig


app = Dash(__name__)
app.title = "Pink Morsel sales — Soul Foods"
app.layout = html.Div(
    [
        html.Header(
            [
                html.H1(
                    "Soul Foods — Pink Morsel sales visualiser",
                    style={
                        "fontFamily": "system-ui, sans-serif",
                        "fontWeight": "600",
                        "fontSize": "1.75rem",
                        "marginBottom": "0.35rem",
                    },
                ),
                html.P(
                    "Daily total sales revenue (all regions), from transaction data.",
                    style={
                        "fontFamily": "system-ui, sans-serif",
                        "color": "#444",
                        "marginTop": 0,
                    },
                ),
            ]
        ),
        dcc.Graph(id="sales-line", figure=build_figure(), style={"height": "480px"}),
    ],
    style={"maxWidth": "1000px", "margin": "0 auto", "padding": "1.5rem 1.25rem"},
)

server = app.server

if __name__ == "__main__":
    app.run(debug=True)
