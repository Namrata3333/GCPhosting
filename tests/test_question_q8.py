import unittest
import pandas as pd
from questions.question_q8 import answer_question_q8

class TestQuestion8(unittest.TestCase):

    def setUp(self):
        self.df = pd.DataFrame({
            "Final Customer Name": ["Acme", "Acme", "Acme", "ZenCorp", "ZenCorp"],
            "Month": ["2025-04-01", "2025-05-01", "2025-06-01", "2025-05-01", "2025-06-01"],
            "HC": [50, 55, 52, 80, 83]
        })

    def test_valid_account(self):
        result = answer_question_q8(self.df, "Acme")
        self.assertIn("Headcount for account", result["answer"])
        self.assertEqual(result["table"].shape[0], 3)
        self.assertEqual(result["chart"]["type"], "line")

    def test_no_data_account(self):
        result = answer_question_q8(self.df, "NonExistent")
        self.assertIn("No headcount data found", result["answer"])
        self.assertTrue(result["table"].empty)

if __name__ == "__main__":
    unittest.main()
