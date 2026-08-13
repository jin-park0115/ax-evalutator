from django.db import models


class Round(models.Model):
    title = models.CharField(max_length=100)
    status = models.CharField(max_length=30, default="draft")

    def __str__(self) -> str:
        return self.title
