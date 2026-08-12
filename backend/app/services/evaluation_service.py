from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.evaluation import Evaluation


def create_evaluation(
    db: Session,
    *,
    round_id: int,
    evaluator_id: int,
    target_id: int,
    score: int,
) -> Evaluation:
    evaluation = Evaluation(
        round_id=round_id,
        evaluator_id=evaluator_id,
        target_id=target_id,
        score=score,
    )
    db.add(evaluation)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Evaluation already exists for this evaluator and target.") from exc
    db.refresh(evaluation)
    return evaluation

