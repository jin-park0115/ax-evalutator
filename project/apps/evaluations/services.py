from django.db import IntegrityError, transaction

from apps.evaluations.models import Evaluation


def create_evaluation(
    *,
    round_id: int,
    evaluator_id: int,
    target_id: int,
    score: int,
) -> Evaluation:
    if evaluator_id == target_id:
        raise ValueError("자기 자신은 평가할 수 없습니다.")

    if not (1 <= score <= 5):
        raise ValueError("점수는 1점에서 5점 사이여야 합니다.")

    try:
        with transaction.atomic():
            return Evaluation.objects.create(
                round_id=round_id,
                evaluator_id=evaluator_id,
                target_id=target_id,
                score=score,
            )
    except IntegrityError as exc:
        raise ValueError("Evaluation already exists for this evaluator and target.")