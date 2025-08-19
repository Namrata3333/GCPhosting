import unittest
import pandas as pd
from kpi_engine import cost

class TestCostKPI(unittest.TestCase):

    def setUp(self):
        # Sample mock data simulating LnTPnL structure
        self.sample_data = pd.DataFrame({
            "Amount in USD": [1000, 2000, 3000, 4000, 500],
            "Group1": [
                "COST - ONSITE", "COST - OFFSHORE", "COST - INDIRECT", 
                "COST - INDIRECT", "COST - ONSITE"
            ]
        })

    def test_total_cost(self):
        total = cost.calculate_total_cost(self.sample_data)
        self.assertEqual(total, 10500)

    def test_onsite_cost(self):
        onsite = cost.calculate_cost_by_type(self.sample_data, "ONSITE")
        self.assertEqual(onsite, 1500)

    def test_offshore_cost(self):
        offshore = cost.calculate_cost_by_type(self.sample_data, "OFFSHORE")
        self.assertEqual(offshore, 2000)

    def test_indirect_cost(self):
        indirect = cost.calculate_cost_by_type(self.sample_data, "INDIRECT")
        self.assertEqual(indirect, 7000)

    def test_summary(self):
        summary = cost.summarize_cost(self.sample_data)
        self.assertTrue(isinstance(summary, list))
        self.assertEqual(len(summary), 3)
        self.assertIn("💰", summary[0])
        self.assertIn("🏢", summary[1])
        self.assertIn("📊", summary[2])

if __name__ == "__main__":
    unittest.main()
