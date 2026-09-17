import copy
import csv
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import pandas as pd
import yaml

import app_dash as dashboard


ROOT = Path(__file__).resolve().parents[1]


class DatasetValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'input.csv'
        self.config = copy.deepcopy(dashboard.cfg['input_datas']['blood_collection_data'])
        self.config['csv_file_path'] = str(self.path)

    def load(self, text):
        self.path.write_text(text)
        return dashboard.load_dataset(self.config)

    def test_valid_metrics_and_text_ids(self):
        df, visits, pid, collected, _ = self.load(
            'pseudo_ID,V1,V2\n001,Blood_collected,Not_collected\nNA,Not_collected,Blood_collected\n'
        )
        self.assertEqual(df[pid].tolist(), ['001', 'NA'])
        metrics = dashboard.compute_metrics(df, visits, pid, collected)
        self.assertEqual((metrics['total'], metrics['collected'], metrics['pct']), (4, 2, 50.0))

    def test_missing_and_unknown_statuses(self):
        for status in ['', ' ', 'Pending', 'Blood_collected ']:
            with self.subTest(status=status), self.assertRaisesRegex(ValueError, "input.csv.*participant 'P1'.*visit 'V1'"):
                self.load(f'pseudo_ID,V1\nP1,{status}\n')

    def test_missing_id_column(self):
        with self.assertRaisesRegex(ValueError, 'missing participant-ID column'):
            self.load('wrong,V1\nP1,Blood_collected\n')

    def test_missing_ids(self):
        for pid in ['', '  ']:
            with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'missing participant IDs.*2'):
                self.load(f'pseudo_ID,V1\n{pid},Blood_collected\n')

    def test_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "duplicate participant IDs.*P1"):
            self.load('pseudo_ID,V1\nP1,Blood_collected\nP1,Not_collected\n')

    def test_empty_inputs(self):
        for text in ['', 'pseudo_ID,V1\n', 'pseudo_ID\nP1\n']:
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'empty|at least one'):
                self.load(text)
        with self.assertRaisesRegex(ValueError, 'without participants and visits'):
            dashboard.compute_metrics(pd.DataFrame(columns=['V1']), ['V1'], 'pseudo_ID', 'Blood_collected')

    def test_distinct_status_labels(self):
        self.config['values']['not_collected'] = 'Blood_collected'
        with self.assertRaisesRegex(ValueError, 'labels must differ'):
            self.load('pseudo_ID,V1\nP1,Blood_collected\n')


class SourceConstraintTests(unittest.TestCase):
    def setUp(self):
        self.datasets = copy.deepcopy(dashboard.DATASETS)
        self.config = copy.deepcopy(dashboard.cfg['input_datas'])
        self.key = 'blood_collection_output_plasma'
        self.derived = self.datasets[self.key]
        self.source = self.datasets['blood_collection_data']

    def validate(self):
        dashboard.validate_source_constraints(self.datasets, self.config)

    def test_reordered_rows_columns_and_different_id_name(self):
        self.derived['df'] = self.derived['df'].iloc[::-1, ::-1].rename(columns={'pseudo_ID': 'subject_id'})
        self.derived['pid_col'] = 'subject_id'
        self.derived['visit_cols'] = self.derived['visit_cols'][::-1]
        self.validate()

    def test_processed_without_source(self):
        unavailable = self.source['df'][self.source['visit_cols']].eq('Not_collected')
        rows, cols = unavailable.to_numpy().nonzero()
        visit = self.source['visit_cols'][cols[0]]
        self.derived['df'].loc[rows[0], visit] = self.derived['val_collected']
        with self.assertRaisesRegex(ValueError, self.key + '.*without source collection'):
            self.validate()

    def test_mismatched_participants(self):
        self.derived['df'].loc[0, 'pseudo_ID'] = 'OTHER'
        with self.assertRaisesRegex(ValueError, 'participant IDs must match'):
            self.validate()

    def test_mismatched_visits(self):
        self.derived['df'] = self.derived['df'].rename(columns={'Visit_1': 'Other'})
        self.derived['visit_cols'][0] = 'Other'
        with self.assertRaisesRegex(ValueError, 'visits must match'):
            self.validate()

    def test_exactly_one_source(self):
        for flag in [False, True]:
            with self.subTest(flag=flag):
                self.config['blood_collection_data']['is_source'] = flag
                self.config[self.key]['is_source'] = flag
                with self.assertRaisesRegex(ValueError, 'exactly one'):
                    self.validate()


class DashboardTests(unittest.TestCase):
    def test_example_metrics(self):
        for key, ds in dashboard.DATASETS.items():
            with self.subTest(key=key):
                expected = (587, 48.9) if key == 'blood_collection_data' else (300, 25.0)
                self.assertEqual((ds['metrics']['collected'], ds['metrics']['pct']), expected)
                self.assertEqual(ds['metrics']['total'], 1200)

    def test_uniform_heatmap_domain(self):
        for collected in [False, True]:
            ds = copy.deepcopy(dashboard.DATASETS['blood_collection_data'])
            ds['df'].loc[:, ds['visit_cols']] = ds['val_collected'] if collected else ds['val_not_collected']
            trace = dashboard.make_heatmap(ds).data[0]
            self.assertEqual((trace.zmin, trace.zmax), (0, 1))
            self.assertTrue((trace.z == int(collected)).all())

    def test_wsgi_endpoints_and_all_tab_callbacks(self):
        self.assertIs(dashboard.server, dashboard.app.server)
        client = dashboard.server.test_client()
        for path in ['/', '/_dash-layout', '/_dash-dependencies']:
            self.assertEqual(client.get(path).status_code, 200)
        for key in dashboard.DATASETS:
            with self.subTest(key=key):
                response = client.post('/_dash-update-component', json={
                    'output': 'tab-content.children',
                    'outputs': {'id': 'tab-content', 'property': 'children'},
                    'inputs': [{'id': 'dataset-tabs', 'property': 'value', 'value': key}],
                    'state': [], 'changedPropIds': ['dataset-tabs.value'],
                })
                self.assertEqual(response.status_code, 200)
                self.assertIn(key + '-heatmap', response.get_data(as_text=True))


class GeneratorTests(unittest.TestCase):
    def test_reproducibility_and_custom_id_header(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ['scripts', 'config', 'data/simulated']:
                (root / relative).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'scripts/generate_data.py', root / 'scripts/generate_data.py')
            shutil.copyfile(ROOT / 'config/config.yaml', root / 'config/config.yaml')
            for source in (ROOT / 'data/simulated').glob('*.csv'):
                shutil.copyfile(source, root / 'data/simulated' / source.name)
            command = [sys.executable, str(root / 'scripts/generate_data.py')]
            subprocess.run(command, cwd=directory, check=True, capture_output=True)
            for source in (ROOT / 'data/simulated').glob('*.csv'):
                self.assertEqual(source.read_bytes(), (root / 'data/simulated' / source.name).read_bytes())
            config_path = root / 'config/config.yaml'
            config = yaml.safe_load(config_path.read_text())
            ds_config = config['blood_collection_dash_app']['input_datas']['blood_collection_output_plasma']
            ds_config['participant_id_col'] = 'subject_id'
            config_path.write_text(yaml.safe_dump(config))
            subprocess.run(command, cwd=directory, check=True, capture_output=True)
            csv_path = root / ds_config['csv_file_path']
            with csv_path.open() as handle:
                self.assertEqual(next(csv.reader(handle))[0], 'subject_id')
            ds_config['csv_file_path'] = str(csv_path)
            df, visits, pid, collected, _ = dashboard.load_dataset(ds_config)
            self.assertEqual(pid, 'subject_id')
            self.assertEqual(dashboard.compute_metrics(df, visits, pid, collected)['collected'], 300)


if __name__ == '__main__':
    unittest.main()
