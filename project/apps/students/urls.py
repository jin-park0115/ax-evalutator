from django.urls import path
from .views import (
    student_home, 
    student_team, 
    student_result,
    student_list,
    update_student,
    delete_student
)

urlpatterns = [
    # 수강생 본인용 페이지 (기존)
    path("", student_home, name="student_home"),
    path("team/", student_team, name="student_team"),
    path("result/", student_result, name="student_result"),
    
    # 관리자용 수강생 관리 API (추가)
    path("manage/", student_list, name="student_list"),
    path("manage/<int:student_id>/update/", update_student, name="update_student"),
    path("manage/<int:student_id>/delete/", delete_student, name="delete_student"),
]