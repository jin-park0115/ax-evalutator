from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from apps.accounts.views import home

from apps.evaluations.views_tutor import (
    round_list,
    team_build,
    team_evaluation,
    individual_evaluation,
    template_list,
    template_create,
    tutor_settings,
    evaluation_status,
)


urlpatterns = [
    # 메인
    path(
        "",
        home,
        name="home",
    ),

    # 학생
    path(
        "student/",
        include("apps.students.urls"),
    ),

    # 학생 평가
    path(
        "",
        include("apps.evaluations.urls"),
    ),

    # 팀 편성 API
    # round_team_members / create_team /
    # assign_or_move_student / auto_assign_teams /
    # confirm_team_assignment
    path(
        "teams/",
        include("apps.teams.urls"),
    ),

    # =========================
    # Tutor / FE2
    # =========================

    # 회차 관리
    path(
        "tutor/rounds/",
        round_list,
        name="tutor_rounds",
    ),

    # 팀 편성
    path(
        "tutor/team-build/",
        team_build,
        name="tutor_team_build",
    ),

    # 팀 평가
    path(
        "tutor/team-evaluation/",
        team_evaluation,
        name="tutor_team_evaluation",
    ),

    # 개인 평가
    path(
        "tutor/individual-evaluation/",
        individual_evaluation,
        name="tutor_individual_evaluation",
    ),

    # 템플릿
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

    # =========================
    # 로그인 / 로그아웃 & 소셜 로그인
    # =========================

    # 커스텀 로그인 경로를 allauth보다 위에 배치
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html"
        ),
        name="login",
    ),

    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # 커스텀 accounts 앱
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