from sqlalchemy.orm import Session

from app.models.student import Student


def list_students(db: Session) -> list[Student]:
    return list(db.query(Student).order_by(Student.id).all())

