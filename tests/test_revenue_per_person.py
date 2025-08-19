# tests/test_revenue_per_person.py

import unittest
import pandas as pd
from kpi_engine import revenue_per_person

class TestRevenuePerPerson(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            pnl_path = "LnTPnL.xlsx"
            ut_path = "LNTData.xlsx"
            cls.pnl_df, cls.ut_df = revenue_per_person.load_data(pnl_path, ut_path)
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.pnl_df, pd.DataFrame)
        self.assertIsInstance(self.ut_df, pd.DataFrame)
        self.assertFalse(self.pnl_df.empty)
        self.assertFalse(self.ut_df.empty)

    def test_calculate_revenue_per_person(self):
        result = revenue_per_person.calculate_revenue_per_person(self.pnl_df, self.ut_df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_zero_headcount(self):
        ut_df_zero = self.ut_df.copy()
        ut_df_zero["Total_Headcount"] = 0
        result = revenue_per_person.calculate_revenue_per_person(self.pnl_df, ut_df_zero)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
