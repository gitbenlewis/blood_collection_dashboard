"""
Generate/fill all CSV datasets defined in config.yaml.

The dataset with `is_source: true` is filled first; all other datasets are
generated with values constrained to visits where the source was collected.
"""
import random
import csv
import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
BASE_DIR    = os.path.join(os.path.dirname(__file__), "..")

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)["blood_collection_dash_app"]

input_datas      = cfg["input_datas"]
num_participants = cfg["num_participants"]
pid_prefix       = cfg["participant_id_prefix"]

# ── Identify source dataset from config ───────────────────────────────────────
source_key = next(
    (k for k, v in input_datas.items() if v.get("is_source", False)),
    None,
)
if source_key is None:
    raise ValueError("No dataset with 'is_source: true' found in config.yaml")

source_cfg = input_datas[source_key]

# ── 1. Generate source CSV ────────────────────────────────────────────────────
source_csv_path  = os.path.join(BASE_DIR, source_cfg["csv_file_path"])
source_values    = list(source_cfg["values"].values())
source_collected = source_cfg["values"]["collected"]
pid_col          = source_cfg["participant_id_col"]

# Derive visit columns from the existing CSV header, stripping any BOM characters
with open(source_csv_path, newline="", encoding="utf-8-sig") as f:
    existing_header = [col.replace('\ufeff', '').strip() for col in next(csv.reader(f))]
visit_cols = [c for c in existing_header if c != pid_col]

pids = [f"{pid_prefix}{i:07d}" for i in range(1, num_participants + 1)]
header = [pid_col] + visit_cols

random.seed(source_cfg.get("random_seed", 42))

filled = [header]
for pid in pids:
    visits = [random.choice(source_values) for _ in visit_cols]
    filled.append([pid] + visits)

os.makedirs(os.path.dirname(source_csv_path), exist_ok=True)
with open(source_csv_path, "w", newline="") as f:
    csv.writer(f).writerows(filled)

print(f"[{source_key}] generated {len(filled)-1} rows → {source_csv_path}")

# Mask: {pid: [True/False per visit]} — True where source was collected
source_mask = {
    row[0]: [v == source_collected for v in row[1:]]
    for row in filled[1:]
}

# ── 2. Generate output CSVs (constrained by source) ───────────────────────────
for key, ds_cfg in input_datas.items():
    if key == source_key:
        continue

    csv_path          = os.path.join(BASE_DIR, ds_cfg["csv_file_path"])
    val_collected     = ds_cfg["values"]["collected"]
    val_not_collected = ds_cfg["values"]["not_collected"]

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    random.seed(ds_cfg.get("random_seed", 42))

    out_rows = [header]
    for pid in pids:
        available = source_mask[pid]
        visits = [
            random.choice([val_collected, val_not_collected]) if available[i]
            else val_not_collected
            for i in range(len(visit_cols))
        ]
        out_rows.append([pid] + visits)

    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerows(out_rows)

    n_collected = sum(1 for row in out_rows[1:] for v in row[1:] if v == val_collected)
    print(f"[{key}] generated {len(out_rows)-1} rows, {n_collected} collected → {csv_path}")
