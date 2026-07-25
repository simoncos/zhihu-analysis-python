import unittest
from unittest.mock import patch

import igraph as ig
import numpy as np
import pandas as pd

from analysis.bfs_bias import draw_balanced_degree_sequences
from analysis.characterize import concentration_shares, gini, graph_structure, homophily, topic_side
from analysis.powerlaw_fit import (
    ALTERNATIVES,
    _controlled_generate_random,
    apply_fdr_adjustments,
    analyze_series,
    classify,
)


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
    def test_skipped_gof_is_not_described_as_plausible(self):
        row = powerlaw_row(gof_p=None, analysis_status="not_evaluated")
        self.assertEqual(classify(row), "Not evaluated; GOF skipped")

    def test_nonfinite_comparison_is_invalid(self):
        row = powerlaw_row(R_lognormal=np.nan)
        self.assertEqual(classify(row), "Invalid fit; non-finite test statistic")

    def test_gof_interval_crossing_threshold_is_inconclusive(self):
        row = powerlaw_row(gof_p=0.08, gof_mc_ci_low=0.06, gof_mc_ci_high=0.11)
        self.assertEqual(
            classify(row),
            "GOF threshold unresolved at current Monte Carlo resolution",
        )

    def test_fdr_adjustment_is_reported_and_used(self):
        rows = [powerlaw_row(gof_p=0.01), powerlaw_row(gof_p=0.08)]
        adjusted = apply_fdr_adjustments(rows)
        self.assertAlmostEqual(adjusted[0]["q_gof_p"], 0.02)
        self.assertAlmostEqual(adjusted[1]["q_gof_p"], 0.08)
        self.assertIn("verdict_unadjusted", adjusted[0])

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

    @staticmethod
    def generate_random(size):
        return np.random.randint(1, 4, size=size)


class FakeFit:
    xmin = 1.0
    n_tail = 2
    power_law = FakeDistribution()
    truncated_power_law = FakeDistribution()

    @staticmethod
    def distribution_compare(first, second, normalized_ratio=True):
        return (1.0, 0.5)


class PowerLawOutputTests(unittest.TestCase):
    @patch(
        "analysis.powerlaw_fit.gof_bootstrap",
        return_value={
            "pvalue": 0.5,
            "exceedances": 1,
            "n_sims": 1,
            "mc_ci_low": 0.01,
            "mc_ci_high": 0.99,
        },
    )
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
        self.assertEqual(row["analysis_status"], "evaluated")

    def test_third_party_random_draw_restores_global_numpy_state(self):
        np.random.seed(123)
        expected = np.random.random()
        np.random.seed(123)
        _controlled_generate_random(FakeDistribution(), 10, np.random.default_rng(99))
        actual = np.random.random()
        self.assertAlmostEqual(actual, expected)

    @patch("analysis.powerlaw_fit._fit", return_value=FakeFit())
    def test_zero_simulations_produce_not_evaluated_row(self, _fit):
        row, _ = analyze_series("sample", [1, 2, 3], n_sims=0)
        self.assertEqual(row["analysis_status"], "not_evaluated")
        self.assertIsNone(row["gof_p"])
        self.assertEqual(row["verdict"], "Not evaluated; GOF skipped")


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

    def test_homophily_uses_repeated_matched_null(self):
        graph = ig.Graph(
            n=6,
            edges=[(0, 1), (0, 2), (3, 4), (3, 5), (1, 3), (4, 0)],
            directed=True,
        )
        graph.vs["name"] = [f"u{i}" for i in range(6)]
        user = pd.DataFrame(
            {
                "user_url": graph.vs["name"],
                "answer_num": [1, 2, 3, 1, 2, 3],
                "layer": [1, 1, 1, 2, 2, 2],
            }
        )
        topics = pd.DataFrame(
            {
                "user_url": [f"u{i}" for i in range(6) for _ in range(2)],
                "topic": ["a", "b", "a", "c", "a", "d", "x", "y", "x", "z", "x", "w"],
            }
        )
        result = homophily(
            graph,
            topics,
            user,
            np.random.default_rng(7),
            n_samples=6,
            n_null_reps=5,
            k_matches=2,
        )
        self.assertEqual(result["n_null_reps"], 5)
        self.assertIn("jaccard_matched_null_ci95", result)
        self.assertIn("layer", result["matching_features"])


class BfsGeneratorTests(unittest.TestCase):
    def test_degree_sequences_are_balanced_without_uniform_stub_inflation(self):
        din, dout = draw_balanced_degree_sequences(
            10_000, 2.3, 2.6, np.random.default_rng(7), base_out=48
        )
        self.assertEqual(int(din.sum()), int(dout.sum()))
        self.assertGreater(np.quantile(din, 0.99), np.quantile(din, 0.50) * 3)


if __name__ == "__main__":
    unittest.main()
