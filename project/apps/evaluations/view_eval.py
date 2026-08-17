from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.evaluations.models import (
    EvaluationRound,
    TeamEvaluation,
    IndividualEvaluation,
)
from apps.teams.models import Team, TeamMember


@login_required
def evaluation_home(request):
    """
    학생 평가 메인 화면
    현재 진행 중인 평가 회차를 보여준다.
    """

    rounds = EvaluationRound.objects.filter(
        status=EvaluationRound.Status.IN_PROGRESS
    ).order_by("-id")

    return render(
        request,
        "student/evaluation.html",
        {
            "rounds": rounds,
        },
    )


@login_required
def team_evaluation(request, round_id):
    """
    학생 팀 평가 화면
    """

    round_obj = get_object_or_404(
        EvaluationRound,
        id=round_id,
        status=EvaluationRound.Status.IN_PROGRESS,
    )

    student = request.user

    membership = get_object_or_404(
        TeamMember.objects.select_related("team"),
        student=student,
        team__round=round_obj,
    )

    my_team = membership.team

    teams = (
        Team.objects
        .filter(round=round_obj)
        .exclude(id=my_team.id)
        .order_by("id")
    )

    existing_evaluations = TeamEvaluation.objects.filter(
        round=round_obj,
        evaluator_team=my_team,
        submitted_by=student,
    )

    evaluated_team_ids = set(
        existing_evaluations.values_list(
            "target_team_id",
            flat=True,
        )
    )

    return render(
        request,
        "student/team_evaluation.html",
        {
            "round": round_obj,
            "my_team": my_team,
            "teams": teams,
            "evaluated_team_ids": evaluated_team_ids,
        },
    )


@login_required
def individual_evaluation(request, round_id):
    """
    학생 개인 평가 화면
    """

    round_obj = get_object_or_404(
        EvaluationRound,
        id=round_id,
        status=EvaluationRound.Status.IN_PROGRESS,
    )

    student = request.user

    membership = get_object_or_404(
        TeamMember.objects.select_related("team"),
        student=student,
        team__round=round_obj,
    )

    my_team = membership.team

    members = (
        TeamMember.objects
        .filter(team__round=round_obj)
        .select_related("student", "team")
        .exclude(student_id=student.id)
        .order_by("student__username")
    )

    existing_evaluations = IndividualEvaluation.objects.filter(
        round=round_obj,
        evaluator=student,
    )

    evaluated_student_ids = set(
        existing_evaluations.values_list(
            "target_id",
            flat=True,
        )
    )

    return render(
        request,
        "student/individual_evaluation.html",
        {
            "round": round_obj,
            "my_team": my_team,
            "members": members,
            "evaluated_student_ids": evaluated_student_ids,
        },
    )