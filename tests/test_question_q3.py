import unittest
import pandas as pd
from questions.question_q3 import compare_cb_variation_quarters

class TestQuestionQ3(unittest.TestCase):
    def test_compare_cb_variation_quarters(self):
        data = {
            "Group Description": ["C&B Cost"] * 6,
            "Month": ["Jan-25", "Feb-25", "Mar-25", "Apr-25", "May-25", "Jun-25"],
            "Amount in USD": [1000, 1000, 1000, 1200, 1300, 1400]
        }
        df = pd.DataFrame(data)
        result = compare_cb_variation_quarters(df)
        self.assertIn("summary", result)
        self.assertIn("table", result)
        self.assertIn("chart", result)
