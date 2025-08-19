import unittest
import pandas as pd
from questions.question_q5 import analyze_cb_cost_percentage_trend

class TestQuestionQ5(unittest.TestCase):
    def test_cb_cost_percentage_trend(self):
        # Mock Data
        data = {
            "Month": ["Apr'25", "Apr'25", "May'25", "May'25", "Jun'25", "Jun'25"],
            "Group Description": ["C&B", "Total Revenue", "C&B", "Total Revenue", "C&B", "Total Revenue"],
            "Amount in USD": [1000, 5000, 1200, 6000, 1500, 7500]
        }
        df = pd.DataFrame(data)

        result = analyze_cb_cost_percentage_trend(df)
        
        self.assertIn("summary", result)
        self.assertIn("table", result)
        self.assertIn("chart", result)
        self.assertEqual(len(result["table"]), 3)
        self.assertAlmostEqual(result["table"][0]["C&B Cost %"], 20.0, places=1)
        self.assertAlmostEqual(result["table"][1]["C&B Cost %"], 20.0, places=1)

if __name__ == "__main__":
    unittest.main()
