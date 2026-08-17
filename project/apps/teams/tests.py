from django.test import TestCase

from apps.accounts.models import User
from apps.evaluations.models import EvaluationRound
from apps.teams.models import Team, TeamMember, TeamUserScoreSeed
from apps.teams.services import assign_seed_based_teams


class AssignSeedBasedTeamsTest(TestCase):
    def setUp(self):
        # 이전 평가 회차
        self.previous_round = EvaluationRound.objects.create(
            name="이전 평가 회차"
        )

        # 현재 평가 회차
        self.current_round = EvaluationRound.objects.create(
            name="현재 평가 회차"
        )

        # 이전 회차의 팀
        self.previous_team = Team.objects.create(
            round=self.previous_round,
            name="이전 1팀",
        )

        # 현재 회차의 팀
        self.teams = [
            Team.objects.create(
                round=self.current_round,
                name="1팀",
            ),
            Team.objects.create(
                round=self.current_round,
                name="2팀",
            ),
        ]

        # 테스트용 학생 6명 생성
        self.students = []

        for i in range(1, 7):
            student = User.objects.create_user(
                email=f"student{i}@test.com",
                username=f"student{i}",
                password="test1234",
                role=User.Role.STUDENT,
                is_active=True,
            )

            self.students.append(student)

            # Seed는 현재 회차가 아닌 이전 회차에 저장
            TeamUserScoreSeed.objects.create(
                user=student,
                round=self.previous_round,
                team=self.previous_team,
                cumulative_seed=float(100 - i),
            )

        # 테스트에서 만든 학생 외의 기존 학생은 제외
        self.test_student_ids = {
            student.id for student in self.students
        }

        self.other_student_ids = list(
            User.objects.filter(
                role=User.Role.STUDENT,
                is_active=True,
            )
            .exclude(id__in=self.test_student_ids)
            .values_list("id", flat=True)
        )

    def test_assign_seed_based_teams_assigns_all_students(self):
        assign_seed_based_teams(
            target_round=self.current_round,
            num_teams=2,
            excluded_student_ids=self.other_student_ids,
        )

        assigned_student_ids = set(
            TeamMember.objects.filter(
                team__round=self.current_round
            ).values_list("student_id", flat=True)
        )

        expected_student_ids = {
            student.id for student in self.students
        }

        self.assertEqual(
            assigned_student_ids,
            expected_student_ids,
        )

    def test_assign_seed_based_teams_creates_requested_team_count(self):
        assign_seed_based_teams(
            target_round=self.current_round,
            num_teams=3,
            excluded_student_ids=self.other_student_ids,
        )

        team_count = Team.objects.filter(
            round=self.current_round
        ).count()

        self.assertEqual(team_count, 3)

    def test_excluded_students_are_not_assigned(self):
        excluded_student = self.students[0]

        assign_seed_based_teams(
            target_round=self.current_round,
            num_teams=2,
            excluded_student_ids=[
                excluded_student.id,
                *self.other_student_ids,
            ],
        )

        assigned_student_ids = set(
            TeamMember.objects.filter(
                team__round=self.current_round
            ).values_list("student_id", flat=True)
        )

        self.assertNotIn(
            excluded_student.id,
            assigned_student_ids,
        )