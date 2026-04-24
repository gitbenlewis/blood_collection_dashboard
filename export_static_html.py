"""
Blood Collection Dashboard - Static HTML Export
Exports the dashboard as a standalone HTML file with embedded data and charts.
"""
import os
import sys
import json
import yaml
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime

# ── Config ────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)["blood_collection_dash_app"]

TITLE = cfg["title"]
COLORS = cfg["colors"]
CHARTS = cfg["charts"]

# ── Data loading ──────────────────────────
def load_dataset(ds_cfg):
    csv_path = os.path.join(BASE_DIR, ds_cfg["csv_file_path"])
    pid_col = ds_cfg["participant_id_col"]
    val_c = ds_cfg["values"]["collected"]
    val_nc = ds_cfg["values"]["not_collected"]
    seed = ds_cfg.get("random_seed", 42)

    df = pd.read_csv(csv_path)
    
    # Apply random values to missing data (for export, use actual data)
    visit_cols = [c for c in df.columns if c != pid_col]
    for col in visit_cols:
        for idx in df.index:
            if pd.isna(df.at[idx, col]) or str(df.at[idx, col]).strip() == "":
                df.at[idx, col] = val_c if df.at[idx, visit_cols[0]] == val_c else val_nc
    
    return df, visit_cols, pid_col, val_c, val_nc


def compute_metrics(df, visit_cols, pid_col, val_c):
    total = df[visit_cols].size
    coll = int((df[visit_cols] == val_c).sum().sum())
    not_coll = total - coll
    pct = round(coll / total * 100, 1)
    per_visit_pct = ((df[visit_cols] == val_c).sum() / len(df) * 100).round(1)
    per_pt_pct = ((df[visit_cols] == val_c).sum(axis=1) / len(visit_cols) * 100).round(1)
    return {
        "total": total, "collected": coll, "not_collected": not_coll,
        "pct": pct, "per_visit_pct": per_visit_pct, "per_participant_pct": per_pt_pct,
    }


# ── HTML generation ─────────────────────────
def generate_static_html(output_path):
    """Generate a single HTML file with all tabs embedded."""
    
    # Load all datasets
    datasets = {}
    for key, ds_cfg in cfg["input_datas"].items():
        df, visit_cols, pid_col, val_c, val_nc = load_dataset(ds_cfg)
        label = ds_cfg.get("label") or val_c.replace("_collected", "").replace("_processed", "").replace("_", " ")
        datasets[key] = {
            "df": df, "visit_cols": visit_cols, "pid_col": pid_col,
            "val_collected": val_c, "val_not_collected": val_nc,
            "metrics": compute_metrics(df, visit_cols, pid_col, val_c),
            "label": label,
        }

    first_key = list(datasets.keys())[0]
    first_ds = datasets[first_key]
    
    # Inline Plotly.js so the export is self-contained (no CDN dependency).
    # Trade-off: ~5 MB file size vs. bulletproof offline rendering + no risk of
    # a CDN URL changing out from under old snapshots.
    import plotly.offline as _po
    plotly_js = _po.get_plotlyjs()

    # Create HTML structure
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TITLE}</title>
    <script type="text/javascript">{plotly_js}</script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "{CHARTS["font_family"]}", sans-serif;
            background-color: {COLORS["background"]};
            color: {COLORS["text"]};
            min-height: 100vh;
        }}
        .header {{
            background-color: {COLORS["header_bg"]};
            color: {COLORS["header_text"]};
            padding: 14px 24px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .header h1 {{ font-weight: 600; font-size: 1.5rem; margin: 0; }}
        .header-subtitle {{ opacity: 0.7; font-size: 0.9rem; margin-left: 20px; }}
        .tabs {{
            display: flex;
            padding: 0 24px;
            background-color: #f5f5f5;
            border-bottom: 1px solid #ddd;
        }}
        .tab {{
            padding: 10px 20px;
            cursor: pointer;
            font-family: "{CHARTS["font_family"]}", sans-serif;
            font-weight: 500;
            border: none;
            background: none;
            color: #666;
            font-size: 0.9rem;
            transition: all 0.2s;
        }}
        .tab:hover {{ color: {COLORS["accent"]}; }}
        .tab.active {{
            font-weight: 600;
            color: {COLORS["accent"]};
            border-top: 3px solid {COLORS["accent"]};
        }}
        .tab-content {{ display: none; padding: 24px; background-color: #f5f5f5; min-height: calc(100vh - 180px); }}
        .tab-content.active {{ display: block; }}
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .kpi-card {{
            background-color: {COLORS["card_bg"]};
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .kpi-label {{ font-size: 0.78rem; letter-spacing: 0.05em; color: #666; margin-bottom: 8px; text-transform: uppercase; }}
        .kpi-value {{ font-size: 2rem; font-weight: 700; margin: 0; }}
        .kpi-sub {{ font-size: 0.85rem; color: #666; margin-top: 4px; }}
        .charts-row {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        .chart-container {{
            background-color: {COLORS["card_bg"]};
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .chart-title {{
            font-size: 0.8rem;
            letter-spacing: 0.04em;
            color: #666;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}
        .heatmap-legend {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            font-size: 0.78rem;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 4px; }}
        .legend-box {{ width: 12px; height: 12px; border-radius: 2px; }}
        .chart-area {{
            background-color: {COLORS["card_bg"]};
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.85rem;
            border-top: 1px solid #e0e0e0;
            background-color: #f5f5f5;
        }}
        .timestamp {{ font-style: italic; color: #888; }}
        @media (max-width: 1200px) {{
            .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-row {{ grid-template-columns: 1fr; }}
        }}
        @media (max-width: 768px) {{
            .kpi-row {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <!-- Header -->
    <div class="header">
        <h1>{TITLE}</h1>
        <span class="header-subtitle">{len(first_ds['df'])} participants · {len(first_ds['visit_cols'])} visits</span>
    </div>
    
    <!-- Tabs -->
    <div class="tabs">
'''

    # Add tabs
    tab_keys = list(datasets.keys())
    for i, key in enumerate(tab_keys):
        active = "active" if i == 0 else ""
        html_content += f'        <button class="tab {active}" onclick="showTab(\'{key}\')">{datasets[key]["label"]}</button>\n'
    
    html_content += """    </div>
    
    <!-- Tab Contents -->
"""

    # Add tab contents
    for key, ds in datasets.items():
        active = "active" if key == tab_keys[0] else ""
        m = ds["metrics"]
        val_c = ds["val_collected"]
        val_nc = ds["val_not_collected"]
        
        html_content += f"""    <div id="{key}-tab" class="tab-content {'active' if active else ''}">
        
        <!-- KPI Cards -->
        <div class="kpi-row">
            <div class="kpi-card">
                <div class="kpi-label">Overall Collection Rate</div>
                <h2 class="kpi-value" style="color: {COLORS['collected']}">{m['pct']}%</h2>
                <div class="kpi-sub">{m['collected']} of {m['total']} samples</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Samples Collected</div>
                <h2 class="kpi-value" style="color: {COLORS['collected']}">{m['collected']}</h2>
                <div class="kpi-sub">{val_c}</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Samples Not Collected</div>
                <h2 class="kpi-value" style="color: {COLORS['not_collected']}">{m['not_collected']}</h2>
                <div class="kpi-sub">{val_nc}</div>
            </div>
            
            <div class="kpi-card">
                <div class="kpi-label">Total Participants</div>
                <h2 class="kpi-value">{len(ds['df'])}</h2>
                <div class="kpi-sub">All visits included</div>
            </div>
        </div>
        
        <!-- Charts Row -->
        <div class="charts-row">
            <div class="chart-container">
                <div class="chart-title">Collection Rate by Visit</div>
                <div id="{key}-bar-plot"></div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">Participant Collection Distribution</div>
                <div id="{key}-hist-plot"></div>
            </div>
        </div>
        
        <!-- Heatmap -->
        <div class="chart-area">
            <div class="chart-title">Participant × Visit Heatmap</div>
            <div class="heatmap-legend">
                <div class="legend-item">
                    <div class="legend-box" style="background-color: {COLORS['collected']}"></div>
                    <span>{val_c}</span>
                </div>
                <div class="legend-item">
                    <div class="legend-box" style="background-color: {COLORS['not_collected']}"></div>
                    <span>{val_nc}</span>
                </div>
            </div>
            <div id="{key}-heatmap-plot"></div>
        </div>
        
    </div>
"""

    # Add tab switching script
    html_content += """
    
    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.getElementById(tabId + '-tab').classList.add('active');
            const button = document.querySelector('.tab[onclick="showTab(\\'' + tabId + '\\')"]');
            if (button) {{
                button.classList.add('active');
            }}
            const plots = document.querySelectorAll('#' + tabId + '-bar-plot, #' + tabId + '-hist-plot, #' + tabId + '-heatmap-plot');
            plots.forEach(plotDiv => {{
                Plotly.Plots.resize(plotDiv);
            }});
        }}
    </script>
"""

    # Add chart data and render
    for key, ds in datasets.items():
        # Bar chart
        pct = ds["metrics"]["per_visit_pct"]
        bar_colors = [COLORS["collected"] if p >= 50 else COLORS["not_collected"] for p in pct]
        bar_fig = go.Figure(go.Bar(
            x=ds["visit_cols"], y=pct.values,
            marker_color=bar_colors,
            text=[f"{p}%" for p in pct.values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Collection rate: %{y}%<extra></extra>",
        ))
        bar_fig.add_hline(y=50, line_dash="dot", line_color=COLORS["subtext"], annotation_text="50%")
        bar_fig.update_layout(
            height=CHARTS["bar_height"],
            yaxis=dict(title="Collection rate (%)", range=[0, 110]),
            xaxis=dict(title="Visit"),
            paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["background"],
            font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
            margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
        )
        bar_json_str = bar_fig.to_json()
        bar_json = json.loads(bar_json_str)
        html_content += f"""
    <script>
        Plotly.newPlot('{key}-bar-plot', {json.dumps(bar_json['data'])}, {json.dumps(bar_json['layout'])}, {{responsive: true}});
    </script>
"""
        
        # Histogram
        hist_fig = px.histogram(
            x=ds["metrics"]["per_participant_pct"], nbins=13,
            color_discrete_sequence=[COLORS["accent"]],
            labels={"x": "Collection rate (%)"},
        )
        hist_fig.update_traces(hovertemplate="Rate: %{x}%<br>Participants: %{y}<extra></extra>")
        hist_fig.update_layout(
            height=CHARTS["bar_height"],
            xaxis=dict(title="% visits collected", range=[-5, 105]),
            yaxis=dict(title="Number of participants"),
            paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["background"],
            font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
            margin=dict(l=10, r=10, t=20, b=10), showlegend=False, bargap=0.05,
        )
        hist_json_str = hist_fig.to_json()
        hist_json = json.loads(hist_json_str)
        html_content += f"""
    <script>
        Plotly.newPlot('{key}-hist-plot', {json.dumps(hist_json['data'])}, {json.dumps(hist_json['layout'])}, {{responsive: true}});
    </script>
"""
        
        # Heatmap
        z = (ds["df"][ds["visit_cols"]] == ds["val_collected"]).astype(int).values
        pids = ds["df"][ds["pid_col"]].tolist()
        height = max(CHARTS["heatmap_min_height"], len(pids) * CHARTS["heatmap_row_height"])
        heatmap_fig = go.Figure(go.Heatmap(
            z=z, x=ds["visit_cols"], y=pids,
            colorscale=[[0, COLORS["not_collected"]], [1, COLORS["collected"]]],
            showscale=False, hoverongaps=False,
            hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
            customdata=[[ds["val_collected"] if v else ds["val_not_collected"] for v in row] for row in z],
        ))
        heatmap_fig.update_layout(
            height=height,
            width=CHARTS.get('heatmap_width', 1200),
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor=COLORS["card_bg"], plot_bgcolor=COLORS["card_bg"],
            font=dict(family=CHARTS["font_family"], size=CHARTS["font_size"], color=COLORS["text"]),
            xaxis=dict(side="top", tickangle=-45, tickfont=dict(size=9)),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        )
        heatmap_json_str = heatmap_fig.to_json()
        heatmap_json = json.loads(heatmap_json_str)
        html_content += f"""
    <script>
        Plotly.newPlot('{key}-heatmap-plot', {json.dumps(heatmap_json['data'])}, {json.dumps(heatmap_json['layout'])}, {{responsive: true}});
    </script>
"""

    # Footer
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html_content += f"""
    
    <!-- Footer -->
    <div class="footer">
        <div class="timestamp">Exported: {timestamp}</div>
        <div>Blood Collection Dashboard - Static Export</div>
        <div style="font-size: 0.75rem; margin-top: 8px;">Fully self-contained — works offline</div>
    </div>

</body>
</html>
"""

    # Write file
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    return output_path


if __name__ == "__main__":
    print("📄 Exporting Blood Collection Dashboard as Static HTML...")
    print("=" * 60)
    
    output_filename = "Blood_Collection_Dashboard_Static.html"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    try:
        result = generate_static_html(output_path)
        file_size = os.path.getsize(result)
        print(f"✅ Static HTML export complete!")
        print(f"📄 Output: {result}")
        print(f"📦 Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        print(f"📊 Datasets included: {len(cfg['input_datas'])} tabs")
        print("")
        print("To view: Open the file in any web browser")
        print("         (fully self-contained — works offline)")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
