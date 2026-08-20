from django.urls import path
from . import views

urlpatterns = [
    # 수강생 본인용 페이지
    path("", views.student_home, name="student_home"),
    path("team/", views.student_team, name="student_team"),
    path("result/", views.student_result, name="student_result"),
]