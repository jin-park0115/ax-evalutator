from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from apps.accounts.views import home

from apps.evaluations.views_tutor import (
    round_list,
    team_build,
    open_team_presentation,
    team_evaluation,
    individual_evaluation,
    template_list,
    template_create,
    tutor_settings,
    evaluation_status,
)

# Tutor 평가 폼
from apps.evaluations.views_tutor import (
    team_evaluation_form as tutor_team_evaluation_form_view,
    individual_evaluation_form as tutor_individual_evaluation_form_view,
)

# 학생 평가
from apps.evaluations.views_eval import (
    team_evaluation_list,
    team_evaluation_form,
    peer_evaluation_form,
    submit_final,
)


urlpatterns = [
    # =========================================================
    # 메인
    # =========================================================
    path(
        "",
        home,
        name="home",
    ),

    # =========================================================
    # 학생
    # =========================================================
    path(
        "student/",
        include("apps.students.urls"),
    ),

    # =========================================================
    # 학생 평가 관련
    # =========================================================
    path(
        "",
        include("apps.evaluations.urls"),
    ),

    # =========================================================
    # 팀 구성 API
    # round_team_members / create_team /
    # assign_or_move_student / auto_assign_teams /
    # confirm_team_assignment
    # =========================================================
    path(
        "teams/",
        include("apps.teams.urls"),
    ),

    # =========================================================
    # Tutor
    # =========================================================

    # 회차 관리
    path(
        "tutor/rounds/",
        round_list,
        name="tutor_rounds",
    ),

    # 팀 구성
    path(
        "tutor/team-build/",
        team_build,
        name="tutor_team_build",
    ),
    path(
        "tutor/teams/<int:team_id>/open/",
        open_team_presentation,
        name="open_team_presentation",
    ),

    # 팀 평가
    path(
        "tutor/team-evaluation/",
        team_evaluation,
        name="tutor_team_evaluation",
    ),
    path(
        "tutor/team-evaluation/<int:team_id>/",
        tutor_team_evaluation_form_view,
        name="tutor_team_evaluation_form",
    ),

    # 개인 평가
    path(
        "tutor/individual-evaluation/",
        individual_evaluation,
        name="tutor_individual_evaluation",
    ),
    path(
        "tutor/individual-evaluation/<int:student_id>/",
        tutor_individual_evaluation_form_view,
        name="tutor_individual_evaluation_form",
    ),

    # 평가 문항 템플릿
    path(
        "tutor/templates/",
        template_list,
        name="tutor_templates",
    ),
    path(
        "tutor/templates/new/",
        template_create,
        name="tutor_template_create",
    ),

    # 공개 설정
    path(
        "tutor/settings/",
        tutor_settings,
        name="tutor_settings",
    ),

    # 평가 현황
    path(
        "tutor/evaluation-status/",
        evaluation_status,
        name="tutor_evaluation_status",
    ),

    # =========================================================
    # 학생 평가
    # =========================================================

    # 팀 평가 목록
    path(
        "eval/teams/",
        team_evaluation_list,
        name="eval_team_list",
    ),

    # 특정 팀 평가
    path(
        "eval/teams/<int:team_id>/",
        team_evaluation_form,
        name="eval_team_form",
    ),

    # 개인 평가
    path(
        "eval/peer/",
        peer_evaluation_form,
        name="eval_peer_form",
    ),

    # 최종 제출
    path(
        "eval/submit-final/",
        submit_final,
        name="eval_submit_final",
    ),

    # =========================================================
    # 로그인 / 로그아웃
    # =========================================================

    # 커스텀 로그인
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login",
    ),

    # 로그아웃
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # 커스텀 accounts
    path(
        "accounts/",
        include("apps.accounts.urls"),
    ),

    # allauth
    path(
        "accounts/",
        include("allauth.urls"),
    ),

    # 관리자
    path(
        "admin/",
        admin.site.urls,
    ),
]