from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def student_home(request):
    # state = get_student_state(request.user)
    state = "before"
    return render(request, "student/home.html", {"state": state})


@login_required
def student_team(request):
    team, members = get_my_team(request.user)
    return render(request, "student/team.html", {"team": team, "members": members})


@login_required
def student_result(request):
    result = get_visible_result(request.user)
    return render(request, "student/result.html", {"result": result})


def get_my_team(user):
    """BE1의 team_service.get_my_team()이 나오면 이 함수만 교체한다."""
    from apps.teams.models import TeamMember

    student = getattr(user, "student", None)
    if not student:
        return None, []

    tm = TeamMember.objects.select_related("team").filter(student=student).first()
    if not tm:
        return None, []

    members = (
        TeamMember.objects
        .filter(team=tm.team)
        .select_related("student")
        .order_by("id")
    )
    return tm.team, members


def get_visible_result(user):
    """BE2의 score_service.get_visible_result()가 나오면 이 함수만 교체한다."""
    return None