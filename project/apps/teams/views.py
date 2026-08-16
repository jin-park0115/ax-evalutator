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


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def calculate_optimal_team_count(total_students):
    """팀 수 미입력 시 4~5명 위주로 인원이 균등하게 배정되도록 최적의 팀 수 계산"""
    if total_students <= 0:
        return 0
    if total_students <= 5:
        return 1

    best_team_count = round(total_students / 4.5)

    while best_team_count > 1 and (total_students / best_team_count) < 3:
        best_team_count -= 1
    while (total_students / best_team_count) > 5:
        best_team_count += 1

    return max(1, best_team_count)


def is_round_editable(target_round):
    """
    회차 상태에 따라 팀 편성/수정이 가능한지 검증하는 함수
    'UPCOMING'(시작 전) 또는 'DRAFT'(수정 중/준비 중) 상태일 때만 True 반환
    (프로젝트의 EvaluationRound status 필드값에 맞게 상태 문자열을 조정해주세요)
    """
    editable_statuses = ["UPCOMING", "DRAFT", "READY"]
    return getattr(target_round, "status", "UPCOMING") in editable_statuses


# ---------------------------------------------------------------------------
# API Views
# ---------------------------------------------------------------------------

# 1. 회차별 전체 팀 및 팀원 목록 조회
# - 회차 시작 전: 관리자만 조회 가능
# - 회차 시작 후: 일반 사용자도 조회 가능
@require_http_methods(["GET"])
def round_team_members(request):
    round_id = request.GET.get("round_id")

    if not round_id:
        latest_round = EvaluationRound.objects.order_by("-id").first()
        if not latest_round:
            return JsonResponse({"round_id": None, "teams": []}, status=200)
        round_id = latest_round.id

    target_round = get_object_or_404(EvaluationRound, id=round_id)

    # [권한 체크] 회차가 시작 전 상태인데 관리자(staff)가 아닌 경우 조회 거부
    is_admin = request.user.is_authenticated and request.user.is_staff
    if is_round_editable(target_round) and not is_admin:
        return JsonResponse(
            {"error": "회차가 시작되기 전에는 관리자만 팀 목록을 조회할 수 있습니다."},
            status=403,
        )

    teams = (
        Team.objects.filter(round=target_round)
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

    return JsonResponse(
        {
            "round_id": int(round_id),
            "round_status": getattr(target_round, "status", None),
            "teams": teams_data,
        },
        status=200,
    )

# 2. 팀 수동 생성 (시작 전 상태에서만 허용)
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

    # 상태 검증: 시작 전/수정 가능 상태인지 체크
    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 팀을 신규 생성할 수 없습니다."},
            status=400,
        )

    # 중복 팀 이름 방지
    if Team.objects.filter(round=target_round, name=team_name).exists():
        return JsonResponse({"error": f"이미 해당 회차에 '{team_name}'이(가) 존재합니다."}, status=400)

    team = Team.objects.create(round=target_round, name=team_name)

    return JsonResponse(
        {"message": f"'{team.name}' 팀이 생성되었습니다.", "team_id": team.id},
        status=201,
    )


# 3. 수강생 팀 수동 배정 및 이동 (시작 전 상태에서만 허용)
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

    # 상태 검증: 시작 전/수정 가능 상태인지 체크
    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 팀 구성을 변경할 수 없습니다."},
            status=400,
        )

    with transaction.atomic():
        # 해당 회차 내에 이미 다른 팀에 배정되어 있다면 기존 팀에서 삭제 (동일 회차 내 1인 1팀 보장)
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


# 4. 무작위 팀 자동 편성 (수동 고정 수강생 반영, 시작 전 상태에서만 허용)
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

    # 상태 검증
    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 자동 편성을 실행할 수 없습니다."},
            status=400,
        )

    all_students = list(Student.objects.all())
    total_students_count = len(all_students)

    if total_students_count == 0:
        return JsonResponse({"error": "등록된 수강생이 없습니다."}, status=400)

    num_teams = int(team_count) if team_count else calculate_optimal_team_count(total_students_count)

    with transaction.atomic():
        existing_teams = list(Team.objects.filter(round=target_round).order_by("id"))

        if len(existing_teams) < num_teams:
            for i in range(len(existing_teams) + 1, num_teams + 1):
                new_team = Team.objects.create(round=target_round, name=f"{i}팀")
                existing_teams.append(new_team)
        elif len(existing_teams) > num_teams:
            for team_to_delete in existing_teams[num_teams:]:
                team_to_delete.delete()
            existing_teams = existing_teams[:num_teams]

        # 고정 멤버 및 인원 카운트
        assigned_memberships = TeamMember.objects.filter(
            team__round=target_round
        ).select_related("student")

        assigned_student_ids = set()
        team_member_counts = {team.id: 0 for team in existing_teams}

        for membership in assigned_memberships:
            if membership.team_id in team_member_counts:
                assigned_student_ids.add(membership.student.id)
                team_member_counts[membership.team_id] += 1

        unassigned_students = [s for s in all_students if s.id not in assigned_student_ids]
        random.shuffle(unassigned_students)

        # 라운드 로빈 배치 (오차 범위 1명)
        for student in unassigned_students:
            min_count = min(team_member_counts.values())
            candidate_teams = [t_id for t_id, count in team_member_counts.items() if count == min_count]
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


# 5. [신규] 팀 편성 확정 및 회차 상태 전이 API
@staff_member_required
@require_http_methods(["POST"])
def confirm_team_assignment(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    round_id = data.get("round_id")

    if not round_id:
        return JsonResponse({"error": "round_id는 필수입니다."}, status=400)

    target_round = get_object_or_404(EvaluationRound, id=round_id)

    # 이미 확정되었거나 진행/종료된 경우 중복 확정 방지
    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"이미 확정되었거나 변경할 수 없는 상태입니다. (현재 상태: {target_round.status})"},
            status=400,
        )

    # 팀이 하나도 구성되지 않은 경우 확정 불가
    team_count = Team.objects.filter(round=target_round).count()
    if team_count == 0:
        return JsonResponse({"error": "생성된 팀이 없습니다. 최소 1개 이상의 팀을 편성해주세요."}, status=400)

    with transaction.atomic():
        # 회차 상태를 확정/시작가능 상태로 전이 (모델 field 정의에 맞는 값으로 수정)
        target_round.status = "CONFIRMED"  # 혹은 "IN_PROGRESS" / "READY"
        target_round.save()

    return JsonResponse(
        {
            "message": f"{target_round.id}회차 팀 편성이 확정되었습니다. 이제 팀 구성을 변경할 수 없습니다.",
            "round_id": target_round.id,
            "status": target_round.status,
        },
        status=200,
    )