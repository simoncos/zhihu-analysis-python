import unittest
from unittest.mock import patch

import igraph as ig
import numpy as np
import pandas as pd

from analysis.characterize import concentration_shares, gini, graph_structure, topic_side
from analysis.powerlaw_fit import ALTERNATIVES, analyze_series, classify


def powerlaw_row(**overrides):
    row = {
        "gof_p": 0.01,
        "R_lognormal": -1.0,
        "p_lognormal": 0.01,
        "R_exponential": 1.0,
        "p_exponential": 0.01,
        "R_truncated_power_law": -1.0,
        "p_truncated_power_law": 0.01,
        "R_stretched_exponential": 1.0,
        "p_stretched_exponential": 0.01,
        "R_tpl_vs_lognormal": 1.0,
        "p_tpl_vs_lognormal": 0.01,
    }
    row.update(overrides)
    return row


class PowerLawClassificationTests(unittest.TestCase):
    def test_rejected_power_law_names_truncated_only_after_direct_comparison(self):
        self.assertEqual(
            classify(powerlaw_row()),
            "Not power law; Truncated power law favored over lognormal",
        )

    def test_rejected_power_law_can_name_lognormal(self):
        self.assertEqual(
            classify(powerlaw_row(R_tpl_vs_lognormal=-1.0)),
            "Not power law; Lognormal favored over truncated power law",
        )

    def test_rejected_power_law_keeps_alternative_unresolved(self):
        self.assertEqual(
            classify(powerlaw_row(p_tpl_vs_lognormal=0.5)),
            "Not power law; alternative family unresolved",
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


class FakeDistribution:
    alpha = 2.5
    xmin = 1.0
    sigma = 0.1
    D = 0.03
    parameter2 = 0.002


class FakeFit:
    xmin = 1.0
    n_tail = 2
    power_law = FakeDistribution()
    truncated_power_law = FakeDistribution()

    @staticmethod
    def distribution_compare(first, second, normalized_ratio=True):
        return (1.0, 0.5)


class PowerLawOutputTests(unittest.TestCase):
    @patch("analysis.powerlaw_fit.gof_pvalue", return_value=0.5)
    @patch("analysis.powerlaw_fit._fit", return_value=FakeFit())
    def test_full_sample_and_candidate_accounting(self, _fit, _gof):
        row, _ = analyze_series("sample", [0, 1, 2, np.nan], n_sims=1)
        self.assertEqual(row["n_total"], 4)
        self.assertEqual(row["n_positive"], 2)
        self.assertEqual(row["n_zero_dropped"], 1)
        self.assertEqual(row["n_nonfinite_dropped"], 1)
        self.assertIn("stretched_exponential", ALTERNATIVES)
        self.assertIn("R_stretched_exponential", row)
        self.assertEqual(row["tpl_alpha"], FakeDistribution.alpha)
        self.assertEqual(row["tpl_lambda"], FakeDistribution.parameter2)


class CharacterizationParityTests(unittest.TestCase):
    def test_graph_reports_directed_scc_and_undirected_wcc_metrics(self):
        graph = ig.Graph(n=4, edges=[(0, 1), (1, 0), (1, 2), (2, 3)], directed=True)
        stats = graph_structure(graph, np.random.default_rng(42), n_path_samples=4)
        self.assertIn("assortativity_degree_directed", stats)
        self.assertIn("assortativity_degree_undirected", stats)
        self.assertIn("avg_shortest_path_giant_scc_sampled", stats)
        self.assertIn("avg_shortest_path_giant_wcc_undirected_sampled", stats)
        self.assertEqual(stats["diameter_lower_bound_giant_wcc_undirected"], 3)

    def test_wcc_sampling_does_not_advance_existing_rng(self):
        graph = ig.Graph(n=4, edges=[(0, 1), (1, 0), (1, 2), (2, 3)], directed=True)
        actual_rng = np.random.default_rng(42)
        expected_rng = np.random.default_rng(42)
        graph_structure(
            graph,
            actual_rng,
            n_path_samples=4,
            wcc_rng=np.random.default_rng(43),
        )
        # SCC sampling consumes one permutation from each; WCC must not consume
        # from ``actual_rng`` after that.
        expected_rng.choice(2, size=2, replace=False)
        self.assertAlmostEqual(actual_rng.random(), expected_rng.random())

    def test_topic_side_retains_topic_population_summary(self):
        user = pd.DataFrame({"user_url": ["u1", "u2", "u3"]})
        topics = pd.DataFrame(
            {"user_url": ["u1", "u1", "u2"], "topic": ["a", "b", "a"]}
        )
        stats = topic_side(topics, user)
        self.assertAlmostEqual(stats["topic_user_size_mean"], 1.5)
        self.assertAlmostEqual(stats["topic_user_size_median"], 1.5)


if __name__ == "__main__":
    unittest.main()
