from django.db import models

from app.models.round import Round
from app.models.student import Student


class Evaluation(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    evaluator = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="given_evaluations",
    )
    target = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="received_evaluations",
    )
    score = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["round", "evaluator", "target"],
                name="uq_evaluation_once",
            )
        ]
