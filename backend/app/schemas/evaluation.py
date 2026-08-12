from pydantic import BaseModel, Field


class EvaluationCreate(BaseModel):
    round_id: int
    evaluator_id: int
    target_id: int
    score: int = Field(ge=0, le=100)


class EvaluationRead(EvaluationCreate):
    id: int

