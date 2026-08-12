from django.db import IntegrityError, transaction

from app.models.evaluation import Evaluation


def create_evaluation(
    *,
    round_id: int,
    evaluator_id: int,
    target_id: int,
    score: int,
) -> Evaluation:
    try:
        with transaction.atomic():
            return Evaluation.objects.create(
                round_id=round_id,
                evaluator_id=evaluator_id,
                target_id=target_id,
                score=score,
            )
    except IntegrityError as exc:
        raise ValueError("Evaluation already exists for this evaluator and target.") from exc
