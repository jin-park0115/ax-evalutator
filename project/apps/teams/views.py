import json
import random
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

from apps.evaluations.models import EvaluationRound
from apps.students.models import Student
from .models import Team, TeamMember


# 헬퍼 함수: 팀 수 미입력 시 4~5명 위주로 최적의 팀 수 계산
def calculate_optimal_team_count(total_students):
    if total_students <= 0:
        return 0
    if total_students <= 5:
        return 1

    # 4.5명 기준으로 나누어 4~5명 위주 배정
    best_team_count = round(total_students / 4.5)

    # 3~5명 범위를 벗어나지 않도록 보정
    while best_team_count > 1 and (total_students / best_team_count) < 3:
        best_team_count -= 1
    while (total_students / best_team_count) > 5:
        best_team_count += 1

    return max(1, best_team_count)


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


# 2. 팀 생성
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


# 3. 수강생 팀 수동 배정 및 이동
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


# 4. 랜덤 팀 자동 편성 (수동 고정 수강생 유지)
@staff_member_required
@require_http_methods(["POST"])
def auto_assign_teams(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    round_id = data.get("round_id")
    team_count = data.get("team_count")

    if not round_id:
        return JsonResponse({"error": "round_id는 필수입니다."}, status=400)

    target_round = get_object_or_404(EvaluationRound, id=round_id)
    all_students = list(Student.objects.all())
    total_students_count = len(all_students)

    if total_students_count == 0:
        return JsonResponse({"error": "등록된 수강생이 없습니다."}, status=400)

    # 1) 팀 수 결정 (팀 수 미지정 시 4~5명 위주 최적 계산)
    if team_count:
        num_teams = int(team_count)
    else:
        num_teams = calculate_optimal_team_count(total_students_count)

    with transaction.atomic():
        # 2) 해당 회차의 팀 객체 맞춤 조정 (생성 또는 초과분 삭제)
        existing_teams = list(Team.objects.filter(round=target_round).order_by("id"))

        if len(existing_teams) < num_teams:
            for i in range(len(existing_teams) + 1, num_teams + 1):
                new_team = Team.objects.create(round=target_round, name=f"{i}팀")
                existing_teams.append(new_team)
        elif len(existing_teams) > num_teams:
            for team_to_delete in existing_teams[num_teams:]:
                team_to_delete.delete()
            existing_teams = existing_teams[:num_teams]

        # 3) 고정된 수강생 파악
        assigned_memberships = TeamMember.objects.filter(
            team__round=target_round
        ).select_related("student")

        assigned_student_ids = set()
        team_member_counts = {team.id: 0 for team in existing_teams}

        for membership in assigned_memberships:
            if membership.team_id in team_member_counts:
                assigned_student_ids.add(membership.student.id)
                team_member_counts[membership.team_id] += 1

        # 4) 미배정 수강생 무작위 셔플 후 인원수가 가장 적은 팀에 배치 (오차 범위 1명)
        unassigned_students = [
            s for s in all_students if s.id not in assigned_student_ids
        ]
        random.shuffle(unassigned_students)

        for student in unassigned_students:
            min_count = min(team_member_counts.values())
            candidate_teams = [
                t_id for t_id, count in team_member_counts.items() if count == min_count
            ]
            selected_team_id = random.choice(candidate_teams)

            selected_team = next(t for t in existing_teams if t.id == selected_team_id)
            TeamMember.objects.create(team=selected_team, student=student)
            team_member_counts[selected_team_id] += 1

    return JsonResponse(
        {
            "message": f"총 {num_teams}개 팀으로 자동 편성이 완료되었습니다.",
            "round_id": int(round_id),
            "team_count": num_teams,
        },
        status=200,
    )