from django.contrib import admin
from .models import (
    Assignment,
    EvaluationRound,
    EvaluationTemplate,
    IndividualEvaluation,
    ScoreResult,
    TeamEvaluation,
    TutorEvaluation,
)


class EvaluationTemplateInline(admin.TabularInline):
    """평가 회차 상세 화면에서 템플릿을 함께 관리하는 인라인"""
    model = EvaluationTemplate
    extra = 0


class AssignmentInline(admin.TabularInline):
    """평가 회차 상세 화면에서 과제를 함께 관리하는 인라인"""
    model = Assignment
    extra = 0


@admin.register(EvaluationRound)
class EvaluationRoundAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "status",
        "start_at",
        "end_at",
        "team_weight",
        "individual_weight",
    )
    list_filter = (
        "status",
        "team_first_rank_visible",
        "team_rank_visible",
        "individual_score_visible",
        "individual_rank_visible",
    )
    search_fields = ("name",)
    inlines = [EvaluationTemplateInline, AssignmentInline]


@admin.register(EvaluationTemplate)
class EvaluationTemplateAdmin(admin.ModelAdmin):
    list_display = ("id", "round", "type")
    list_filter = ("type", "round")
    search_fields = ("round__name",)


@admin.register(TeamEvaluation)
class TeamEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "round",
        "evaluator_team",
        "target_team",
        "submitted_by",
        "score",
        "is_final",
        "created_at",
    )
    list_filter = ("round", "is_final", "created_at")
    search_fields = (
        "evaluator_team__name",
        "target_team__name",
        "submitted_by__username",
        "submitted_by__email",
    )
    readonly_fields = ("created_at",)


@admin.register(IndividualEvaluation)
class IndividualEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "round",
        "team",
        "evaluator",
        "target",
        "score",
        "is_final",
        "created_at",
    )
    list_filter = ("round", "is_final", "created_at")
    search_fields = (
        "team__name",
        "evaluator__username",
        "evaluator__email",
        "target__username",
        "target__email",
    )
    readonly_fields = ("created_at",)


@admin.register(TutorEvaluation)
class TutorEvaluationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "round",
        "evaluator",
        "user",
        "team",
        "score",
        "created_at",
    )
    list_filter = ("round", "created_at")
    search_fields = (
        "evaluator__username",
        "user__username",
        "team__name",
    )
    readonly_fields = ("created_at",)


@admin.register(ScoreResult)
class ScoreResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "round",
        "user",
        "team",
        "team_score",
        "individual_score",
        "final_score",
        "rank",
    )
    list_filter = ("round",)
    search_fields = (
        "user__username",
        "user__email",
        "team__name",
    )
    ordering = ("round", "rank")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "round", "title", "eval_start_at", "eval_end_at")
    list_filter = ("round",)
    search_fields = ("title", "description")