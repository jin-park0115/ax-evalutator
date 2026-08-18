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

from apps.evaluations.views_tutor import (
    team_evaluation_form as tutor_team_evaluation_form_view,
    individual_evaluation_form as tutor_individual_evaluation_form_view,
)

from apps.evaluations.views_eval import (
    team_evaluation_list,
    team_evaluation_form,
    peer_evaluation_form,
    submit_team_final,
    submit_individual_final,
)


urlpatterns = [
    path(
        "",
        home,
        name="home",
    ),

    path(
        "student/",
        include("apps.students.urls"),
    ),

    path(
        "",
        include("apps.evaluations.urls"),
    ),

    path(
        "teams/",
        include("apps.teams.urls"),
    ),

    # Tutor
    path(
        "tutor/rounds/",
        round_list,
        name="tutor_rounds",
    ),

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

    path(
        "tutor/settings/",
        tutor_settings,
        name="tutor_settings",
    ),

    path(
        "tutor/evaluation-status/",
        evaluation_status,
        name="tutor_evaluation_status",
    ),

    # 학생 평가
    path(
        "eval/teams/",
        team_evaluation_list,
        name="eval_team_list",
    ),

    path(
        "eval/teams/<int:team_id>/",
        team_evaluation_form,
        name="eval_team_form",
    ),

    path(
        "eval/peer/",
        peer_evaluation_form,
        name="eval_peer_form",
    ),

    # 팀 평가 최종 제출
    path(
        "eval/teams/submit-final/",
        submit_team_final,
        name="eval_submit_team_final",
    ),

    # 개인 평가 최종 제출
    path(
        "eval/peer/submit-final/",
        submit_individual_final,
        name="eval_submit_individual_final",
    ),

    # 로그인
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

    # accounts
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