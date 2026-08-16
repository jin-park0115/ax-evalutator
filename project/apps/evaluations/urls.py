# apps/evaluations/urls.py
from django.urls import path
from . import views_tutor

urlpatterns = [
    path("tutor/rounds/", views_tutor.round_list, name="tutor_rounds"),
    path("tutor/rounds/<int:round_id>/status/", views_tutor.update_round_status, name="update_round_status"),
    path("tutor/rounds/<int:round_id>/toggle-first-rank/", views_tutor.toggle_team_first_rank, name="toggle_team_first_rank"),
]