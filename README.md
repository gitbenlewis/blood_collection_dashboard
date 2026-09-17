# Blood Collection Dashboard

Config-driven Plotly Dash web application for monitoring biomarker collection progress in a simulated clinical trial.

![Blood Collection Dashboard](docs/images/blood_collection_dashboard.png)

## Overview

This dashboard tracks sample collection rates across multiple derived biomarker types (blood, plasma, serum, PBMC) for a simulated 100-participant clinical trial cohort. Derived datasets (plasma, serum, PBMC) are constrained so that collection is only possible at visits where the primary blood sample was collected.

Each biomarker type is presented in its own tab with:

- **KPI metric cards** -- overall collection rate, samples collected, samples not collected, total participants
- **Per-visit bar chart** -- collection percentage per visit with a 50% threshold reference line
- **Participant distribution histogram** -- spread of collection rates across the cohort
- **Participant-by-visit heatmap** -- full grid showing collection status for every participant at every timepoint

## Tech Stack

| Package | Version |
|---|---|
| Dash | 4.1.0 |
| Dash Bootstrap Components | 2.0.4 |
| Plotly | 6.6.0 |
| Pandas | 2.3.3 |
| PyYAML | 6.0.3 |
| Gunicorn | 26.2.0 |

## Setup

```bash
python -m pip install -r requirements.txt
```

## Data Generation

Regenerate simulated datasets with seeded randomness for reproducibility. This overwrites the configured CSVs. The existing source CSV header supplies the visit names, so retain it when regenerating:

```bash
python scripts/generate_data.py
```

This creates four CSVs in `data/simulated/`:

| File | Description |
|---|---|
| `blood_collected_at_visit.csv` | Primary blood collection (source dataset) |
| `blood_plasma_processed.csv` | Plasma processing, constrained to collected blood visits |
| `blood_serum_processed.csv` | Serum processing, constrained to collected blood visits |
| `blood_pbmc_processed.csv` | PBMC processing, constrained to collected blood visits |

The source dataset (`is_source: true` in config) is generated first. A source mask records which participant-visit combinations had blood collected, and derived datasets are constrained so that collection can only occur where the mask is `True`.

## Running the App

```bash
python app_dash.py
```

The dashboard launches at `http://localhost:8050` by default. CSVs are loaded at startup; restart the server after changing data.

### Input validation

Each CSV must contain its configured participant-ID column and at least one visit column. All remaining columns are treated as visits. IDs must be nonblank and unique; statuses must exactly match the configured collected/not-collected labels. Missing and unknown statuses cause a descriptive startup error rather than being filled or counted as failures. IDs are read as text to preserve leading zeros.

Configure exactly one source dataset. Derived datasets must contain the same participants and visits, but row and column order may differ. A processed sample requires a collected source sample for that participant and visit. Validated data retains the original denominator: all participant-visit combinations.

Randomness is used only by the simulation generator. The supplied derived datasets intentionally retain their existing shared seeds and identical collection masks.

## Config-Driven Architecture

The entire application is driven by `config/config.yaml`. No code changes are required to:

- **Add or remove datasets** -- define a new entry under `input_datas` with a CSV path, column mappings, and collected/not-collected value labels
- **Change the cohort** -- adjust `num_participants` and `participant_id_prefix`
- **Customize the UI** -- modify color schemes, chart dimensions, heatmap row heights, fonts, and font sizes
- **Set source constraints** -- mark one dataset as `is_source: true` to control which visits are available for derived datasets

### Config Structure

```yaml
blood_collection_dash_app:
  title: "Blood Collection Dashboard - Ben Lewis"
  num_participants: 100
  participant_id_prefix: "BL_"

  input_datas:
    blood_collection_data:
      is_source: true
      label: "Blood collected"
      csv_file_path: "data/simulated/blood_collected_at_visit.csv"
      participant_id_col: "pseudo_ID"
      values:
        collected: "Blood_collected"
        not_collected: "Not_collected"
      random_seed: 42
    # ... additional datasets

  colors:
    collected: "#2ecc71"
    not_collected: "#e74c3c"
    # ...

  charts:
    heatmap_row_height: 14
    bar_height: 360
    # ...
```

## Deployment

The included `Procfile` serves `app_dash:server` using Gunicorn and binds to Heroku's `PORT`. The Python entry point remains available for local development. Install `requirements.txt` even if using the optional Conda environment in `config/env_yamls/`.

To check the production server locally on macOS or Linux:

```bash
gunicorn app_dash:server --no-control-socket --bind 127.0.0.1:8050
```

Deploy to Heroku:

```bash
heroku create
git push heroku main
```

## Project Structure

```
blood_collection_dashboard/
├── app_dash.py               # Dashboard and WSGI entry point
├── config/                  # Application and optional Conda configuration
├── data/
│   └── simulated/            # Tracked example CSVs; generator outputs
├── docs/
│   └── images/               # README screenshot
├── scripts/
│   └── generate_data.py      # Seeded simulation generator
├── tests/
│   └── test_dashboard.py     # Validation, generator, chart, and callback tests
├── requirements.txt
├── Procfile
├── README.md
└── LICENSE
```

## Tests

Run from the repository root after installing dependencies:

```bash
python -m unittest discover -s tests -v
```

Generator tests write only to temporary directories.

## License

See [LICENSE](LICENSE) for details.
