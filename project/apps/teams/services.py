import math
import random
from django.db import transaction
from django.db.models import OuterRef, Subquery, Value, FloatField
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from .models import Team, TeamMember, TeamUserScoreSeed

User = get_user_model()


def get_user_display_name(user):
    """유저의 표시 이름을 안전하게 추출"""
    if hasattr(user, "get_full_name") and user.get_full_name():
        return user.get_full_name()
    return getattr(user, "username", getattr(user, "email", str(user.id)))


def get_student_seed_scores(target_round_id=None, excluded_student_ids=[], window=None):
    """
    모든 활성 학생(STUDENT)의 시드 점수를 조회한다.

    window:
        None (기본값) - 지금까지 "종료"된 모든 회차의 최종점수 평균 (전체 누적)
        1            - 직전 1회차 최종점수
        3, 5 등      - 직전 N회차 최종점수 평균

    ScoreResult(회차별 최종 성적표)에서 직접 계산한다.
    원래는 TEAM_USER_SCORE_SEED 테이블에 미리 계산해 둔 cumulative_seed를
    읽었는데, 그 값을 채워 넣는 코드가 어디에도 없어서 실제로는 테이블이
    항상 비어 있었고(2026-08-19 확인), 자동 편성이 매번 전원 0점으로
    취급해 사실상 완전 무작위로 동작하고 있었다.
    또한 "직전 몇 회차 평균으로 볼지"를 튜터가 자동 편성 화면에서 매번
    골라 쓸 수 있어야 해서, 미리 값을 구워두는 방식 대신 요청 시점에
    ScoreResult에서 즉석으로 계산하는 방식으로 바꿨다.
    """
    from apps.evaluations.models import ScoreResult

    rows_qs = ScoreResult.objects.filter(round__status="finished")
    if target_round_id:
        rows_qs = rows_qs.filter(round_id__lt=target_round_id)

    rows = (
        rows_qs.exclude(user_id__in=excluded_student_ids)
        .order_by("user_id", "-round_id")
        .values("user_id", "final_score")
    )

    scores_by_user = {}
    for row in rows:
        if row["final_score"] is None:
            continue
        scores_by_user.setdefault(row["user_id"], []).append(row["final_score"])

    students = (
        User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .exclude(id__in=excluded_student_ids)
        .order_by("id")
    )

    student_scores = []
    for student in students:
        # round_id 내림차순으로 이미 정렬돼 있으므로 앞에서 window개만
        # 자르면 "가장 최근 N회차"가 된다.
        history = scores_by_user.get(student.id, [])
        if window:
            history = history[:window]
        avg_score = sum(history) / len(history) if history else 0.0

        student_scores.append({
            "student_id": student.id,
            "student_name": get_user_display_name(student),
            "email": getattr(student, "email", ""),
            "avg_score": round(avg_score, 2),
        })

    student_scores.sort(key=lambda s: (-s["avg_score"], s["student_name"], s["student_id"]))

    return student_scores


def get_students_by_percentiles(target_round_id=None, thresholds=[30.0, 60.0], excluded_student_ids=[], window=None):
    """퍼센테이지 슬라이더 변경 시 제외 학생을 뺀 시드 점수대별 수강생 목록 실시간 반환.
    window는 get_student_seed_scores와 동일 (None=전체 누적, 1/3/5=직전 N회차 평균)."""
    student_scores = get_student_seed_scores(
        target_round_id=target_round_id,
        excluded_student_ids=excluded_student_ids,
        window=window,
    )
    total_count = len(student_scores)

    if total_count == 0:
        return []

    sorted_thresholds = sorted([t for t in thresholds if 0 < t < 100])
    groups = []
    prev_idx = 0

    for idx, pct in enumerate(sorted_thresholds):
        curr_idx = math.ceil(total_count * (pct / 100.0))
        groups.append({
            "group_index": idx + 1,
            "label": f"상위 {pct}% 이하" if idx == 0 else f"상위 {sorted_thresholds[idx-1]}% ~ {pct}%",
            "count": curr_idx - prev_idx,
            "students": student_scores[prev_idx:curr_idx],
        })
        prev_idx = curr_idx

    groups.append({
        "group_index": len(sorted_thresholds) + 1,
        "label": f"상위 {sorted_thresholds[-1]}% 초과 (하위)",
        "count": total_count - prev_idx,
        "students": student_scores[prev_idx:],
    })

    return groups


def preview_seed_based_teams(
    current_assignments,
    num_teams,
    target_round_id=None,
    thresholds=[30.0, 60.0],
    fixed_student_ids=[],
    excluded_student_ids=[],
    window=None,
):
    """자동 편성 '미리보기' — DB에 아무것도 쓰지 않는다.

    '편성 확정' 버튼을 눌러야만 DB에 저장되도록 하기 위해, 자동 편성은
    화면(브라우저)에 들고 있는 현재 편성 상태(current_assignments,
    {팀 이름: [student_id, ...]})를 입력으로 받아 다음 편성 결과만
    계산해서 돌려준다. 실제 Team/TeamMember 레코드는 건드리지 않는다.
    """
    groups = get_students_by_percentiles(
        target_round_id=target_round_id,
        thresholds=thresholds,
        excluded_student_ids=excluded_student_ids,
        window=window,
    )

    excluded_set = set(excluded_student_ids)
    fixed_set = set(fixed_student_ids) - excluded_set

    team_names = [f"{i}팀" for i in range(1, num_teams + 1)]
    team_assignments = {name: [] for name in team_names}

    # 고정(fixCheck)된 학생만 기존 자리 그대로 유지. 팀 수가 줄어서
    # 그 팀 자체가 사라졌으면 고정을 풀고 다시 배정 대상에 포함시킨다.
    for name, student_ids in (current_assignments or {}).items():
        if name not in team_assignments:
            continue
        team_assignments[name] = [
            sid for sid in student_ids
            if sid in fixed_set and sid not in excluded_set
        ]

    placed_fixed_ids = {sid for ids in team_assignments.values() for sid in ids}
    effective_fixed_set = fixed_set & placed_fixed_ids

    for group in groups:
        unassigned_group_students = [
            s["student_id"] for s in group["students"]
            if s["student_id"] not in effective_fixed_set and s["student_id"] not in excluded_set
        ]
        random.shuffle(unassigned_group_students)

        for student_id in unassigned_group_students:
            min_count = min(len(members) for members in team_assignments.values())
            candidate_names = [
                name for name, members in team_assignments.items() if len(members) == min_count
            ]
            selected_name = random.choice(candidate_names)
            team_assignments[selected_name].append(student_id)

    return team_assignments


def preview_random_teams(
    current_assignments,
    num_teams,
    active_student_ids,
    fixed_student_ids=[],
    excluded_student_ids=[],
):
    """이전 시드 데이터가 없는 최초 회차용 무작위 자동 편성 '미리보기'.
    preview_seed_based_teams와 마찬가지로 DB에 아무것도 쓰지 않는다."""
    excluded_set = set(excluded_student_ids)
    fixed_set = set(fixed_student_ids) - excluded_set

    team_names = [f"{i}팀" for i in range(1, num_teams + 1)]
    team_assignments = {name: [] for name in team_names}

    for name, student_ids in (current_assignments or {}).items():
        if name not in team_assignments:
            continue
        team_assignments[name] = [
            sid for sid in student_ids
            if sid in fixed_set and sid not in excluded_set
        ]

    placed_fixed_ids = {sid for ids in team_assignments.values() for sid in ids}
    assignable = [
        sid for sid in active_student_ids
        if sid not in excluded_set and sid not in placed_fixed_ids
    ]
    random.shuffle(assignable)

    for student_id in assignable:
        min_count = min(len(members) for members in team_assignments.values())
        candidate_names = [
            name for name, members in team_assignments.items() if len(members) == min_count
        ]
        team_assignments[random.choice(candidate_names)].append(student_id)

    return team_assignments


def assign_seed_based_teams(target_round, num_teams, thresholds=[30.0, 60.0], fixed_student_ids=[], excluded_student_ids=[], window=None):
    """시드 점수 기반 팀 자동 편성.
    window는 get_student_seed_scores와 동일 (None=전체 누적, 1/3/5=직전 N회차 평균)."""
    groups = get_students_by_percentiles(
        target_round_id=target_round.id,
        thresholds=thresholds,
        excluded_student_ids=excluded_student_ids,
        window=window,
    )
    existing_teams = list(Team.objects.filter(round=target_round).order_by("id"))

    # 1. 팀 수 조정
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

    # 2. 기존 팀원 중 제외 대상 및 비고정 대상 삭제
    TeamMember.objects.filter(team__round=target_round, student_id__in=excluded_set).delete()
    TeamMember.objects.filter(team__round=target_round).exclude(student_id__in=fixed_set).delete()

    # 3. 고정 수강생 기반 현재 팀별 인원 추적
    team_assignments = {team.id: [] for team in existing_teams}
    for team in existing_teams:
        members = list(
            TeamMember.objects.filter(team=team)
            .exclude(student_id__in=excluded_set)
            .values_list("student_id", flat=True)
        )
        team_assignments[team.id] = members

    # 4. 구간별 미배정 학생 무작위 균등 배정
    for group in groups:
        unassigned_group_students = [
            s["student_id"] for s in group["students"] 
            if s["student_id"] not in fixed_set and s["student_id"] not in excluded_set
        ]
        random.shuffle(unassigned_group_students)

        for student_id in unassigned_group_students:
            min_count = min(len(members) for members in team_assignments.values())
            candidate_team_ids = [
                t_id for t_id, members in team_assignments.items() if len(members) == min_count
            ]
            selected_team_id = random.choice(candidate_team_ids)

            team_assignments[selected_team_id].append(student_id)
            selected_team = next(t for t in existing_teams if t.id == selected_team_id)
            TeamMember.objects.create(team=selected_team, student_id=student_id)

    return team_assignments