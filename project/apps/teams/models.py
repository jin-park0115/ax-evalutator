from django.db import models
from django.conf import settings
from apps.evaluations.models import EvaluationRound


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
        return f"[{getattr(self.round, 'name', self.round_id)}] {self.name}"


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="members")
    # Student 대신 User(AUTH_USER_MODEL) 직접 참조
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "student"],
                name="uq_team_student_once"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.team.name} - {self.student}"