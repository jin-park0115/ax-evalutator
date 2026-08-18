import json
import random
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

from apps.evaluations.models import EvaluationRound, ScoreResult
from .models import Team, TeamMember
from .services import (
    get_students_by_percentiles, 
    assign_seed_based_teams, 
    get_user_display_name
)

User = get_user_model()


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
    # [수정] 원래는 READY(편성 확정 후)도 편집 가능 목록에 있었는데,
    # "편성 확정" 버튼 자체의 확인창은 "확정하면 더 이상 수정할 수
    # 없습니다"라고 안내하면서 실제로는 계속 수정 가능했던 모순이
    # 있었다. 확정(READY) 후에는 잠기고, 다시 열려면 명시적으로
    # "수정"을 눌러 draft로 되돌려야 편집 가능하도록 변경.
    editable_statuses = [EvaluationRound.Status.DRAFT]
    return getattr(target_round, "status", EvaluationRound.Status.DRAFT) in editable_statuses


@staff_member_required
@require_http_methods(["GET"])
def team_build_view(request):
    """팀 편성 메인 페이지 렌더링 뷰"""
    round_id = request.GET.get("round_id")
    rounds = EvaluationRound.objects.all().order_by("id")

    if round_id:
        target_round = get_object_or_404(EvaluationRound, id=round_id)
    else:
        target_round = rounds.last()

    # 종료된 이전 회차의 점수 결과(ScoreResult) 존재 여부 확인
    has_score_history = False
    if target_round:
        has_score_history = ScoreResult.objects.filter(
            round__status="finished",
            round_id__lt=target_round.id
        ).exists()

    teams = []
    unassigned_students = []
    
    if target_round:
        teams = Team.objects.filter(round=target_round).prefetch_related("members__student")
        
        assigned_student_ids = TeamMember.objects.filter(
            team__round=target_round
        ).values_list("student_id", flat=True)

        unassigned_students = User.objects.filter(
            role=User.Role.STUDENT, 
            is_active=True
        ).exclude(id__in=assigned_student_ids)

    context = {
        "rounds": rounds,
        "round": target_round,
        "round_editable": is_round_editable(target_round) if target_round else False,
        "has_score_history": has_score_history,  # 템플릿 제어용 변수
        "teams": teams,
        "unassigned_students": unassigned_students,
    }
    return render(request, "teams/team_build.html", context)


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
                "name": get_user_display_name(tm.student),
                "email": getattr(tm.student, "email", ""),
            }
            for tm in team.members.all()
        ]
        teams_data.append(
            {
                "team_id": team.id,
                "team_name": team.name,
                "presentation_order": getattr(team, "presentation_order", None),
                "eval_status": getattr(team, "eval_status", None),
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

    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    target_team = get_object_or_404(Team, id=target_team_id)
    target_round = target_team.round

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 팀 구성을 변경할 수 없습니다."},
            status=400,
        )

    with transaction.atomic():
        TeamMember.objects.filter(team__round=target_round, student=student).delete()
        TeamMember.objects.create(team=target_team, student=student)

    student_display_name = get_user_display_name(student)
    return JsonResponse(
        {"message": f"{student_display_name} 수강생이 '{target_team.name}' 팀으로 배정되었습니다."},
        status=200,
    )


@staff_member_required
@require_http_methods(["POST"])
def get_percentile_preview(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    round_id = data.get("round_id")
    thresholds = data.get("thresholds", [30.0, 60.0])
    excluded_student_ids = [int(sid) for sid in data.get("excluded_student_ids", [])]
    window = data.get("window") or None

    groups = get_students_by_percentiles(
        target_round_id=round_id,
        thresholds=thresholds,
        excluded_student_ids=excluded_student_ids,
        window=window,
    )

    return JsonResponse({"thresholds": thresholds, "groups": groups}, status=200)


@staff_member_required
@require_http_methods(["POST"])
def auto_assign_teams(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    round_id = data.get("round_id")
    team_count = data.get("team_count")
    thresholds = data.get("thresholds", [30.0, 60.0])
    fixed_student_ids = [int(sid) for sid in data.get("fixed_student_ids", [])]
    excluded_student_ids = [int(sid) for sid in data.get("excluded_student_ids", [])]
    window = data.get("window") or None

    if not round_id:
        return JsonResponse({"error": "round_id는 필수입니다."}, status=400)

    target_round = get_object_or_404(EvaluationRound, id=round_id)

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"현재 회차 상태({target_round.status})에서는 자동 편성을 실행할 수 없습니다."},
            status=400,
        )

    has_score_history = ScoreResult.objects.filter(
        round__status="finished", round_id__lt=target_round.id
    ).exists()

    active_students = (
        User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .exclude(id__in=excluded_student_ids)
        .distinct()
    )
    total_students_count = active_students.count()

    if total_students_count == 0:
        return JsonResponse({"error": "배정 가능한 대상 수강생이 없습니다."}, status=400)

    num_teams = int(team_count) if team_count else calculate_optimal_team_count(total_students_count)
    if num_teams < 1:
        num_teams = 1

    with transaction.atomic():
        if has_score_history:
            assign_seed_based_teams(
                target_round=target_round,
                num_teams=num_teams,
                thresholds=thresholds,
                fixed_student_ids=fixed_student_ids,
                excluded_student_ids=excluded_student_ids,
                window=window,
            )
            window_label = "전체 누적 평균" if not window else f"직전 {window}회차 평균"
            msg = f"시드 점수 기반({window_label}, 제외 {len(excluded_student_ids)}명 반영, 총 {num_teams}개 팀) 자동 편성이 완료되었습니다."
        else:
            existing_teams = list(Team.objects.filter(round=target_round).order_by("id"))

            if len(existing_teams) < num_teams:
                for i in range(len(existing_teams) + 1, num_teams + 1):
                    new_team = Team.objects.create(round=target_round, name=f"{i}팀")
                    existing_teams.append(new_team)
            elif len(existing_teams) > num_teams:
                for team_to_delete in existing_teams[num_teams:]:
                    team_to_delete.delete()
                existing_teams = existing_teams[:num_teams]

            excluded_set = set(excluded_student_ids)
            fixed_set = set(fixed_student_ids) - excluded_set

            TeamMember.objects.filter(team__round=target_round, student_id__in=excluded_set).delete()
            TeamMember.objects.filter(team__round=target_round).exclude(student_id__in=fixed_set).delete()

            assigned_student_ids = set(
                TeamMember.objects.filter(team__round=target_round).values_list("student_id", flat=True)
            )
            unassigned_students = [
                s for s in active_students 
                if s.id not in assigned_student_ids and s.id not in excluded_set
            ]
            random.shuffle(unassigned_students)

            team_member_counts = {
                team.id: TeamMember.objects.filter(team=team).count() for team in existing_teams
            }

            for student in unassigned_students:
                min_count = min(team_member_counts.values())
                candidate_teams = [t_id for t_id, count in team_member_counts.items() if count == min_count]
                selected_team_id = random.choice(candidate_teams)

                selected_team = next(t for t in existing_teams if t.id == selected_team_id)
                TeamMember.objects.create(team=selected_team, student=student)
                team_member_counts[selected_team_id] += 1

            msg = f"최초 회차 - 무작위(제외 {len(excluded_student_ids)}명 반영, 총 {num_teams}개 팀) 자동 편성이 완료되었습니다."

    return JsonResponse(
        {
            "message": msg,
            "round_id": int(round_id),
            "team_count": num_teams,
            "excluded_count": len(excluded_student_ids),
            "is_seed_based": has_score_history,
        },
        status=200,
    )


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
        target_round.status = getattr(EvaluationRound.Status, "READY", "READY")
        target_round.save()

    return JsonResponse(
        {
            "message": f"{target_round.id}회차 팀 편성이 확정되었습니다.",
            "round_id": target_round.id,
            "status": target_round.status,
        },
        status=200,
    )