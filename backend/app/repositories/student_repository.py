from app.models.student import Student


def list_students() -> list[Student]:
    return list(Student.objects.order_by("id"))
