from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("round_id", "evaluator_id", "target_id", name="uq_evaluation_once"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"), nullable=False)
    evaluator_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False)
    score: Mapped[int] = mapped_column(nullable=False)

