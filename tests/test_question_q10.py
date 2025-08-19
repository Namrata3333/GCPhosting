import unittest
import pandas as pd
from questions.question_q10 import answer_question_q10

class TestQuestion10(unittest.TestCase):

    def setUp(self):
        self.ut = pd.DataFrame({
            "Final Customer Name": ["A", "A", "A", "A", "A", "A"],
            "Business_Unit": ["BU1"] * 6,
            "Delivery_Unit": ["DU1"] * 6,
            "Month": pd.date_range(start="2025-01-01", periods=6, freq="MS"),
            "HC": [20, 25, 30, 35, 40, 45],
            "Billed HC": [15, 20, 24, 30, 35, 39],
        })

    def test_du_query(self):
        result = answer_question_q10(self.ut, "DU1")
        self.assertIn("UT%", result["table"].columns)
        self.assertIn("Trend", result["chart"]["title"])

    def test_invalid_query(self):
        result = answer_question_q10(self.ut, "InvalidDU")
        self.assertIn("not found", result["answer"])
        self.assertTrue(result["table"].empty)

if __name__ == "__main__":
    unittest.main()
