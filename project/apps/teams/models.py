from django.db import models

from apps.evaluations.models import EvaluationRound
from apps.students.models import Student


class Team(models.Model):
    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        # 한 팀에 동일한 수강생이 중복 등록되지 않도록 설정
        unique_together = ("team", "student")

    def __str__(self) -> str:
        return f"{self.team.name} - {self.student}"

