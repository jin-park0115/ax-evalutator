from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, unique=True)

    def __str__(self) -> str:
        return self.name