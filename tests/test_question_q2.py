import unittest
import pandas as pd
from questions.question_q2 import identify_margin_drop_costs

class TestQuestionQ2(unittest.TestCase):
    def test_identify_margin_drop_costs(self):
        sample_data = {
            "Segment": ["Transportation"] * 6,
            "Group Description": ["A", "B", "C", "A", "B", "C"],
            "Month": ["May-25", "May-25", "May-25", "Jun-25", "Jun-25", "Jun-25"],
            "Amount in USD": [1000, 2000, 1500, 3000, 2500, 1000],
            "Type": ["Cost"] * 6
        }
        df = pd.DataFrame(sample_data)
        result = identify_margin_drop_costs(df)
        self.assertIn("summary", result)
        self.assertIn("table", result)
        self.assertIn("chart", result)
