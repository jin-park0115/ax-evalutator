from django.db import models

from apps.students.models import Student


class EvaluationRound(models.Model):
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="draft")

    def __str__(self) -> str:
        return self.title


class Evaluation(models.Model):
    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE)

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

