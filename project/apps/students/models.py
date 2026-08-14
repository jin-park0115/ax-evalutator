from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, unique=True)

    def __str__(self) -> str:
        return self.name

