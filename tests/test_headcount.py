# tests/test_headcount.py

import unittest
import pandas as pd
from kpi_engine import headcount

class TestHeadcountKPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = pd.DataFrame({
            'Month': ['2024-01-01', '2024-01-01', '2024-02-01', '2024-02-01'],
            'Client': ['Client A', 'Client B', 'Client A', 'Client B'],
            'Type': ['Fixed', 'Project', 'Fixed', 'Project'],
            'Location': ['Onshore', 'Offshore', 'Onshore', 'Offshore']
        })
        cls.df['Month'] = pd.to_datetime(cls.df['Month'])
        cls.df = headcount.preprocess_resource_data(cls.df)

    def test_total_headcount(self):
        self.assertEqual(headcount.total_headcount(self.df), 4)

    def test_headcount_by_client(self):
        result = headcount.headcount_by_client(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Client A', result['Client'].values)

    def test_headcount_by_type(self):
        result = headcount.headcount_by_type(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Fixed', result['Type'].values)

    def test_headcount_by_location(self):
        result = headcount.headcount_by_location(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Onshore', result['Location'].values)

    def test_headcount_trend(self):
        result = headcount.headcount_trend(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn(2, result['Headcount'].values)

    def test_headcount_summary(self):
        summary = headcount.headcount_summary(self.df)
        self.assertEqual(len(summary), 3)
        self.assertTrue(summary[0].startswith("Total headcount"))

if __name__ == '__main__':
    unittest.main()
