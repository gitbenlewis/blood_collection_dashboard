"""
Blood Collection Dashboard
Config-driven Plotly Dash app for monitoring clinical trial biomarker collection.
"""
import os
import random
import yaml
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output

# ── Config ────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)["blood_collection_dash_app"]

TITLE     = cfg["title"]
COLORS    = cfg["colors"]
CHARTS    = cfg["charts"]
APP_HOST  = cfg["app"]["host"]
APP_PORT  = int(os.environ.get("PORT", cfg["app"]["port"]))
APP_DEBUG = cfg["app"]["debug"]

# ── Data loading ──────────────────────────────────────────────────────────────
def load_dataset(ds_cfg):
    csv_path = os.path.join(BASE_DIR, ds_cfg["csv_file_path"])
    pid_col  = ds_cfg["participant_id_col"]
    val_c    = ds_cfg["values"]["collected"]
    val_nc   = ds_cfg["values"]["not_collected"]
    seed     = ds_cfg.get("random_seed", 42)

    df = pd.read_csv(csv_path)
    random.seed(seed)
    visit_cols = [c for c in df.columns if c != pid_col]
    for col in visit_cols:
        df[col] = df[col].apply(
            lambda v: random.choice([val_c, val_nc])
            if pd.isna(v) or str(v).strip() == "" else v
        )
    return df, visit_cols, pid_col, val_c, val_nc


def compute_metrics(df, visit_cols, pid_col, val_c):
    total    = df[visit_cols].size
    coll     = int((df[visit_cols] == val_c).sum().sum())
    not_coll = total - coll
    pct      = round(coll / total * 100, 1)
    per_visit_pct = ((df[visit_cols] == val_c).sum() / len(df) * 100).round(1)
    per_pt_pct    = ((df[visit_cols] == val_c).sum(axis=1) / len(visit_cols) * 100).round(1)
    return {
        "total": total, "collected": coll, "not_collected": not_coll,
        "pct": pct, "per_visit_pct": per_visit_pct, "per_participant_pct": per_pt_pct,
    }


# Load all datasets defined in config
DATASETS = {}
for key, ds_cfg in cfg["input_datas"].items():
    df, visit_cols, pid_col, val_c, val_nc = load_dataset(ds_cfg)
    # Use explicit label from config, or derive from the collected value name
    label = ds_cfg.get("label") or val_c.replace("_collected", "").replace("_processed", "").replace("_", " ")
    DATASETS[key] = {
        "df": df, "visit_cols": visit_cols, "pid_col": pid_col,
        "val_collected": val_c, "val_not_collected": val_nc,
        "metrics": compute_metrics(df, visit_cols, pid_col, val_c),
        "label": label,
    }

# ── Chart builders ────────────────────────────────────────────────────────────
def make_heatmap(ds):
    df, visit_cols = ds["df"], ds["visit_cols"]
    val_c, val_nc  = ds["val_collected"], ds["val_not_collected"]
    z    = (df[visit_cols] == val_c).astype(int).values
    pids = df[ds["pid_col"]].tolist()

    height = max(
        CHARTS["heatmap_min_height"],
        len(pids) * CHARTS["heatmap_row_height"],
    )
    fig = go.Figure(go.Heatmap(
        z=z, x=visit_cols, y=pids,
        colorscale=[[0, COLORS["not_collected"]], [1, COLORS["collected"]]],
        showscale=False, hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
        customdata=[[val_c if v else val_nc for v in row] for row in z],
    ))
    fig.update_layout(
        height=height,
        width=CHARTS.get("heatmap_width", 1200),
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["card_bg"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        xaxis=dict(side="top", tickangle=-45, tickfont=dict(size=9)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
    )
    return fig


def make_per_visit_bar(ds):
    m          = ds["metrics"]
    visit_cols = ds["visit_cols"]
    pct        = m["per_visit_pct"]
    bar_colors = [COLORS["collected"] if p >= 50 else COLORS["not_collected"] for p in pct]

    fig = go.Figure(go.Bar(
        x=visit_cols, y=pct.values,
        marker_color=bar_colors,
        text=[f"{p}%" for p in pct.values],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Collection rate: %{y}%<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color=COLORS["subtext"], annotation_text="50%")
    fig.update_layout(
        height=CHARTS["bar_height"],
        yaxis=dict(title="Collection rate (%)", range=[0, 110]),
        xaxis=dict(title="Visit"),
        paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["background"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
    )
    return fig


def make_participant_histogram(ds):
    per_pt_pct = ds["metrics"]["per_participant_pct"]
    fig = px.histogram(
        x=per_pt_pct, nbins=13,
        color_discrete_sequence=[COLORS["accent"]],
        labels={"x": "Collection rate (%)"},
    )
    fig.update_traces(hovertemplate="Rate: %{x}%<br>Participants: %{y}<extra></extra>")
    fig.update_layout(
        height=CHARTS["bar_height"],
        xaxis=dict(title="% visits collected", range=[-5, 105]),
        yaxis=dict(title="Number of participants"),
        paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["background"],
        font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
        margin=dict(l=10, r=10, t=20, b=10), showlegend=False, bargap=0.05,
    )
    return fig


# ── UI helpers ────────────────────────────────────────────────────────────────
def kpi_card(label, value, sub=None, color=COLORS["accent"]):
    return dbc.Card(
        dbc.CardBody([
            html.P(label, className="text-muted mb-1",
                   style={"fontSize": "0.78rem", "letterSpacing": "0.05em"}),
            html.H3(str(value), style={"color": color, "fontWeight": "700", "margin": "0"}),
            html.Small(sub, className="text-muted") if sub else None,
        ]),
        style={"backgroundColor": COLORS["card_bg"], "border": "1px solid #e0e0e0"},
        className="shadow-sm",
    )


def make_tab_content(key, ds):
    m      = ds["metrics"]
    val_c  = ds["val_collected"]
    val_nc = ds["val_not_collected"]

    return html.Div([
        # KPI row
        dbc.Row([
            dbc.Col(kpi_card("Overall Collection Rate", f"{m['pct']}%",
                             f"{m['collected']} of {m['total']} samples",
                             COLORS["collected"]), md=3),
            dbc.Col(kpi_card("Samples Collected",    m["collected"],    val_c,  COLORS["collected"]),    md=3),
            dbc.Col(kpi_card("Samples Not Collected", m["not_collected"], val_nc, COLORS["not_collected"]), md=3),
            dbc.Col(kpi_card("Total Participants",   len(ds["df"])),                                        md=3),
        ], className="g-3", style={"padding": "16px 0 0"}),

        # Charts row
        dbc.Row([
            dbc.Col([
                html.H6("Collection Rate by Visit", className="text-muted mb-2",
                        style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                dcc.Graph(id=f"{key}-bar", figure=make_per_visit_bar(ds),
                          config={"displayModeBar": False}),
            ], md=6, style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px",
                            "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),

            dbc.Col([
                html.H6("Participant Collection Distribution", className="text-muted mb-2",
                        style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                dcc.Graph(id=f"{key}-hist", figure=make_participant_histogram(ds),
                          config={"displayModeBar": False}),
            ], md=6, style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px",
                            "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),
        ], className="g-3", style={"padding": "16px 0 0"}),

        # Heatmap row
        dbc.Row(
            dbc.Col([
                html.H6("Participant × Visit Heatmap", className="text-muted mb-2",
                        style={"fontSize": "0.8rem", "letterSpacing": "0.04em"}),
                html.Div([
                    html.Span(style={"display": "inline-block", "width": "12px", "height": "12px",
                                     "backgroundColor": COLORS["collected"],
                                     "borderRadius": "2px", "marginRight": "4px"}),
                    html.Span(val_c,  style={"fontSize": "0.78rem", "marginRight": "16px",
                                             "color": COLORS["text"]}),
                    html.Span(style={"display": "inline-block", "width": "12px", "height": "12px",
                                     "backgroundColor": COLORS["not_collected"],
                                     "borderRadius": "2px", "marginRight": "4px"}),
                    html.Span(val_nc, style={"fontSize": "0.78rem", "color": COLORS["text"]}),
                ], style={"marginBottom": "8px"}),
                dcc.Graph(id=f"{key}-heatmap", figure=make_heatmap(ds),
                          config={"displayModeBar": False}),
            ], style={"backgroundColor": COLORS["card_bg"], "borderRadius": "6px",
                      "padding": "16px", "boxShadow": "0 1px 4px rgba(0,0,0,0.08)"}),
            className="g-3", style={"padding": "16px 0 24px"},
        ),
    ])


# ── Layout ────────────────────────────────────────────────────────────────────
first_ds = next(iter(DATASETS.values()))

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
                        f"{len(first_ds['df'])} participants · {len(first_ds['visit_cols'])} visits",
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

        # Tabs — one per dataset
        html.Div([
            dcc.Tabs(
                id="dataset-tabs",
                value=list(DATASETS.keys())[0],
                children=[
                    dcc.Tab(
                        label=ds["label"],
                        value=key,
                        style={
                            "padding": "10px 20px",
                            "fontFamily": CHARTS["font_family"],
                            "fontWeight": "500",
                        },
                        selected_style={
                            "padding": "10px 20px",
                            "fontFamily": CHARTS["font_family"],
                            "fontWeight": "600",
                            "borderTop": f"3px solid {COLORS['accent']}",
                            "color": COLORS["accent"],
                        },
                    )
                    for key, ds in DATASETS.items()
                ],
            ),
            html.Div(id="tab-content"),
        ], style={"padding": "0 24px"}),
    ],
)

# ── Callback — render tab content on selection ────────────────────────────────
@app.callback(Output("tab-content", "children"), Input("dataset-tabs", "value"))
def render_tab(tab_key):
    return make_tab_content(tab_key, DATASETS[tab_key])

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host=APP_HOST, port=APP_PORT, debug=APP_DEBUG)
