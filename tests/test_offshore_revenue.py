# tests/test_offshore_revenue.py

import unittest
import pandas as pd
from kpi_engine import offshore_revenue

class TestOffshoreRevenue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.df = offshore_revenue.load_data("LnTPnL.xlsx")
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.df, pd.DataFrame)
        self.assertFalse(self.df.empty)

    def test_calculate_offshore_revenue(self):
        result = offshore_revenue.calculate_offshore_revenue(self.df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_no_offshore_rows(self):
        df_no_offshore = self.df[~(self.df["Group1"] == "OFFSHORE")]
        result = offshore_revenue.calculate_offshore_revenue(df_no_offshore)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
