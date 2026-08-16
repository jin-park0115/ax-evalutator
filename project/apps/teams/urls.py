from django.urls import path
from . import views

urlpatterns = [
    path("members/", views.round_team_members, name="round_team_members"),
    path("create/", views.create_team, name="create_team"),
    path("assign/", views.assign_or_move_student, name="assign_or_move_student"),
    path("auto-assign/", views.auto_assign_teams, name="auto_assign_teams"),
    path("confirm/", views.confirm_team_assignment, name="confirm_team_assignment"),  # 추가된 확정 API
]