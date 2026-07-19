import unittest

from analysis.characterize import concentration_shares, gini
from analysis.powerlaw_fit import classify


def powerlaw_row(**overrides):
    row = {
        "gof_p": 0.01,
        "R_lognormal": -1.0,
        "p_lognormal": 0.01,
        "R_exponential": 1.0,
        "p_exponential": 0.01,
        "R_truncated_power_law": -1.0,
        "p_truncated_power_law": 0.01,
        "R_tpl_vs_lognormal": 1.0,
        "p_tpl_vs_lognormal": 0.01,
    }
    row.update(overrides)
    return row


class PowerLawClassificationTests(unittest.TestCase):
    def test_rejected_power_law_names_truncated_only_after_direct_comparison(self):
        self.assertEqual(
            classify(powerlaw_row()),
            "Not power law; Truncated power law favored",
        )

    def test_rejected_power_law_can_name_lognormal(self):
        self.assertEqual(
            classify(powerlaw_row(R_tpl_vs_lognormal=-1.0)),
            "Not power law; Lognormal favored",
        )

    def test_rejected_power_law_keeps_alternative_unresolved(self):
        self.assertEqual(
            classify(powerlaw_row(p_tpl_vs_lognormal=0.5)),
            "Not power law; TPL vs lognormal unresolved",
        )

    def test_rejected_power_law_does_not_name_an_alternative_that_loses(self):
        self.assertEqual(
            classify(
                powerlaw_row(
                    R_lognormal=1.0,
                    R_truncated_power_law=1.0,
                )
            ),
            "Not power law; no supported alternative selected",
        )


class ConcentrationMetricTests(unittest.TestCase):
    def test_equal_values_have_zero_gini(self):
        self.assertAlmostEqual(gini([1, 1, 1, 1]), 0.0)

    def test_equal_population_shares_follow_group_sizes(self):
        shares = concentration_shares([1] * 100)
        self.assertAlmostEqual(shares["top_1pct"], 0.01)
        self.assertAlmostEqual(shares["next_9pct"], 0.09)
        self.assertAlmostEqual(shares["bottom_90pct"], 0.90)


if __name__ == "__main__":
    unittest.main()
