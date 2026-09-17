"""
Blood Collection Dashboard - Standalone Desktop Application

A standalone desktop application using PyWebView for monitoring biomarker 
collection progress in a simulated clinical trial.

Run with: python flask_app.py
"""

import os
import random
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import webview
import numpy as np

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config', 'config.yaml')

# Simple config loading
import yaml
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

APP_CONFIG = config['blood_collection_dash_app']

def load_data():
    """Load all biomarker datasets from CSV files with column-based structure."""
    data = {}
    for dataset_key, dataset_config in APP_CONFIG['input_datas'].items():
        csv_path = os.path.join(SCRIPT_DIR, dataset_config['csv_file_path'])
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            # Identify data columns (everything except pseudo_ID)
            participant_col = 'pseudo_ID'
            visit_cols = [col for col in df.columns if col != participant_col]
            
            # Fill in any missing values with random selection
            collected_val = dataset_config['values']['collected']
            not_collected_val = dataset_config['values']['not_collected']
            seed = dataset_config.get('random_seed', 42)
            random.seed(seed)
            
            for col in visit_cols:
                df[col] = df[col].apply(
                    lambda v: random.choice([collected_val, not_collected_val])
                    if pd.isna(v) or str(v).strip() == "" else v
                )
            
            # Compute metrics
            total = df[visit_cols].size
            collected_count = int((df[visit_cols] == collected_val).sum().sum())
            not_collected_count = total - collected_count
            pct = round(collected_count / total * 100, 1)
            per_visit_pct = ((df[visit_cols] == collected_val).sum() / len(df) * 100).round(1)
            per_participant_pct = ((df[visit_cols] == collected_val).sum(axis=1) / len(visit_cols) * 100).round(1)
            
            data[dataset_key] = {
                'df': df,
                'participant_col': participant_col,
                'visit_cols': visit_cols,
                'values': dataset_config['values'],
                'metrics': {
                    'total': total,
                    'collected': collected_count,
                    'not_collected': not_collected_count,
                    'pct': pct,
                    'per_visit_pct': per_visit_pct,
                    'per_participant_pct': per_participant_pct
                }
            }
    return data

def create_bar_chart(df, visit_cols, values, metrics):
    """Create per-visit bar chart."""
    pct = metrics['per_visit_pct']
    bar_colors = ['#2ecc71' if p >= 50 else '#e74c3c' for p in pct.values]
    
    fig = go.Figure(go.Bar(
        x=visit_cols,
        y=pct.values,
        marker_color=bar_colors,
        text=[f"{p:.1f}%" for p in pct.values],
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Collection rate: %{y}%<extra></extra>"
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#7f8c8d", annotation_text="50%")
    fig.update_layout(
        height=APP_CONFIG['charts']['bar_height'],
        yaxis=dict(title="Collection rate (%)", range=[0, 110]),
        xaxis=dict(title="Visit"),
        paper_bgcolor=APP_CONFIG['colors']['card_bg'],
        plot_bgcolor=APP_CONFIG['colors']['background'],
        font=dict(family=APP_CONFIG['charts']['font_family'], size=APP_CONFIG['charts']['font_size'], color=APP_CONFIG['colors']['text']),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False
    )
    return fig

def create_histogram(df, visit_cols, values, metrics):
    """Create participant distribution histogram."""
    fig = px.histogram(
        metrics['per_participant_pct'],
        nbins=13,
        color_discrete_sequence=[APP_CONFIG['colors']['accent']]
    )
    fig.update_traces(hovertemplate="Rate: %{x:.1f}%<br>Participants: %{y}<extra></extra>")
    fig.update_layout(
        height=APP_CONFIG['charts']['bar_height'],
        xaxis=dict(title="% visits collected", range=[-5, 105]),
        yaxis=dict(title="Number of participants"),
        paper_bgcolor=APP_CONFIG['colors']['card_bg'],
        plot_bgcolor=APP_CONFIG['colors']['background'],
        font=dict(family=APP_CONFIG['charts']['font_family'], size=APP_CONFIG['charts']['font_size'], color=APP_CONFIG['colors']['text']),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        bargap=0.05
    )
    return fig

def create_heatmap(df, visit_cols, values):
    """Create participant-by-visit heatmap with all 12 visits."""
    val_c, val_nc = values['collected'], values['not_collected']
    z = (df[visit_cols] == val_c).astype(int).values
    pids = df['pseudo_ID'].tolist()
    
    height = max(
        APP_CONFIG['charts']['heatmap_min_height'],
        len(pids) * APP_CONFIG['charts']['heatmap_row_height']
    )
    
    fig = go.Figure(go.Heatmap(
        z=z,
        x=visit_cols,
        y=pids,
        colorscale=[[0, APP_CONFIG['colors']['not_collected']], [1, APP_CONFIG['colors']['collected']]],
        showscale=False,
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
        customdata=[[val_c if v else val_nc for v in row] for row in z],
    ))
    fig.update_layout(
        height=height,
        width=APP_CONFIG['charts']['heatmap_width'],
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor=APP_CONFIG['colors']['card_bg'],
        plot_bgcolor=APP_CONFIG['colors']['card_bg'],
        font=dict(family=APP_CONFIG['charts']['font_family'], size=APP_CONFIG['charts']['font_size'], color=APP_CONFIG['colors']['text']),
        xaxis=dict(
            side="top",
            tickangle=0,  # Horizontal labels
            showticklabels=True,
            tickmode='auto',
            nticks=12  # Force all 12 labels
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=10)
        )
    )
    return fig

def render_dashboard():
    """Render the main dashboard HTML."""
    data = load_data()
    
    if not data:
        return '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Error</title></head>
<body style="padding:50px;text-align:center;font-family:Arial">
    <h1>Error: No data files found</h1>
    <p>Please run: python scripts/generate_data.py</p>
</body></html>'''
    
    # Build tab titles and content from all datasets
    tab_titles = []
    all_tabs_html = ""
    
    first_dataset = list(data.keys())[0]
    first_data = data[first_dataset]
    num_participants = first_data['df'].shape[0]
    num_visits = len(first_data['visit_cols'])
    
    for i, (dataset_key, dataset_info) in enumerate(data.items()):
        df = dataset_info['df']
        visit_cols = dataset_info['visit_cols']
        values = dataset_info['values']
        metrics = dataset_info['metrics']
        
        bar_fig = create_bar_chart(df, visit_cols, values, metrics)
        histogram_fig = create_histogram(df, visit_cols, values, metrics)
        heatmap_fig = create_heatmap(df, visit_cols, values)
        
        bar_html = bar_fig.to_html(include_plotlyjs='cdn', full_html=False)
        hist_html = histogram_fig.to_html(include_plotlyjs='cdn', full_html=False)
        heat_html = heatmap_fig.to_html(include_plotlyjs='cdn', full_html=False)
        
        # Extract biomarker type from dataset key for display label
        if 'blood_collection_output' in dataset_key:
            label = dataset_key.replace('blood_collection_output_', '').title().replace('_', ' ')
        else:
            label = 'Blood Collected'
        
        tab_titles.append(label)
        
        # Build tab content
        all_tabs_html += f'''
        <div id="tab-{i}" class="tab-content {"active" if i == 0 else ""}" data-collected="{values['collected']}" data-not-collected="{values['not_collected']}">
            <div class="kpi-row">
                <div class="kpi-card">
                    <div class="kpi-label">Overall Collection Rate</div>
                    <div class="kpi-value">{metrics['pct']}%</div>
                    <div class="kpi-subtext">{metrics['collected']} of {metrics['total']} samples</div>
                </div>
                <div class="kpi-card collected">
                    <div class="kpi-label">Samples Collected</div>
                    <div class="kpi-value">{metrics['collected']}</div>
                    <div class="kpi-subtext">{values['collected']}</div>
                </div>
                <div class="kpi-card not-collected">
                    <div class="kpi-label">Samples Not Collected</div>
                    <div class="kpi-value">{metrics['not_collected']}</div>
                    <div class="kpi-subtext">{values['not_collected']}</div>
                </div>
                <div class="kpi-card">
                    <div class="kpi-label">Total Participants</div>
                    <div class="kpi-value">{num_participants}</div>
                </div>
            </div>
            
            <div class="charts-row">
                <div class="chart-container">
                    <div class="chart-label">Collection Rate by Visit</div>
                    <div class="chart">{bar_html}</div>
                </div>
                <div class="chart-container">
                    <div class="chart-label">Participant Collection Distribution</div>
                    <div class="chart">{hist_html}</div>
                </div>
            </div>
            
            <div class="heatmap-container">
                <div class="chart-label">Participant × Visit Heatmap</div>
                <div class="legend-row">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: {APP_CONFIG['colors']['collected']};"></div>
                        <span class="legend-text">{values['collected']}</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: {APP_CONFIG['colors']['not_collected']};"></div>
                        <span class="legend-text">{values['not_collected']}</span>
                    </div>
                </div>
                <div class="chart">{heat_html}</div>
            </div>
        </div>'''
    
    # Build tabs navigation
    tabs_html = ""
    for i, title in enumerate(tab_titles):
        active = "active" if i == 0 else ""
        tabs_html += f'<button class="tab {active}" onclick="switchTab({i})">{title}</button>'
    
    # Build JavaScript
    js_code = '''
    function switchTab(tabIndex) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(function(content) {
            content.classList.remove('active');
        });
        
        // Remove active from all tabs
        document.querySelectorAll('.tab').forEach(function(tab) {
            tab.classList.remove('active');
        });
        
        // Show selected content
        var tabId = 'tab-' + tabIndex;
        document.getElementById(tabId).classList.add('active');
        
        // Add active to clicked tab
        var tabs = document.querySelectorAll('.tab');
        if (tabs[tabIndex]) {
            tabs[tabIndex].classList.add('active');
        }
        
        // Update legend colors based on dataset-specific values
        var tabContent = document.getElementById(tabId);
        var collectedValue = tabContent.getAttribute('data-collected');
        var notCollectedValue = tabContent.getAttribute('data-not-collected');
        var legendTexts = tabContent.querySelectorAll('.legend-text');
        if (legendTexts.length >= 2) {
            legendTexts[0].textContent = collectedValue;
            legendTexts[1].textContent = notCollectedValue;
        }
    }
    '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{APP_CONFIG['title']}</title>
    <script src="https://cdn.plotly.com/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: {APP_CONFIG['charts']['font_family']}; 
            background-color: {APP_CONFIG['colors']['background']}; 
            color: {APP_CONFIG['colors']['text']};
            font-size: {APP_CONFIG['charts']['font_size']}px;
        }}
        
        /* Header */
        .header {{
            background-color: {APP_CONFIG['colors']['header_bg']};
            color: {APP_CONFIG['colors']['header_text']};
            padding: 12px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid {APP_CONFIG['colors']['accent']};
        }}
        .header h1 {{
            font-size: 18px;
            font-weight: 600;
            margin: 0;
        }}
        .header-meta {{
            opacity: 0.8;
            font-size: 12px;
        }}
        
        /* Tabs */
        .tabs {{
            display: flex;
            background-color: white;
            border-bottom: 2px solid #dfe4ea;
            padding-left: 24px;
        }}
        .tab {{
            padding: 12px 24px;
            cursor: pointer;
            background: none;
            border: none;
            font-size: 14px;
            font-weight: 500;
            color: #57606f;
            transition: all 0.2s ease;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
        }}
        .tab:hover {{
            color: #3498db;
        }}
        .tab.active {{
            color: #3498db;
            font-weight: 600;
            border-bottom-color: #3498db;
        }}
        
        /* Content */
        .content {{
            padding: 24px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        
        /* KPI Cards */
        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background-color: white;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }}
        .kpi-card.collected {{
            border-color: {APP_CONFIG['colors']['collected']};
        }}
        .kpi-card.not-collected {{
            border-color: {APP_CONFIG['colors']['not_collected']};
        }}
        .kpi-label {{
            font-size: 11px;
            color: #747d8c;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 8px;
        }}
        .kpi-value {{
            font-size: 28px;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        }}
        .kpi-card.collected .kpi-value {{
            color: {APP_CONFIG['colors']['collected']};
        }}
        .kpi-card.not-collected .kpi-value {{
            color: {APP_CONFIG['colors']['not_collected']};
        }}
        .kpi-subtext {{
            font-size: 11px;
            color: #a4b0be;
            margin-top: 4px;
        }}
        
        /* Charts Row */
        .charts-row {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 16px;
        }}
        
        /* Chart Containers */
        .chart-container {{
            background-color: white;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            width: 100%;
            overflow-x: auto;
        }}
        .chart-label {{
            font-size: 11px;
            color: #747d8c;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        .chart {{
            background-color: white;
            border-radius: 4px;
        }}
        
        /* Heatmap Container */
        .heatmap-container {{
            background-color: white;
            border-radius: 6px;
            padding: 16px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }}
        
        /* Legend */
        .legend-row {{
            display: flex;
            gap: 24px;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f5f6fa;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
        .legend-text {{
            font-size: 11px;
            color: #57606f;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{APP_CONFIG['title']}</h1>
        <div class="header-meta">
            {num_participants} participants · {num_visits} visits
        </div>
    </div>
    
    <div class="tabs">
        {tabs_html}
    </div>
    
    <div class="content">
        {all_tabs_html}
    </div>
    
    <script>
    {js_code}
    </script>
</body>
</html>'''

def launch_app():
    """Launch the desktop application."""
    html_content = render_dashboard()
    
    temp_html_path = '/tmp/blood_dashboard.html'
    with open(temp_html_path, 'w') as f:
        f.write(html_content)
    
    print("Launching Blood Collection Dashboard...")
    print(f"Window size: {APP_CONFIG['window']['width']}x{APP_CONFIG['window']['height']}")
    
    window = webview.create_window(
        title=APP_CONFIG['title'],
        url=f'file://{temp_html_path}',
        width=APP_CONFIG['window']['width'],
        height=APP_CONFIG['window']['height'],
        resizable=APP_CONFIG['window']['resizable'],
        fullscreen=APP_CONFIG['window']['fullscreen'],
        background_color=APP_CONFIG['colors']['background']
    )
    
    webview.start()

if __name__ == '__main__':
    launch_app()
