# tests/test_utilization.py

import unittest
import pandas as pd
from kpi_engine import utilization

class TestUtilizationKPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df = pd.DataFrame({
            'Month': ['2024-01-01', '2024-01-01', '2024-02-01', '2024-02-01'],
            'Client': ['Client A', 'Client B', 'Client A', 'Client B'],
            'Type': ['Fixed', 'Project', 'Fixed', 'Project'],
            'Utilization %': [80, 70, 90, 60]
        })
        cls.df['Month'] = pd.to_datetime(cls.df['Month'])

    def test_overall_utilization(self):
        result = utilization.overall_utilization(self.df)
        self.assertAlmostEqual(result, 75.0)

    def test_utilization_by_client(self):
        result = utilization.utilization_by_client(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Client A', result['Client'].values)

    def test_utilization_by_type(self):
        result = utilization.utilization_by_type(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn('Fixed', result['Type'].values)

    def test_utilization_trend(self):
        result = utilization.utilization_trend(self.df)
        self.assertEqual(len(result), 2)
        self.assertIn(70.0, result['Utilization %'].values)

    def test_utilization_summary(self):
        summary = utilization.utilization_summary(self.df)
        self.assertEqual(len(summary), 4)
        self.assertTrue(summary[0].startswith("Overall utilization"))

if __name__ == '__main__':
    unittest.main()
