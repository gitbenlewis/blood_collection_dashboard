"""
Blood Collection Dashboard
Config-driven Plotly Dash app for monitoring clinical trial biomarker collection.
"""
import os
import yaml
import pandas as pd
import random
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)["blood_collection_dash_app"]

TITLE        = cfg["title"]
CSV_PATH     = os.path.join(BASE_DIR, cfg["csv_file_path"])
PID_COL      = cfg["participant_id_col"]
VAL_COLLECTED    = cfg["values"]["collected"]
VAL_NOT_COLLECTED = cfg["values"]["not_collected"]
SEED         = cfg.get("random_seed", 42)
COLORS       = cfg["colors"]
CHARTS       = cfg["charts"]
APP_HOST     = cfg["app"]["host"]
APP_PORT     = cfg["app"]["port"]
APP_DEBUG    = cfg["app"]["debug"]

# ── Data ──────────────────────────────────────────────────────────────────────
def load_data():
    df = pd.read_csv(CSV_PATH)
    # Fill any remaining empty cells with randomized values (reproducible)
    random.seed(SEED)
    visit_cols = [c for c in df.columns if c != PID_COL]
    for col in visit_cols:
        df[col] = df[col].apply(
            lambda v: random.choice([VAL_COLLECTED, VAL_NOT_COLLECTED])
            if pd.isna(v) or str(v).strip() == ""
            else v
        )
    return df, visit_cols

df, VISIT_COLS = load_data()

# ── Derived metrics ───────────────────────────────────────────────────────────
def compute_metrics(data, visit_cols):
    total_cells   = data[visit_cols].size
    collected     = (data[visit_cols] == VAL_COLLECTED).sum().sum()
    not_collected = (data[visit_cols] == VAL_NOT_COLLECTED).sum().sum()
    pct           = round(collected / total_cells * 100, 1)

    per_visit = (data[visit_cols] == VAL_COLLECTED).sum()
    per_visit_pct = (per_visit / len(data) * 100).round(1)

    per_participant = (data[visit_cols] == VAL_COLLECTED).sum(axis=1)
    per_participant_pct = (per_participant / len(visit_cols) * 100).round(1)

    return {
        "total": total_cells,
        "collected": int(collected),
        "not_collected": int(not_collected),
        "pct": pct,
        "per_visit_pct": per_visit_pct,
        "per_participant_pct": per_participant_pct,
    }

metrics = compute_metrics(df, VISIT_COLS)

# ── Chart builders ────────────────────────────────────────────────────────────
def make_heatmap(data, visit_cols):
    z = (data[visit_cols] == VAL_COLLECTED).astype(int).values
    pids = data[PID_COL].tolist()

    height = max(
        CHARTS["heatmap_min_height"],
        len(pids) * CHARTS["heatmap_row_height"],
    )

    fig = go.Figure(
        go.Heatmap(
            z=z,
            x=visit_cols,
            y=pids,
            colorscale=[
                [0, COLORS["not_collected"]],
                [1, COLORS["collected"]],
            ],
            showscale=False,
            hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
            customdata=[[VAL_COLLECTED if v else VAL_NOT_COLLECTED for v in row] for row in z],
        )
    )
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["card_bg"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        xaxis=dict(side="top", tickangle=-45),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
    )
    return fig


def make_per_visit_bar(per_visit_pct, visit_cols):
    colors = [
        COLORS["collected"] if p >= 50 else COLORS["not_collected"]
        for p in per_visit_pct
    ]
    fig = go.Figure(
        go.Bar(
            x=visit_cols,
            y=per_visit_pct.values,
            marker_color=colors,
            text=[f"{p}%" for p in per_visit_pct.values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Collection rate: %{y}%<extra></extra>",
        )
    )
    fig.add_hline(y=50, line_dash="dot", line_color=COLORS["subtext"], annotation_text="50%")
    fig.update_layout(
        height=CHARTS["bar_height"],
        yaxis=dict(title="Collection rate (%)", range=[0, 110]),
        xaxis=dict(title="Visit"),
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["background"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
    )
    return fig


def make_participant_histogram(per_participant_pct):
    fig = px.histogram(
        x=per_participant_pct,
        nbins=13,
        color_discrete_sequence=[COLORS["accent"]],
        labels={"x": "Collection rate (%)"},
    )
    fig.update_traces(
        hovertemplate="Rate: %{x}%<br>Participants: %{y}<extra></extra>"
    )
    fig.update_layout(
        height=CHARTS["bar_height"],
        xaxis=dict(title="% visits with blood collected", range=[-5, 105]),
        yaxis=dict(title="Number of participants"),
        paper_bgcolor=COLORS["card_bg"],
        plot_bgcolor=COLORS["background"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        bargap=0.05,
    )
    return fig


# ── KPI card helper ───────────────────────────────────────────────────────────
def kpi_card(label, value, sub=None, color=COLORS["accent"]):
    return dbc.Card(
        dbc.CardBody([
            html.P(label, className="text-muted mb-1", style={"fontSize": "0.78rem", "letterSpacing": "0.05em"}),
            html.H3(str(value), style={"color": color, "fontWeight": "700", "margin": "0"}),
            html.Small(sub, className="text-muted") if sub else None,
        ]),
        style={"backgroundColor": COLORS["card_bg"], "border": "1px solid #e0e0e0"},
        className="shadow-sm",
    )


# ── Layout ────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title=TITLE,
)

app.layout = dbc.Container(
    fluid=True,
    style={"backgroundColor": COLORS["background"], "minHeight": "100vh", "padding": "0"},
    children=[
        # Header
        html.Div(
            dbc.Row([
                dbc.Col(html.H4(TITLE, style={"margin": "0", "fontWeight": "600"}), width="auto"),
                dbc.Col(
                    html.Span(
                        f"{len(df)} participants · {len(VISIT_COLS)} visits",
                        style={"opacity": "0.7", "fontSize": "0.9rem"},
                    ),
                    className="d-flex align-items-center",
                ),
            ], align="center", className="g-0"),
            style={
                "backgroundColor": COLORS["header_bg"],
                "color": COLORS["header_text"],
                "padding": "14px 24px",
            },
        ),

        # KPI row
        dbc.Row(
            [
                dbc.Col(kpi_card("Overall Collection Rate", f"{metrics['pct']}%", f"{metrics['collected']} of {metrics['total']} samples", COLORS["collected"]), md=3),
                dbc.Col(kpi_card("Samples Collected",      metrics["collected"],  VAL_COLLECTED,     COLORS["collected"]),    md=3),
                dbc.Col(kpi_card("Samples Not Collected",  metrics["not_collected"], VAL_NOT_COLLECTED, COLORS["not_collected"]), md=3),
                dbc.Col(kpi_card("Total Participants",     len(df)),                                                                md=3),
            ],
            className="g-3",
            style={"padding": "16px 24px 0"},
        ),

        # Charts row 1 — per-visit bar + participant histogram
        dbc.Row(
            [
                dbc.Col([
                    html.H6("Collection Rate by Visit", className="text-muted mb-2", style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                    dcc.Graph(
                        id="per-visit-bar",
                        figure=make_per_visit_bar(metrics["per_visit_pct"], VISIT_COLS),
                        config={"displayModeBar": False},
                    ),
                ], md=6, style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px", "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),

                dbc.Col([
                    html.H6("Participant Collection Distribution", className="text-muted mb-2", style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                    dcc.Graph(
                        id="participant-hist",
                        figure=make_participant_histogram(metrics["per_participant_pct"]),
                        config={"displayModeBar": False},
                    ),
                ], md=6, style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px", "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),
            ],
            className="g-3",
            style={"padding": "16px 24px 0"},
        ),

        # Heatmap row
        dbc.Row(
            dbc.Col([
                html.H6("Participant × Visit Heatmap", className="text-muted mb-2", style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                # Legend
                html.Div([
                    html.Span(style={"display": "inline-block", "width": "12px", "height": "12px",
                                     "backgroundColor": COLORS["collected"], "borderRadius": "2px", "marginRight": "4px"}),
                    html.Span(VAL_COLLECTED, style={"fontSize": "0.78rem", "marginRight": "16px", "color": COLORS["text"]}),
                    html.Span(style={"display": "inline-block", "width": "12px", "height": "12px",
                                     "backgroundColor": COLORS["not_collected"], "borderRadius": "2px", "marginRight": "4px"}),
                    html.Span(VAL_NOT_COLLECTED, style={"fontSize": "0.78rem", "color": COLORS["text"]}),
                ], style={"marginBottom": "8px"}),
                dcc.Graph(
                    id="heatmap",
                    figure=make_heatmap(df, VISIT_COLS),
                    config={"displayModeBar": False},
                ),
            ],
            style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px", "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),
            className="g-3",
            style={"padding": "16px 24px 24px"},
        ),
    ],
)

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)
