from django.db import models
from django.conf import settings  # 1. settings 추가


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # 2. User -> settings.AUTH_USER_MODEL 변경
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="student",
    )
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, unique=True)

    def __str__(self) -> str:
        return self.name