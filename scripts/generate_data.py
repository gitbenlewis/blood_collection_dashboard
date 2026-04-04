"""
Fill empty cells in visit_log.csv with randomized Blood_collected / Not_collected values.
Reads seed and paths from config.yaml. Run once to populate the data file.
"""
import random
import csv
import os
import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")

with open(CONFIG_PATH) as f:
    cfg = yaml.safe_load(f)["blood_collection_dash_app"]

csv_path = os.path.join(os.path.dirname(__file__), "..", cfg["csv_file_path"])
values = list(cfg["values"].values())          # ['Blood_collected', 'Not_collected']
seed = cfg.get("random_seed", 42)

random.seed(seed)

with open(csv_path, newline="") as f:
    reader = csv.reader(f)
    rows = list(reader)

header = rows[0]
filled = [header]
for row in rows[1:]:
    pid = row[0]
    visits = [v if v.strip() else random.choice(values) for v in row[1:]]
    filled.append([pid] + visits)

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(filled)

print(f"Filled {len(filled)-1} participants across {len(header)-1} visits → {csv_path}")
