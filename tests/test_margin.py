# tests/test_margin.py

import unittest
import pandas as pd
from kpi_engine import margin

class TestMarginKPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = pd.DataFrame({
            'Month': ['2024-01-01', '2024-01-01', '2024-02-01', '2024-02-01'],
            'Client': ['Client A', 'Client B', 'Client A', 'Client B'],
            'Type': ['Fixed', 'Project', 'Fixed', 'Project'],
            'Location': ['Onshore', 'Offshore', 'Onshore', 'Offshore'],
            'Revenue': [100000, 80000, 120000, 90000],
            'Cost': [60000, 50000, 70000, 40000]
        })
        cls.df['Month'] = pd.to_datetime(cls.df['Month'])
        cls.df = margin.preprocess_pnl_data(cls.df)

    def test_total_margin(self):
        result = margin.total_margin(self.df)
        self.assertEqual(result, 110000.0)

    def test_overall_margin_percent(self):
        result = margin.overall_margin_percent(self.df)
        self.assertAlmostEqual(result, 40.55, places=2)

    def test_margin_by_client(self):
        result = margin.margin_by_client(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Client A', result['Client'].values)

    def test_margin_by_type(self):
        result = margin.margin_by_type(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Fixed', result['Type'].values)

    def test_margin_by_location(self):
        result = margin.margin_by_location(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Onshore', result['Location'].values)

    def test_margin_trend(self):
        result = margin.margin_trend(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn(50000.0, result['Margin (₹)'].values)

    def test_margin_summary(self):
        summary = margin.margin_summary(self.df)
        self.assertEqual(len(summary), 4)
        self.assertTrue(summary[0].startswith("Total margin"))

if __name__ == '__main__':
    unittest.main()
