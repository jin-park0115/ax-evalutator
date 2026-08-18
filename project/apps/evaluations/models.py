from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# ==============================================================================
# 기본 5점 척도
# ==============================================================================

SCALE_5_POINT = {
    "min": 1,
    "max": 5,
    "description": {
        "5": "매우 우수 (기대 수준을 명확히 상회한다)",
        "4": "우수 (기대 수준을 충족하고 일부 상회한다)",
        "3": "보통 (기대 수준을 충족한다)",
        "2": "미흡 (일부 항목이 기대 수준에 미달한다)",
        "1": "매우 미흡 (대부분 기대 수준에 미달한다)",
    },
}


# ==============================================================================
# 기본 팀 평가 문항
# ==============================================================================

DEFAULT_TEAM_CRITERIA = [
    {
        "key": "q1",
        "text": "문제 정의와 목표가 명확한가",
    },
    {
        "key": "q2",
        "text": "산출물이 요구사항을 충족하는가",
    },
    {
        "key": "q3",
        "text": "기술적 완성도가 충분한가",
    },
    {
        "key": "q4",
        "text": "발표 구성과 전달이 명확한가",
    },
    {
        "key": "q5",
        "text": "질의응답에 적절히 대응했는가",
    },
]


# ==============================================================================
# 기본 개인 평가 문항
# ==============================================================================

DEFAULT_INDIVIDUAL_CRITERIA = [
    {
        "key": "q1",
        "text": "맡은 역할을 책임감 있게 수행했는가",
    },
    {
        "key": "q2",
        "text": "일정과 약속을 지켰는가",
    },
    {
        "key": "q3",
        "text": "의사소통이 원활했는가",
    },
    {
        "key": "q4",
        "text": "문제 상황에 적극적으로 기여했는가",
    },
    {
        "key": "q5",
        "text": "협업 태도가 팀에 긍정적이었는가",
    },
]


# ==============================================================================
# 평가 회차
# ==============================================================================

class EvaluationRound(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "작성 중"
        READY = "ready", "대기"
        IN_PROGRESS = "in_progress", "진행 중"
        FINISHED = "finished", "종료"

    name = models.CharField(
        max_length=100,
        verbose_name="평가 회차 이름",
    )

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

    # ==========================================================================
    # 팀 / 개인 성적 비율
    #
    # 팀 40% + 개인 60% 고정
    # ==========================================================================

    team_weight = models.FloatField(
        default=0.4,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0),
        ],
        verbose_name="팀 성적 비율",
    )

    individual_weight = models.FloatField(
        default=0.6,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0),
        ],
        verbose_name="개인 성적 비율",
    )

    # ==========================================================================
    # 학생 / 튜터 평가 비율
    #
    # 회차별로 튜터가 설정
    # 예: 학생 70% + 튜터 30%
    # ==========================================================================

    student_weight = models.FloatField(
        default=0.5,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0),
        ],
        verbose_name="학생 평가 비율",
    )

    tutor_weight = models.FloatField(
        default=0.5,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0),
        ],
        verbose_name="튜터 평가 비율",
    )

    # ==========================================================================
    # 결과 공개 설정
    # ==========================================================================

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

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        super().clean()

        # 팀 40% + 개인 60% 고정
        if self.team_weight != 0.4:
            raise ValidationError(
                "팀 성적 비율은 40%로 고정입니다."
            )

        if self.individual_weight != 0.6:
            raise ValidationError(
                "개인 성적 비율은 60%로 고정입니다."
            )

        # 학생 + 튜터 = 100%
        if round(self.student_weight + self.tutor_weight, 6) != 1.0:
            raise ValidationError(
                "학생 평가 비율과 튜터 평가 비율의 합은 100%여야 합니다."
            )

    def __str__(self):
        return self.name


# ==============================================================================
# 기존 기본 평가 모델
#
# 주의:
# 현재 프로젝트의 기존 코드와 연결되어 있을 수 있으므로
# 일단 유지한다.
# ==============================================================================

class Evaluation(models.Model):

    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="legacy_evaluations",
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

    score = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name="평가 점수",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "round",
                    "evaluator",
                    "target",
                ],
                name="uq_evaluation_once",
            )
        ]

    def clean(self):
        super().clean()

        if self.evaluator_id == self.target_id:
            raise ValidationError(
                "자기 자신을 평가할 수 없습니다."
            )


# ==============================================================================
# 평가 문항 템플릿
# ==============================================================================

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
        default=list,
        blank=True,
        verbose_name="평가 문항 목록",
    )

    def save(self, *args, **kwargs):

        # 문항이 비어 있으면 기본 문항 자동 등록
        if not self.criteria:

            if self.type == self.TemplateType.TEAM:
                self.criteria = DEFAULT_TEAM_CRITERIA

            elif self.type == self.TemplateType.INDIVIDUAL:
                self.criteria = DEFAULT_INDIVIDUAL_CRITERIA

            elif self.type == self.TemplateType.TUTOR:
                self.criteria = DEFAULT_TEAM_CRITERIA

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"[{self.round.name}] "
            f"{self.get_type_display()} 템플릿"
        )


# ==============================================================================
# 학생 팀 평가
# ==============================================================================

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
        verbose_name="평가자 팀",
    )

    target_team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="received_team_evaluations",
        verbose_name="평가 대상 팀",
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_team_evaluations",
        verbose_name="평가 제출자",
    )

    # ==========================================================================
    # 점수
    #
    # 1~5점 척도 그대로 저장
    # 예: 4.2 / 3.7 / 4.5
    # ==========================================================================

    score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="평균 평가 점수",
    )

    # ==========================================================================
    # 문항별 점수 + 서술 의견
    # ==========================================================================

    responses = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="문항별 점수 및 서술 의견",
    )

    # ==========================================================================
    # 최종 제출 여부
    #
    # False → 계속 수정 가능
    # True → 수정 불가
    # ==========================================================================

    is_final = models.BooleanField(
        default=False,
        verbose_name="최종 제출 여부",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self):
        super().clean()

        # 자기 팀 평가 방지
        if (
            self.evaluator_team_id is not None
            and self.target_team_id is not None
            and self.evaluator_team_id == self.target_team_id
        ):
            raise ValidationError(
                "자기 팀을 평가할 수 없습니다."
            )

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

    def __str__(self):
        return (
            f"{self.evaluator_team} → "
            f"{self.target_team} "
            f"({self.score})"
        )


# ==============================================================================
# 학생 개인 평가
# ==============================================================================

class IndividualEvaluation(models.Model):

    round = models.ForeignKey(
        EvaluationRound,
        on_delete=models.CASCADE,
        related_name="individual_evaluations",
    )

    # 평가 대상 학생이 속한 팀
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="individual_evaluations",
        verbose_name="평가 대상 팀",
    )

    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="given_individual_evaluations",
        verbose_name="평가자",
    )

    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_individual_evaluations",
        verbose_name="평가 대상자",
    )

    # 1~5점 척도
    score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="평균 평가 점수",
    )

    # 문항별 점수 + 서술 의견
    responses = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="문항별 점수 및 서술 의견",
    )

    # 최종 제출 여부
    is_final = models.BooleanField(
        default=False,
        verbose_name="최종 제출 여부",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self):
        super().clean()

        if self.evaluator_id == self.target_id:
            raise ValidationError(
                "자기 자신을 평가할 수 없습니다."
            )

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

    def __str__(self):
        return (
            f"{self.evaluator} → "
            f"{self.target} "
            f"({self.score})"
        )


# ==============================================================================
# 튜터 평가
# ==============================================================================

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
        verbose_name="평가 튜터",
    )

    # 개인 평가 대상
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutor_evaluations_as_target",
        verbose_name="개인 평가 대상자",
    )

    # 팀 평가 대상
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tutor_evaluations_as_target",
        verbose_name="팀 평가 대상",
    )

    # 1~5점 척도
    score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="평균 평가 점수",
    )

    # 문항별 점수 + 서술 의견
    responses = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="문항별 점수 및 서술 의견",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self):
        super().clean()

        # 팀 평가와 개인 평가 중 하나의 대상만 가져야 함
        if self.user_id is not None and self.team_id is not None:
            raise ValidationError(
                "튜터 평가의 대상은 팀 또는 개인 중 하나만 지정해야 합니다."
            )

        if self.user_id is None and self.team_id is None:
            raise ValidationError(
                "튜터 평가의 대상 팀 또는 개인을 지정해야 합니다."
            )

    def __str__(self):

        if self.team_id:
            return (
                f"{self.evaluator} → "
                f"{self.team} "
                f"({self.score})"
            )

        return (
            f"{self.evaluator} → "
            f"{self.user} "
            f"({self.score})"
        )


# ==============================================================================
# 최종 성적 결과
# ==============================================================================

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
        verbose_name="학생",
    )

    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="score_results",
        verbose_name="소속 팀",
    )

    # 1~5점 척도
    team_score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="최종 팀 평가점수",
    )

    # 1~5점 척도
    individual_score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="최종 개인 평가점수",
    )

    # 팀 40% + 개인 60%
    # 역시 1~5점 척도
    final_score = models.FloatField(
        validators=[
            MinValueValidator(1.0),
            MaxValueValidator(5.0),
        ],
        verbose_name="최종 합산점수",
    )

    rank = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="석차",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "round",
                    "user",
                ],
                name="uq_score_result_round_user",
            )
        ]

    def __str__(self):
        return (
            f"{self.user} - "
            f"{self.final_score}점 "
            f"({self.rank}위)"
        )


# ==============================================================================
# 과제
# ==============================================================================

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

    def __str__(self):
        return self.title