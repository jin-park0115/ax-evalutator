from django.urls import path

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
    path(
        "tutor/rounds/<int:round_id>/calculate/",
        views_tutor.calculate_round_scores,
        name="calculate_round_scores",
    ),
    path(
        "tutor/rounds/<int:round_id>/delete/",
        views_tutor.delete_round,
        name="delete_round",
    ),
    path(
        "tutor/rounds/<int:round_id>/unlock-formation/",
        views_tutor.unlock_round_formation,
        name="unlock_round_formation",
    ),

    # 학생 평가 경로(/student/evaluation/*)는 views_eval.py의 /eval/* 플로우로
    # 일원화하면서 제거했다 (2026-08-18, 전예진/안형준 합의).
]