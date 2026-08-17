from django.urls import path

from . import view_eval
from . import views_tutor


urlpatterns = [
    # =========================
    # 튜터
    # =========================
    path(
        "tutor/rounds/",
        views_tutor.round_list,
        name="tutor_rounds",
    ),
    path(
        "tutor/rounds/<int:round_id>/status/",
        views_tutor.update_round_status,
        name="update_round_status",
    ),
    path(
        "tutor/rounds/<int:round_id>/toggle-first-rank/",
        views_tutor.toggle_team_first_rank,
        name="toggle_team_first_rank",
    ),

    # =========================
    # 학생 평가
    # =========================
    path(
        "student/evaluation/",
        view_eval.evaluation_home,
        name="evaluation_home",
    ),
    path(
        "student/evaluation/<int:round_id>/team/",
        view_eval.team_evaluation,
        name="team_evaluation",
    ),
    path(
        "student/evaluation/<int:round_id>/individual/",
        view_eval.individual_evaluation,
        name="individual_evaluation",
    ),
]