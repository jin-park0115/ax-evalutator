from django.test import SimpleTestCase

from apps.scoring.services import (
    calculate_final_score,
    calculate_team_score,
    calculate_individual_score,
    calculate_rankings,
    calculate_seed_scores,
    calculate_trimmed_mean,
    calculate_average_excluding_missing,
)


class ScoringServiceTests(SimpleTestCase):

    def test_calculate_final_score(self):
        result = calculate_final_score(80, 90)

        self.assertEqual(result, 86.0)

    def test_calculate_team_score(self):
        result = calculate_team_score(80, 90, 0.4, 0.6)

        self.assertEqual(result, 86.0)

    def test_calculate_individual_score(self):
        result = calculate_individual_score(80, 90, 0.4, 0.6)

        self.assertEqual(result, 86.0)

    def test_calculate_rankings(self):
        result = calculate_rankings(
            {
                1: 90.0,
                2: 80.0,
                3: 95.0,
            },
            {
                1: "김철수",
                2: "이영희",
                3: "박민수",
            },
        )

        expected = [
            (3, 95.0, 1),
            (1, 90.0, 2),
            (2, 80.0, 3),
        ]

        self.assertEqual(result, expected)

    def test_calculate_seed_scores(self):
        result = calculate_seed_scores([
            {1: 80.0, 2: 90.0},
            {1: 90.0, 2: 80.0},
        ])

        expected = {
            1: 85.0,
            2: 85.0,
        }

        self.assertEqual(result, expected)

    def test_calculate_trimmed_mean(self):
        result = calculate_trimmed_mean([10, 20, 30, 40, 100])

        self.assertEqual(result, 30.0)

    def test_calculate_average_excluding_missing(self):
        result = calculate_average_excluding_missing([80.0, None, 90.0])

        self.assertEqual(result, 85.0)