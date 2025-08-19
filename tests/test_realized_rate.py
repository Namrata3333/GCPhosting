# tests/test_realized_rate.py

import unittest
import pandas as pd
from kpi_engine import realized_rate

class TestRealizedRate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            pnl_path = "LnTPnL.xlsx"
            ut_path = "LNTData.xlsx"
            cls.pnl_df, cls.ut_df = realized_rate.load_data(pnl_path, ut_path)
        except Exception as e:
            raise RuntimeError(f"Setup failed: {e}")

    def test_load_data(self):
        self.assertIsInstance(self.pnl_df, pd.DataFrame)
        self.assertIsInstance(self.ut_df, pd.DataFrame)
        self.assertFalse(self.pnl_df.empty)
        self.assertFalse(self.ut_df.empty)

    def test_calculate_realized_rate(self):
        result = realized_rate.calculate_realized_rate(self.pnl_df, self.ut_df)
        self.assertIsInstance(result, float)
        self.assertGreaterEqual(result, 0.0)

    def test_zero_available_hours(self):
        ut_df_zero = self.ut_df.copy()
        ut_df_zero["NetAvailableHours"] = 0
        result = realized_rate.calculate_realized_rate(self.pnl_df, ut_df_zero)
        self.assertEqual(result, 0.0)

if __name__ == '__main__':
    unittest.main()
