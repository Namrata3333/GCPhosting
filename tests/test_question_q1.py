# tests/test_question_q1.py

import unittest
import pandas as pd
from question_engine.question_q1 import analyze_low_cm_accounts

class TestQuestionQ1(unittest.TestCase):

    def setUp(self):
        self.sample_data = pd.DataFrame({
            'Final Customer Name': ['Client A', 'Client B', 'Client C', 'Client A'],
            'Month': ["Apr'25", "May'25", "Jun'25", "Mar'25"],
            'Revenue': [100000, 200000, 300000, 150000],
            'Cost': [80000, 150000, 295000, 100000]  # CM%: 20%, 25%, 1.67%, 33%
        })

    def test_low_cm_filtering(self):
        result = analyze_low_cm_accounts(self.sample_data)
        expected_clients = ['Client A', 'Client B', 'Client C']
        self.assertListEqual(sorted(result['Final Customer Name'].unique().tolist()), expected_clients)

    def test_excludes_non_q1_months(self):
        result = analyze_low_cm_accounts(self.sample_data)
        self.assertNotIn("Mar'25", result['Month'].tolist())

    def test_cm_values_below_threshold(self):
        result = analyze_low_cm_accounts(self.sample_data)
        self.assertTrue((result['CM%'] < 0.3).all())

if __name__ == '__main__':
    unittest.main()
