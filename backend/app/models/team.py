from django.db import models

from app.models.round import Round
from app.models.student import Student


class Team(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name


class TeamMember(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
