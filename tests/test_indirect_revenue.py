# tests/test_indirect_revenue.py

import unittest
import pandas as pd
from kpi_engine import indirect_revenue
from google.cloud import storage
import json
import os
from io import BytesIO
class TestIndirectRevenue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.df = indirect_revenue.load_data("LnTPnL.xlsx")
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.df, pd.DataFrame)
        self.assertFalse(self.df.empty)

    def test_calculate_indirect_revenue(self):
        result = indirect_revenue.calculate_indirect_revenue(self.df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_no_indirect_rows(self):
        df_no_indirect = self.df[~(self.df["Type"] == "Indirect Revenue")]
        result = indirect_revenue.calculate_indirect_revenue(df_no_indirect)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
