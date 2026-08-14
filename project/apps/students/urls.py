from django.urls import path
from .views import student_home, student_team

urlpatterns = [
    path("", student_home, name="student_home"),
    path("team/", student_team, name="student_team"),
]