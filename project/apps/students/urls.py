from django.urls import path
from .views import student_home, student_team, student_result

urlpatterns = [
    path("", student_home, name="student_home"),
    path("team/", student_team, name="student_team"),
    path("result/", student_result, name="student_result"),
]