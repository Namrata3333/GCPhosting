# tests/test_bench.py

import unittest
import pandas as pd
from kpi_engine import bench

class TestBenchKPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = pd.DataFrame({
            'Month': ['2024-01-01', '2024-01-01', '2024-02-01', '2024-02-01'],
            'Client': ['Client A', 'Client B', 'Client A', 'Client B'],
            'Location': ['Onshore', 'Offshore', 'Onshore', 'Offshore'],
            'Billability': ['Bench', 'Billable', 'Bench', 'Bench']
        })
        cls.df['Month'] = pd.to_datetime(cls.df['Month'])
        cls.df = bench.preprocess_resource_data(cls.df)

    def test_total_bench_count(self):
        self.assertEqual(bench.total_bench_count(self.df), 3)

    def test_bench_percentage(self):
        self.assertEqual(bench.bench_percentage(self.df), 75.0)

    def test_bench_by_client(self):
        result = bench.bench_by_client(self.df)
        self.assertIn('Client A', result['Client'].values)

    def test_bench_by_location(self):
        result = bench.bench_by_location(self.df)
        self.assertIn('Onshore', result['Location'].values)

    def test_bench_trend(self):
        result = bench.bench_trend(self.df)
        self.assertEqual(len(result), 2)

    def test_bench_summary(self):
        summary = bench.bench_summary(self.df)
        self.assertEqual(len(summary), 3)
        self.assertTrue(summary[0].startswith("Total bench headcount"))

if __name__ == '__main__':
    unittest.main()
