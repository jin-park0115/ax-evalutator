from django.db import models

from apps.evaluations.models import EvaluationRound


class Team(models.Model):
    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name

