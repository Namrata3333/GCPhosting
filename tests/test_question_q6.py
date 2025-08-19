import unittest
import pandas as pd
from questions.question_q6 import calculate_revenue_trends

class TestQuestionQ6(unittest.TestCase):

    def setUp(self):
        self.data = pd.DataFrame({
            'Date': ['2023-04-01', '2023-05-01', '2023-06-01',
                     '2024-04-01', '2024-05-01', '2024-06-01'],
            'Delivery_Unit': ['DU1'] * 6,
            'Business_Unit': ['BU1'] * 6,
            'Final_Customer_Name': ['ClientA'] * 6,
            'Revenue': [100, 200, 150, 120, 180, 160]
        })

    def test_revenue_trends_output(self):
        result = calculate_revenue_trends(self.data)
        self.assertIn('yoy_trend', result)
        self.assertIn('qoq_trend', result)
        self.assertIn('mom_trend', result)

        # Check that we have non-empty results
        self.assertFalse(result['yoy_trend'].empty)
        self.assertFalse(result['qoq_trend'].empty)
        self.assertFalse(result['mom_trend'].empty)

        # Check if year aggregation is correct
        year_revenue = result['yoy_trend']
        total_2023 = year_revenue[year_revenue['Year'] == 2023]['Revenue'].values[0]
        self.assertEqual(total_2023, 450)

if __name__ == '__main__':
    unittest.main()
