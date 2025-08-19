import unittest
import pandas as pd
from questions.question_q7 import question_7_realized_rate_drop

class TestQuestion7(unittest.TestCase):

    def test_realized_rate_drop(self):
        pnl_data = {
            "Final Customer name": ["A", "A", "B", "B"],
            "Quarter": ["FY25Q4", "FY26Q1", "FY25Q4", "FY26Q1"],
            "Revenue": [1000, 600, 1200, 800],
        }
        ut_data = {
            "Final Customer name": ["A", "A", "B", "B"],
            "Quarter": ["FY25Q4", "FY26Q1", "FY25Q4", "FY26Q1"],
            "HC": [10, 10, 10, 10],
        }
        pnl_df = pd.DataFrame(pnl_data)
        ut_df = pd.DataFrame(ut_data)

        result = question_7_realized_rate_drop(pnl_df, ut_df, threshold=3.0)

        self.assertIn("summary", result)
        self.assertGreaterEqual(len(result["table"]), 1)
        self.assertIn("Rate Drop", result["table"].columns)

if __name__ == "__main__":
    unittest.main()
