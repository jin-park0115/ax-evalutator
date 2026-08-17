from django.db import models
from apps.evaluations.models import EvaluationRound
from apps.students.models import Student


class Team(models.Model):
    class EvalStatus(models.TextChoices):
        NOT_OPENED = "NOT_OPENED", "평가 미열람"
        OPEN = "OPEN", "평가 진행 중"
        CLOSED = "CLOSED", "평가 종료"

    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=100, verbose_name="팀 이름")
    presentation_order = models.IntegerField(null=True, blank=True, verbose_name="발표 순서")
    eval_status = models.CharField(
        max_length=20,
        choices=EvalStatus.choices,
        default=EvalStatus.NOT_OPENED,
        verbose_name="평가 상태",
    )
    eval_opened_at = models.DateTimeField(null=True, blank=True, verbose_name="평가 시작 일시")
    eval_closed_at = models.DateTimeField(null=True, blank=True, verbose_name="평가 종료 일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성 일시")

    def __str__(self) -> str:
        return f"[{self.round.name}] {self.name}"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="team_memberships")

    class Meta:
        # 1. 한 팀에 동일한 수강생 중복 등록 방지
        # 2. 한 회차 내에서 수강생이 중복으로 다른 팀에 배정되는 것을 DB 레벨에서 차단
        constraints = [
            models.UniqueConstraint(
                fields=["team", "student"],
                name="uq_team_student_once"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.team.name} - {self.student}"