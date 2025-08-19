import unittest
import pandas as pd
from kpi_engine import revenue

class TestRevenueCalculations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load the data once for all tests
        cls.df = revenue.load_pnl_data("LnTPnL.xlsx", sheet_name="LnTPnL")

    def test_total_revenue(self):
        total = revenue.calculate_total_revenue(self.df)
        self.assertIsInstance(total, (float, int))
        self.assertGreaterEqual(total, 0)

    def test_onsite_revenue(self):
        onsite = revenue.calculate_revenue_by_type(self.df, "ONSITE")
        self.assertIsInstance(onsite, (float, int))
        self.assertGreaterEqual(onsite, 0)

    def test_invalid_revenue_type(self):
        with self.assertRaises(ValueError):
            revenue.calculate_revenue_by_type(self.df, "INVALID_TYPE")

if __name__ == '__main__':
    unittest.main()
