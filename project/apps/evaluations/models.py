from django.conf import settings
from django.db import models


class EvaluationRound(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "작성 중"
        READY = "ready", "대기"
        IN_PROGRESS = "in_progress", "진행 중"
        FINISHED = "finished", "종료"

    # 명세서 필드
    name = models.CharField(max_length=100, verbose_name="평가 회차 이름")
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="회차 전체 상태",
    )
    start_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="회차 시작 일시",
    )
    end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="회차 종료 일시",
    )

    # 성적 비율
    # 팀 40%, 개인 60% 고정
    # 학생 평가 / 튜터 평가 비율은 회차별 설정
    team_weight = models.FloatField(
        default=0.4,
        verbose_name="팀 성적 비율",
    )
    individual_weight = models.FloatField(
        default=0.6,
        verbose_name="개인 성적 비율",
    )
    student_weight = models.FloatField(
        default=0.5,
        verbose_name="학생 평가 비율",
    )
    tutor_weight = models.FloatField(
        default=0.5,
        verbose_name="튜터 평가 비율",
    )

    # 공개 여부
    team_first_rank_visible = models.BooleanField(
        default=False,
        verbose_name="팀 1위 공개 여부",
    )
    team_rank_visible = models.BooleanField(
        default=False,
        verbose_name="전체 팀 순위 공개 여부",
    )
    individual_score_visible = models.BooleanField(
        default=False,
        verbose_name="개인 점수 공개 여부",
    )
    individual_rank_visible = models.BooleanField(
        default=False,
        verbose_name="개인 전체 석차 공개 여부",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Evaluation(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
    )

    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_evaluations",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
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


# 1. 평가 템플릿
class EvaluationTemplate(models.Model):
    class TemplateType(models.TextChoices):
        TEAM = "TEAM", "팀 평가"
        INDIVIDUAL = "INDIVIDUAL", "개인 평가"
        TUTOR = "TUTOR", "튜터 평가"

    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="templates",
    )
    type = models.CharField(
        max_length=20,
        choices=TemplateType.choices,
        verbose_name="템플릿 유형",
    )
    criteria = models.JSONField(
        default=dict,
        verbose_name="문항 목록 (JSON)",
    )

    def __str__(self):
        return f"[{self.round.name}] {self.get_type_display()} 템플릿"


# 2. 팀 평가
class TeamEvaluation(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="team_evaluations",
    )
    evaluator_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="given_team_evaluations",
    )
    target_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="received_team_evaluations",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_team_evaluations",
    )
    score = models.FloatField(
        verbose_name="계산 점수",
    )
    responses = models.JSONField(
        default=dict,
        verbose_name="문항별 점수 및 서술 의견",
    )
    is_final = models.BooleanField(
        default=False,
        verbose_name="최종 제출 여부",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "round",
                    "evaluator_team",
                    "target_team",
                    "submitted_by",
                ],
                name="uq_team_evaluation_once",
            )
        ]


# 3. 개인 평가
class IndividualEvaluation(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="individual_evaluations",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="individual_evaluations",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_individual_evaluations",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_individual_evaluations",
    )
    score = models.FloatField(
        verbose_name="계산 점수",
    )
    responses = models.JSONField(
        default=dict,
        verbose_name="문항별 점수 및 서술 의견",
    )
    is_final = models.BooleanField(
        default=False,
        verbose_name="최종 제출 여부",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "round",
                    "evaluator",
                    "target",
                ],
                name="uq_individual_evaluation_once",
            )
        ]


# 4. 튜터 평가
class TutorEvaluation(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="tutor_evaluations",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_tutor_evaluations",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutor_evaluations_as_target",
        verbose_name="개인 평가 대상자",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutor_evaluations_as_target",
        verbose_name="팀 평가 대상",
    )
    score = models.FloatField(
        verbose_name="계산 점수",
    )
    responses = models.JSONField(
        default=dict,
        verbose_name="문항별 점수 및 서술 의견",
    )
    created_at = models.DateTimeField(auto_now_add=True)


# 5. 최종 성적 결과
class ScoreResult(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="score_results",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="score_results",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="score_results",
    )
    team_score = models.FloatField(
        verbose_name="최종 팀 평가점수",
    )
    individual_score = models.FloatField(
        verbose_name="최종 개인 평가점수",
    )
    final_score = models.FloatField(
        verbose_name="최종 합산점수",
    )
    rank = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="석차",
    )


# 6. 과제
class Assignment(models.Model):
    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="과제 제목",
    )
    description = models.TextField(
        blank=True,
        verbose_name="과제 설명",
    )
    eval_start_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="평가 시작 일시",
    )
    eval_end_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="평가 종료 일시",
    )