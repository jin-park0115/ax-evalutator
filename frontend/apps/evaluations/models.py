from django.db import models


class EvaluationRound(models.Model):
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="draft")

    def __str__(self) -> str:
        return self.title

