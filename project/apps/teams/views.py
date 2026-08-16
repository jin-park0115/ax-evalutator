import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from apps.evaluations.models import EvaluationRound
from apps.students.models import Student
from .models import Team, TeamMember


# 1. 회차 선택 시 해당 회차의 모든 팀 및 팀원 목록 일괄 조회
@staff_member_required
@require_http_methods(["GET"])
def round_team_members(request):
    round_id = request.GET.get("round_id")

    # round_id가 선택되지 않은 경우 기본값으로 가장 최신 회차 사용
    if not round_id:
        latest_round = EvaluationRound.objects.order_by("-id").first()
        if not latest_round:
            return JsonResponse({"round_id": None, "teams": []}, status=200)
        round_id = latest_round.id

    # 선택된 회차의 전체 팀 목록 및 소속 수강생(팀원) 한 번에 조회
    teams = (
        Team.objects.filter(round_id=round_id)
        .prefetch_related("members__student")
        .order_by("id")
    )

    teams_data = []
    for team in teams:
        members_data = [
            {
                "student_id": tm.student.id,
                "name": getattr(tm.student, "name", str(tm.student)),
            }
            for tm in team.members.all()
        ]
        teams_data.append(
            {
                "team_id": team.id,
                "team_name": team.name,
                "presentation_order": team.presentation_order,
                "eval_status": team.eval_status,
                "members": members_data,
            }
        )

    return JsonResponse({"round_id": int(round_id), "teams": teams_data}, status=200)


# 2. 팀 생성 (기존 유지)
@staff_member_required
@require_http_methods(["POST"])
def create_team(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    round_id = data.get("round_id")
    team_name = data.get("name")

    if not round_id or not team_name:
        return JsonResponse({"error": "round_id와 team_name은 필수입니다."}, status=400)

    target_round = get_object_or_404(EvaluationRound, id=round_id)
    team = Team.objects.create(round=target_round, name=team_name)

    return JsonResponse(
        {"message": f"'{team.name}' 팀이 생성되었습니다.", "team_id": team.id},
        status=201,
    )


# 3. 수강생 팀 수동 배정 및 이동 (기존 유지)
@staff_member_required
@require_http_methods(["POST"])
def assign_or_move_student(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    student_id = data.get("student_id")
    target_team_id = data.get("team_id")

    if not student_id or not target_team_id:
        return JsonResponse({"error": "student_id와 team_id는 필수입니다."}, status=400)

    student = get_object_or_404(Student, id=student_id)
    target_team = get_object_or_404(Team, id=target_team_id)
    target_round = target_team.round

    with transaction.atomic():
        # 해당 회차 내에 이미 수강생이 다른 팀에 배정되어 있다면 기존 팀에서 제거 후 이동
        existing_membership = TeamMember.objects.filter(
            team__round=target_round, student=student
        ).first()

        if existing_membership:
            if existing_membership.team_id == target_team.id:
                return JsonResponse({"message": "이미 해당 팀에 소속되어 있습니다."}, status=200)
            existing_membership.delete()

        TeamMember.objects.create(team=target_team, student=student)

    return JsonResponse(
        {"message": f"{student} 수강생이 '{target_team.name}' 팀으로 배정되었습니다."},
        status=200,
    )