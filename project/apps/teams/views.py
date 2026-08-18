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
    preview_seed_based_teams,
    preview_random_teams,
    get_user_display_name,
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
    # [수정] "편성 확정"은 이제 회차를 바로 진행 중(IN_PROGRESS)으로
    # 넘기지만, 팀 편성 자체는 실제로 평가(발표)가 시작되기 전까지는
    # 계속 수정 가능해야 한다. 그래서 상태만으로 편집 가능 여부를
    # 판단하지 않고, 이 회차의 팀 중 하나라도 발표(평가)가 열렸는지로
    # 판단한다 — 평가가 시작된 뒤에는 팀 구성을 바꾸면 이미 진행 중인
    # 평가 데이터와 어긋나므로 잠근다.
    status = getattr(target_round, "status", EvaluationRound.Status.DRAFT)
    if status == EvaluationRound.Status.DRAFT:
        return True
    if status in (EvaluationRound.Status.READY, EvaluationRound.Status.IN_PROGRESS):
        return not Team.objects.filter(
            round=target_round, eval_opened_at__isnull=False
        ).exists()
    return False


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
    """자동 편성 '미리보기' — DB에는 아무것도 저장하지 않는다.

    화면(브라우저)에 있는 현재 편성 상태(current_assignments)를 받아서
    다음 편성 결과만 계산해 돌려준다. 실제 저장은 '편성 확정' 버튼을
    눌러 confirm_team_assignment가 호출될 때 한 번에 이뤄진다.
    """
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
    current_assignments = data.get("current_assignments") or {}
    current_assignments = {
        name: [int(sid) for sid in ids] for name, ids in current_assignments.items()
    }

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

    active_student_ids = list(
        User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .exclude(id__in=excluded_student_ids)
        .values_list("id", flat=True)
        .distinct()
    )

    if not active_student_ids:
        return JsonResponse({"error": "배정 가능한 대상 수강생이 없습니다."}, status=400)

    num_teams = int(team_count) if team_count else calculate_optimal_team_count(len(active_student_ids))
    if num_teams < 1:
        num_teams = 1

    if has_score_history:
        team_assignments = preview_seed_based_teams(
            current_assignments=current_assignments,
            num_teams=num_teams,
            target_round_id=target_round.id,
            thresholds=thresholds,
            fixed_student_ids=fixed_student_ids,
            excluded_student_ids=excluded_student_ids,
            window=window,
        )
        window_label = "전체 누적 평균" if not window else f"직전 {window}회차 평균"
        msg = f"시드 점수 기반({window_label}, 제외 {len(excluded_student_ids)}명 반영, 총 {num_teams}개 팀) 임시 편성이 완료되었습니다. '편성 확정'을 눌러야 저장됩니다."
    else:
        # active_student_ids는 exclude된 학생 제외하고 이미 필터됐지만,
        # preview_random_teams에는 excluded_student_ids도 같이 넘겨서
        # 고정(fixed) 판정 등 내부 로직 일관성을 유지한다.
        team_assignments = preview_random_teams(
            current_assignments=current_assignments,
            num_teams=num_teams,
            active_student_ids=active_student_ids,
            fixed_student_ids=fixed_student_ids,
            excluded_student_ids=excluded_student_ids,
        )
        msg = f"무작위(제외 {len(excluded_student_ids)}명 반영, 총 {num_teams}개 팀) 임시 편성이 완료되었습니다. '편성 확정'을 눌러야 저장됩니다."

    users = User.objects.filter(
        id__in=[sid for ids in team_assignments.values() for sid in ids]
    )
    name_by_id = {u.id: get_user_display_name(u) for u in users}

    teams_payload = {
        name: [{"student_id": sid, "name": name_by_id.get(sid, sid)} for sid in ids]
        for name, ids in team_assignments.items()
    }

    return JsonResponse(
        {
            "message": msg,
            "round_id": int(round_id),
            "team_count": num_teams,
            "excluded_count": len(excluded_student_ids),
            "is_seed_based": has_score_history,
            "teams": teams_payload,
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
    assignments = data.get("assignments")

    if not round_id:
        return JsonResponse({"error": "round_id는 필수입니다."}, status=400)

    if not isinstance(assignments, dict):
        return JsonResponse({"error": "assignments(팀별 편성 결과)가 필요합니다."}, status=400)

    target_round = get_object_or_404(EvaluationRound, id=round_id)

    if not is_round_editable(target_round):
        return JsonResponse(
            {"error": f"이미 확정되었거나 변경할 수 없는 상태입니다. (현재 상태: {target_round.status})"},
            status=400,
        )

    # 팀 이름별로 학생 id 목록 정리 + 검증
    try:
        cleaned = {
            str(name).strip(): [int(sid) for sid in ids]
            for name, ids in assignments.items()
            if str(name).strip()
        }
    except (TypeError, ValueError):
        return JsonResponse({"error": "assignments 형식이 올바르지 않습니다."}, status=400)

    if not cleaned:
        return JsonResponse({"error": "생성된 팀이 없습니다. 최소 1개 이상의 팀을 편성해주세요."}, status=400)

    all_student_ids = [sid for ids in cleaned.values() for sid in ids]
    if len(all_student_ids) != len(set(all_student_ids)):
        return JsonResponse({"error": "같은 학생이 두 팀 이상에 중복 배정되어 있습니다."}, status=400)

    valid_student_ids = set(
        User.objects.filter(
            id__in=all_student_ids, role=User.Role.STUDENT, is_active=True
        ).values_list("id", flat=True)
    )
    if len(valid_student_ids) != len(all_student_ids):
        return JsonResponse({"error": "존재하지 않거나 학생이 아닌 사용자가 포함되어 있습니다."}, status=400)

    with transaction.atomic():
        # 웹에서 '편성 확정'을 눌러야만 이 시점에 실제로 DB에 저장된다.
        # 자동 편성/배정/이동/해제는 모두 브라우저에만 있는 임시 상태였고,
        # 여기서 한 번에 Team/TeamMember를 새 편성 결과로 갈아엎는다.
        existing_teams = {t.name: t for t in Team.objects.filter(round=target_round)}

        for name in list(existing_teams.keys()):
            if name not in cleaned:
                existing_teams.pop(name).delete()

        for name in cleaned:
            if name not in existing_teams:
                existing_teams[name] = Team.objects.create(round=target_round, name=name)

        TeamMember.objects.filter(team__round=target_round).delete()
        TeamMember.objects.bulk_create(
            [
                TeamMember(team=existing_teams[name], student_id=sid)
                for name, ids in cleaned.items()
                for sid in ids
            ]
        )

        # 확정 즉시 진행 중 상태로 전환한다 (대기 단계는 두지 않음).
        # 팀 구성은 실제로 발표/평가가 시작되기 전까지 계속 수정 가능
        # (is_round_editable 참고).
        target_round.status = EvaluationRound.Status.IN_PROGRESS
        target_round.save()

    return JsonResponse(
        {
            "message": f"{target_round.id}회차 팀 편성이 확정되어 저장되었습니다.",
            "round_id": target_round.id,
            "status": target_round.status,
        },
        status=200,
    )