import json
import random
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

from apps.evaluations.models import EvaluationRound
from .models import Team, TeamMember

User = get_user_model()


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
    # EvaluationRound.Status 값은 소문자("draft","ready","in_progress","finished")인데
    # 대문자 목록과 비교하고 있어서 항상 False가 나오던 버그 수정
    editable_statuses = [EvaluationRound.Status.DRAFT, EvaluationRound.Status.READY]
    return getattr(target_round, "status", EvaluationRound.Status.DRAFT) in editable_statuses


# ---------------------------------------------------------------------------
# API Views
# ---------------------------------------------------------------------------

# 1. 회차별 전체 팀 및 팀원 목록 조회
@require_http_methods(["GET"])
def round_team_members(request):
    round_id = request.GET.get("round_id")

    if not round_id:
        latest_round = EvaluationRound.objects.order_by("-id").first()
        if not latest_round:
            return JsonResponse({"round_id": None, "teams": []}, status=200)
        round_id = latest_round.id

    target_round = get_object_or_404(EvaluationRound, id=round_id)

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
                "name": getattr(tm.student, "name", getattr(tm.student, "username", str(tm.student))),
                "email": getattr(tm.student, "email", ""),
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


# 2. 팀 수동 생성
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

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 팀을 신규 생성할 수 없습니다."},
            status=400,
        )

    if Team.objects.filter(round=target_round, name=team_name).exists():
        return JsonResponse({"error": f"이미 해당 회차에 '{team_name}'이(가) 존재합니다."}, status=400)

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

    # Student 모델 대신 User 모델에서 STUDENT 역할인 수강생 조회
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    target_team = get_object_or_404(Team, id=target_team_id)
    target_round = target_team.round

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 팀 구성을 변경할 수 없습니다."},
            status=400,
        )

    with transaction.atomic():
        existing_membership = TeamMember.objects.filter(
            team__round=target_round, student=student
        ).first()

        if existing_membership:
            if existing_membership.team_id == target_team.id:
                return JsonResponse({"message": "이미 해당 팀에 소속되어 있습니다."}, status=200)
            existing_membership.delete()

        TeamMember.objects.create(team=target_team, student=student)

    student_display_name = getattr(student, "name", student.username)
    return JsonResponse(
        {"message": f"{student_display_name} 수강생이 '{target_team.name}' 팀으로 배정되었습니다."},
        status=200,
    )


# 4. 무작위 팀 자동 편성
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

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 자동 편성을 실행할 수 없습니다."},
            status=400,
        )

    # Student 모델 대신 User 모델에서 STUDENT 역할을 가진 사용자 전체 추출
    all_students = list(User.objects.filter(role=User.Role.STUDENT))
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


# 5. 팀 편성 확정
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

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"이미 확정되었거나 변경할 수 없는 상태입니다. (현재 상태: {target_round.status})"},
            status=400,
        )

    team_count = Team.objects.filter(round=target_round).count()
    if team_count == 0:
        return JsonResponse({"error": "생성된 팀이 없습니다. 최소 1개 이상의 팀을 편성해주세요."}, status=400)

    with transaction.atomic():
        target_round.status = "CONFIRMED"
        target_round.save()

    return JsonResponse(
        {
            "message": f"{target_round.id}회차 팀 편성이 확정되었습니다. 이제 팀 구성을 변경할 수 없습니다.",
            "round_id": target_round.id,
            "status": target_round.status,
        },
        status=200,
    )