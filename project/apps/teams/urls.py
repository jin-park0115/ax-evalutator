from django.urls import path
from . import views

urlpatterns = [
    path("list/", views.team_list_and_members, name="team_list_and_members"),
    path("create/", views.create_team, name="create_team"),
    path("assign/", views.assign_or_move_student, name="assign_or_move_student"),
]