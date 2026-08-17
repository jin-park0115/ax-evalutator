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
    start_at = models.DateTimeField(null=True, blank=True, verbose_name="회차 시작 일시")
    end_at = models.DateTimeField(null=True, blank=True, verbose_name="회차 종료 일시")

    # 성적 비율 (팀 40%, 개인 60% 고정 / 학생-튜터 설정 비율)
    team_weight = models.FloatField(default=0.4, verbose_name="팀 성적 비율")
    individual_weight = models.FloatField(default=0.6, verbose_name="개인 성적 비율")
    student_weight = models.FloatField(default=0.5, verbose_name="학생 평가 비율")
    tutor_weight = models.FloatField(default=0.5, verbose_name="튜터 평가 비율")

    # 공개 여부 (기본값 False/비공개)
    team_first_rank_visible = models.BooleanField(
        default=False, verbose_name="팀 1위 공개 여부"
    )
    team_rank_visible = models.BooleanField(
        default=False, verbose_name="전체 팀 순위 공개 여부"
    )
    individual_score_visible = models.BooleanField(
        default=False, verbose_name="개인 점수 공개 여부"
    )
    individual_rank_visible = models.BooleanField(
        default=False, verbose_name="개인 전체 석차 공개 여부"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Evaluation(models.Model):
    round = models.ForeignKey(EvaluationRound, on_delete=models.CASCADE)
    
    # Student -> settings.AUTH_USER_MODEL로 변경
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