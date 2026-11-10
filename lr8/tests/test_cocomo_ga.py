import unittest

from cocomo_ga import absolute_error_rms, cocomo_effort, fit_genetic_algorithm


class CocomoGaTests(unittest.TestCase):
    def test_rms_absolute_error_matches_euclidean_metric_definition(self):
        self.assertAlmostEqual(absolute_error_rms([3.0, 4.0], [0.0, 0.0]), (12.5) ** 0.5)

    def test_cocomo_model_is_a_times_kloc_to_b(self):
        self.assertAlmostEqual(cocomo_effort(2.0, 3.0, 1.0), 6.0)

    def test_fit_is_reproducible_and_respects_parameter_bounds(self):
        kwargs = dict(population_size=12, generations=8, seed=22)
        first = fit_genetic_algorithm([1.0, 2.0, 3.0], [3.0, 5.0, 7.0], **kwargs)
        second = fit_genetic_algorithm([1.0, 2.0, 3.0], [3.0, 5.0, 7.0], **kwargs)
        self.assertEqual((first.a, first.b, first.error), (second.a, second.b, second.error))
        self.assertGreaterEqual(first.a, 0.05)
        self.assertLessEqual(first.a, 20.0)
        self.assertGreaterEqual(first.b, 0.1)
        self.assertLessEqual(first.b, 2.5)
        self.assertGreaterEqual(first.error, 0.0)


if __name__ == '__main__':
    unittest.main()
