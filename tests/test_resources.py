# tests/test_resources.py

import unittest
import pandas as pd
from kpi_engine import resources

class TestResourcesKPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = pd.DataFrame({
            'Month': ['2024-01-01', '2024-01-01', '2024-02-01'],
            'Client': ['Client A', 'Client B', 'Client A'],
            'Type': ['Fixed', 'Project', 'Fixed'],
            'Location': ['Onsite', 'Offshore', 'Onsite'],
            'Total Resources': [10, 20, 30]
        })
        cls.sample_data['Month'] = pd.to_datetime(cls.sample_data['Month'])

    def test_total_resources(self):
        total = resources.calculate_total_resources(self.sample_data)
        self.assertEqual(total, 60)

    def test_resources_by_client(self):
        result = resources.calculate_resources_by_client(self.sample_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[result['Client'] == 'Client A']['Total Resources'].values[0], 40)

    def test_resources_by_type(self):
        result = resources.calculate_resources_by_type(self.sample_data)
        self.assertEqual(len(result), 2)
        self.assertIn('Fixed', result['Type'].values)

    def test_resources_by_location(self):
        result = resources.calculate_resources_by_location(self.sample_data)
        self.assertEqual(len(result), 2)
        self.assertIn('Onsite', result['Location'].values)

    def test_resources_trend(self):
        result = resources.calculate_resources_trend(self.sample_data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[1]['Total Resources'], 30)

if __name__ == '__main__':
    unittest.main()
