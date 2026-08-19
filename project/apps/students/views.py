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
    from apps.evaluations import services
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

    progress = None

    if not round_obj:
        # 진행 중인 회차가 없다 — 아직 시작 전이거나, 방금 회차가
        # 종료돼서 다음 회차가 아직 작성 중인 경우다. 후자라면 홈
        # 화면이 "아직 시작 안 함"으로 되돌아가지 않고, 방금 끝난
        # 회차의 결과를 계속 보여준다.
        finished_round = (
            EvaluationRound.objects
            .filter(status=EvaluationRound.Status.FINISHED)
            .order_by("-id")
            .first()
        )
        if finished_round and ScoreResult.objects.filter(
            round=finished_round, user=request.user
        ).exists():
            state = "published"
        else:
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
            # 팀 평가/팀원 평가를 각각 몇 명이나 채웠는지 — 홈 화면 배지와
            # "최종 제출" 버튼 노출 여부(둘 다 다 채웠을 때만) 판단에 쓴다.
            progress = services.get_evaluation_progress(request.user, round_obj)
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
            "progress": progress,
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

    # 1. 진행 중(IN_PROGRESS)인 회차를 먼저 찾고, 없으면(방금 종료돼서
    # 다음 회차가 아직 작성 중일 때 등) 가장 최근에 "종료"된 회차를
    # 보여준다 — 그래야 회차가 끝난 직후에도 자기 팀을 계속 볼 수 있다.
    active_round = (
        EvaluationRound.objects
        .filter(status=EvaluationRound.Status.IN_PROGRESS)
        .order_by("-id")
        .first()
        or EvaluationRound.objects
        .filter(status=EvaluationRound.Status.FINISHED)
        .order_by("-id")
        .first()
    )

    # 2. 회차가 없거나, 작성 중(DRAFT)뿐이라면 학생에게 팀을 안 보여줌
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


def _build_round_result(user, round_obj):
    """한 회차에 대한 이 학생의 결과 dict를 만든다. 점수가 없으면
    "미배정"/"집계 전" 중 어떤 상태인지만 담아서 돌려준다."""
    from apps.evaluations.models import ScoreResult
    from apps.scoring.services import calculate_team_rankings

    score = ScoreResult.objects.filter(round=round_obj, user=user).first()
    if not score:
        from apps.teams.models import TeamMember

        # 점수가 없는 이유가 둘 중 뭔지 구분해서 보여준다 —
        # (1) 이 회차에 팀 배정 자체가 안 된 경우("미배정")
        # (2) 팀 배정은 됐지만 아직 점수 집계 전인 경우
        was_assigned = TeamMember.objects.filter(
            team__round=round_obj, student=user
        ).exists()
        return {
            "round_name": round_obj.name,
            "not_participated": not was_assigned,
            "not_calculated": was_assigned,
        }

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
        "round_name": round_obj.name,
        "team_score": score.team_score if round_obj.team_rank_visible else None,
        "personal_score": score.individual_score if round_obj.individual_score_visible else None,
        "final_score": score.final_score,
        "rank": score.rank if round_obj.individual_rank_visible else None,
        "team_first": team_first,
        "team_rankings": team_rankings,
    }


def get_visible_result(user):
    from apps.evaluations.models import EvaluationRound, ScoreResult

    # 진행 중인 회차는 따로 "현재 회차" 카드로 크게 보여주고, 이미
    # 종료된 회차들은 그 아래에 "지난 회차 결과"로 나열한다. 예전에는
    # 진행 중인 회차 하나만 보여줘서, 새 회차가 시작되는 순간 이전에
    # 이미 받은 점수를 학생이 더 이상 볼 수 없는 문제가 있었다.
    current_round = (
        EvaluationRound.objects.filter(status=EvaluationRound.Status.IN_PROGRESS)
        .order_by("-id")
        .first()
    )
    current = _build_round_result(user, current_round) if current_round else None

    history = []
    for round_obj in EvaluationRound.objects.filter(
        status=EvaluationRound.Status.FINISHED
    ).order_by("-id"):
        if ScoreResult.objects.filter(round=round_obj, user=user).exists():
            history.append(_build_round_result(user, round_obj))

    if not current and not history:
        return None

    return {"current": current, "history": history}


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