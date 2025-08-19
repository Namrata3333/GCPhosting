import unittest
import pandas as pd
from questions.question_q9 import answer_question_q9

class TestQuestion9(unittest.TestCase):

    def setUp(self):
        self.pnl = pd.DataFrame({
            "Final Customer Name": ["Alpha", "Alpha", "Beta"],
            "Month": ["2025-05-01", "2025-06-01", "2025-06-01"],
            "Amount in USD": [50000, 60000, 70000]
        })

        self.ut = pd.DataFrame({
            "Final Customer Name": ["Alpha", "Alpha", "Beta"],
            "Month": ["2025-05-01", "2025-06-01", "2025-06-01"],
            "HC": [25, 30, 40]
        })

    def test_valid_account(self):
        result = answer_question_q9(self.pnl, self.ut, "Alpha")
        self.assertIn("Revenue per person for account", result["answer"])
        self.assertIn("Revenue per Person", result["table"].columns)
        self.assertEqual(result["chart"]["type"], "line")

    def test_missing_data(self):
        result = answer_question_q9(self.pnl, self.ut, "NonExistent")
        self.assertIn("not available", result["answer"])
        self.assertTrue(result["table"].empty)

if __name__ == "__main__":
    unittest.main()
