# apps/evaluations/admin.py
from django.contrib import admin
from apps.evaluations.models import EvaluationRound


@admin.register(EvaluationRound)
class EvaluationRoundAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "start_at", "end_at")
    list_filter = ("status",)
    search_fields = ("name",)