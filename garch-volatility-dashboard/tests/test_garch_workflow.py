from __future__ import annotations

from datetime import date
import unittest

from src.garch_indices.config import DEFAULT_INDICES
from src.garch_indices.data import calculate_log_returns, generate_demo_prices
from src.garch_indices.garch import fit_garch11
from src.garch_indices.reporting import build_summary


class GarchWorkflowTest(unittest.TestCase):
    def test_demo_data_can_be_fitted_and_summarized(self) -> None:
        prices = generate_demo_prices(DEFAULT_INDICES, date(2020, 1, 1), date(2020, 12, 31))
        results = {}

        for name, frame in prices.items():
            returns = calculate_log_returns(frame)
            result = fit_garch11(returns["return_pct"].to_numpy(), max_iterations=120)
            self.assertGreater(result.omega, 0)
            self.assertGreaterEqual(result.alpha, 0)
            self.assertGreaterEqual(result.beta, 0)
            self.assertLess(result.persistence, 1)
            results[name] = result

        summary = build_summary(results)
        self.assertEqual(len(summary), len(DEFAULT_INDICES))
        self.assertIn("persistence_alpha_plus_beta", summary.columns)


if __name__ == "__main__":
    unittest.main()

