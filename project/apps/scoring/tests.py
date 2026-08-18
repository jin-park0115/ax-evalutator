from django.test import SimpleTestCase

from apps.scoring.services import (
    calculate_final_score,
    calculate_team_score,
    calculate_individual_score,
    calculate_rankings,
    calculate_team_rankings,
    calculate_seed_scores,
    calculate_average_excluding_missing,
)


class ScoringServiceTests(SimpleTestCase):

    def test_calculate_final_score(self):
        result = calculate_final_score(
            4.0,
            3.0,
        )

        self.assertEqual(result, 3.4)

    def test_calculate_team_score(self):
        result = calculate_team_score(
            4.0,
            3.0,
            0.6,
            0.4,
        )

        self.assertEqual(result, 3.6)

    def test_calculate_individual_score(self):
        result = calculate_individual_score(
            3.0,
            4.0,
            0.6,
            0.4,
        )

        self.assertEqual(result, 3.4)

    def test_calculate_rankings(self):
        result = calculate_rankings(
            {
                1: 4.0,
                2: 3.5,
                3: 4.5,
            },
            {
                1: "학생1",
                2: "학생2",
                3: "학생3",
            },
        )

        expected = [
            (3, 4.5, 1),
            (1, 4.0, 2),
            (2, 3.5, 3),
        ]

        self.assertEqual(result, expected)

    def test_calculate_rankings_with_tie(self):
        result = calculate_rankings(
            {
                1: 4.5,
                2: 4.5,
                3: 3.5,
            },
            {
                1: "학생1",
                2: "학생2",
                3: "학생3",
            },
        )

        expected = [
            (1, 4.5, 1),
            (2, 4.5, 1),
            (3, 3.5, 3),
        ]

        self.assertEqual(result, expected)

    def test_calculate_team_rankings(self):
        result = calculate_team_rankings(
            {
                1: 4.0,
                2: 3.5,
                3: 4.5,
            },
            {
                1: "1팀",
                2: "2팀",
                3: "3팀",
            },
        )

        expected = [
            (3, 4.5, 1),
            (1, 4.0, 2),
            (2, 3.5, 3),
        ]

        self.assertEqual(result, expected)

    def test_calculate_team_rankings_with_tie(self):
        result = calculate_team_rankings(
            {
                1: 4.5,
                2: 4.5,
                3: 3.5,
            },
            {
                1: "1팀",
                2: "2팀",
                3: "3팀",
            },
        )

        expected = [
            (1, 4.5, 1),
            (2, 4.5, 1),
            (3, 3.5, 3),
        ]

        self.assertEqual(result, expected)

    def test_calculate_seed_scores(self):
        result = calculate_seed_scores(
            [
                {
                    1: 4.0,
                    2: 4.5,
                },
                {
                    1: 4.5,
                    2: 4.0,
                },
            ]
        )

        expected = {
            1: 4.25,
            2: 4.25,
        }

        self.assertEqual(result, expected)

    def test_calculate_average_excluding_missing(self):
        result = calculate_average_excluding_missing(
            [
                4.0,
                None,
                3.0,
            ]
        )

        self.assertEqual(result, 3.5)

    def test_calculate_average_excluding_missing_all_missing(self):
        result = calculate_average_excluding_missing(
            [
                None,
                None,
            ]
        )

        self.assertIsNone(result)

    def test_average_uses_all_scores(self):
        result = calculate_average_excluding_missing(
            [
                5.0,
                4.0,
                3.0,
                2.0,
                1.0,
            ]
        )

        self.assertEqual(result, 3.0)