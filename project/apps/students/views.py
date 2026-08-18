import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

User = get_user_model()


@login_required
def student_home(request):
    from apps.evaluations.models import (
        EvaluationRound,
        IndividualEvaluation,
        ScoreResult,
        TeamEvaluation,
    )

    round_obj = (
        EvaluationRound.objects
        .filter(status=EvaluationRound.Status.IN_PROGRESS)
        .order_by("-id")
        .first()
    )

    if not round_obj:
        state = "before"
    else:
        finalized = (
            TeamEvaluation.objects.filter(
                round=round_obj, submitted_by=request.user, is_final=True
            ).exists()
            or IndividualEvaluation.objects.filter(
                round=round_obj, evaluator=request.user, is_final=True
            ).exists()
        )
        if not finalized:
            state = "open"
        elif ScoreResult.objects.filter(round=round_obj, user=request.user).exists():
            state = "published"
        else:
            state = "done"

    team, members = get_my_team(request.user)

    return render(
        request,
        "student/home.html",
        {
            "state": state,
            "team": team,
        },
    )


@login_required
def student_team(request):
    team, members = get_my_team(request.user)
    return render(request, "student/team.html", {"team": team, "members": members})


@login_required
def student_result(request):
    result = get_visible_result(request.user)
    return render(request, "student/result.html", {"result": result})


def get_my_team(user):
    from apps.teams.models import TeamMember
    from apps.evaluations.models import EvaluationRound

    # 1. 진행 중(IN_PROGRESS)이거나 확정된 회차 가져오기
    active_round = (
        EvaluationRound.objects
        .filter(status=EvaluationRound.Status.IN_PROGRESS)
        .order_by("-id")
        .first()
    )

    # 2. 회차가 없거나, 작성 중(DRAFT) 상태라면 학생에게 팀을 안 보여줌
    if not active_round:
        return None, []

    # 3. 해당 회차에 속한 팀원 정보만 조회
    tm = (
        TeamMember.objects.select_related("team")
        .filter(student=user, team__round=active_round)
        .first()
    )
    
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
    from apps.evaluations.models import EvaluationRound, ScoreResult
    from apps.scoring.services import calculate_team_rankings

    round_obj = (
        EvaluationRound.objects.filter(
            status=EvaluationRound.Status.IN_PROGRESS
        )
        .order_by("-id")
        .first()
        or EvaluationRound.objects.order_by("-id").first()
    )
    if not round_obj:
        return None

    score = ScoreResult.objects.filter(round=round_obj, user=user).first()
    if not score:
        return None

    team_first = None
    team_rankings = None

    if round_obj.team_first_rank_visible or round_obj.team_rank_visible:
        team_rows = (
            ScoreResult.objects.filter(round=round_obj)
            .values("team_id", "team__name", "team_score")
            .distinct()
        )

        team_scores = {}
        team_names = {}
        for row in team_rows:
            team_id = row["team_id"]
            team_scores[team_id] = row["team_score"]
            team_names[team_id] = row["team__name"]

        if team_scores:
            rankings = calculate_team_rankings(team_scores, team_names)

            if round_obj.team_first_rank_visible:
                first_place = next(
                    (item for item in rankings if item[2] == 1),
                    None,
                )
                if first_place:
                    team_first_team_id = first_place[0]
                    team_first = team_names[team_first_team_id]

            if round_obj.team_rank_visible:
                team_rankings = [
                    {
                        "team_name": team_names[team_id],
                        "score": team_score,
                        "rank": rank,
                    }
                    for team_id, team_score, rank in rankings
                ]

    return {
        "team_score": score.team_score if round_obj.team_rank_visible else None,
        "personal_score": score.individual_score if round_obj.individual_score_visible else None,
        "final_score": score.final_score,
        "rank": score.rank if round_obj.individual_rank_visible else None,
        "team_first": team_first,
        "team_rankings": team_rankings,
    }


# ==========================================
# 관리자 전용 수강생 관리 API
# ==========================================

@staff_member_required
@require_http_methods(["GET"])
def student_list(request):
    students = User.objects.filter(role=User.Role.STUDENT).values(
        "id", "username", "email", "date_joined"
    )
    return JsonResponse({"students": list(students)}, status=200)


@staff_member_required
@require_http_methods(["POST", "PUT"])
def update_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    username = data.get("username")
    email = data.get("email")

    if username:
        student.username = username
    if email:
        if User.objects.filter(email=email).exclude(id=student.id).exists():
            return JsonResponse({"error": "이미 사용 중인 이메일입니다."}, status=400)
        student.email = email

    student.save()
    return JsonResponse(
        {"message": f"{student.username} 학생의 정보가 수정되었습니다."},
        status=200,
    )


@staff_member_required
@require_http_methods(["POST", "DELETE"])
def delete_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    student.role = User.Role.PENDING
    student.save()
    
    return JsonResponse(
        {"message": f"{student.username} 학생이 목록에서 삭제되고 승인 대기 상태로 변경되었습니다."},
        status=200,
    )