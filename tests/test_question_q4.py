import unittest
import pandas as pd
from questions.question_q4 import get_mom_cb_cost_percentage_trend

class TestQuestionQ4(unittest.TestCase):

    def test_cb_cost_percentage_mom(self):
        # Sample data
        data = {
            "Month": ["Apr'25", "Apr'25", "May'25", "May'25", "Jun'25", "Jun'25"],
            "Type": ["C&B", "Revenue", "C&B", "Revenue", "C&B", "Revenue"],
            "Amount in USD": [10000, 50000, 12000, 60000, 9000, 55000]
        }
        df = pd.DataFrame(data)

        result = get_mom_cb_cost_percentage_trend(df)

        self.assertEqual(result.shape[0], 3)
        self.assertIn("C&B %", result.columns)
        self.assertIn("MoM Change (%)", result.columns)
        self.assertAlmostEqual(result.iloc[0]["C&B %"], 20.0)
        self.assertAlmostEqual(result.iloc[1]["C&B %"], 20.0)
        self.assertAlmostEqual(result.iloc[2]["C&B %"], 16.36, places=1)

if __name__ == "__main__":
    unittest.main()
