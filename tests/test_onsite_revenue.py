# tests/test_onsite_revenue.py

import unittest
import pandas as pd
from kpi_engine import onsite_revenue

class TestOnsiteRevenue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.df = onsite_revenue.load_data("LnTPnL.xlsx")
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.df, pd.DataFrame)
        self.assertFalse(self.df.empty)

    def test_calculate_onsite_revenue(self):
        result = onsite_revenue.calculate_onsite_revenue(self.df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_no_onsite_rows(self):
        df_no_onsite = self.df[~(self.df["Group1"] == "ONSITE")]
        result = onsite_revenue.calculate_onsite_revenue(df_no_onsite)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
