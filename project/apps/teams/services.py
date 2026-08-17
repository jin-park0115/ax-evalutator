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


def get_student_seed_scores(target_round_id=None, excluded_student_ids=[]):
    """
    모든 활성 학생(STUDENT)의 TEAM_USER_SCORE_SEED 테이블 내 직전 회차 cumulative_seed 조회
    - Subquery를 사용해 N+1 문제 해결 및 단일 쿼리로 최적화
    - target_round_id가 주어지면 해당 회차 '미만'의 가장 최신 시드 점수를 조회
    """
    latest_seed_subquery = TeamUserScoreSeed.objects.filter(
        user=OuterRef("pk")
    )

    if target_round_id:
        latest_seed_subquery = latest_seed_subquery.filter(round_id__lt=target_round_id)

    latest_seed_subquery = latest_seed_subquery.order_by("-round_id").values("cumulative_seed")[:1]

    students = (
        User.objects.filter(role=User.Role.STUDENT, is_active=True)
        .exclude(id__in=excluded_student_ids)
        .annotate(
            seed_score=Coalesce(
                Subquery(latest_seed_subquery, output_field=FloatField()),
                Value(0.0),
            )
        )
        .order_by("-seed_score", "id")
    )

    student_scores = []
    for student in students:
        student_scores.append({
            "student_id": student.id,
            "student_name": get_user_display_name(student),
            "email": getattr(student, "email", ""),
            "avg_score": round(student.seed_score, 2),
        })

    return student_scores


def get_students_by_percentiles(target_round_id=None, thresholds=[30.0, 60.0], excluded_student_ids=[]):
    """퍼센테이지 슬라이더 변경 시 제외 학생을 뺀 누적 시드 점수대별 수강생 목록 실시간 반환"""
    student_scores = get_student_seed_scores(
        target_round_id=target_round_id, 
        excluded_student_ids=excluded_student_ids
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


def assign_seed_based_teams(target_round, num_teams, thresholds=[30.0, 60.0], fixed_student_ids=[], excluded_student_ids=[]):
    """시드 점수 기반 팀 자동 편성"""
    groups = get_students_by_percentiles(
        target_round_id=target_round.id,
        thresholds=thresholds, 
        excluded_student_ids=excluded_student_ids
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