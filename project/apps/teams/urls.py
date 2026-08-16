from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_team, name="create_team"),
    path("assign/", views.assign_or_move_student, name="assign_or_move_student"),
    path("members/", views.round_team_members, name="round_team_members"),
    path("auto-assign/", views.auto_assign_teams, name="auto_assign_teams"),  # 추가
]
