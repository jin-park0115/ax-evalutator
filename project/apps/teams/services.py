import math
import random
from django.db import transaction
from django.db.models import Avg
from django.contrib.auth import get_user_model
from apps.evaluations.models import ScoreResult
from .models import Team, TeamMember

User = get_user_model()


def get_user_display_name(user):
    """유저의 표시 이름을 안전하게 추출"""
    if hasattr(user, "get_full_name") and user.get_full_name():
        return user.get_full_name()
    return getattr(user, "username", getattr(user, "email", str(user.id)))


def assign_teams(student_ids: list[int], team_size: int = 5) -> list[list[int]]:
    if team_size <= 0:
        raise ValueError("team_size must be greater than 0")
    return [student_ids[index : index + team_size] for index in range(0, len(student_ids), team_size)]


def build_teams(student_ids: list[int], team_size: int = 5) -> list[list[int]]:
    return assign_teams(student_ids, team_size=team_size)


def get_student_seed_scores():
    """모든 학생(STUDENT)의 이전 회차 final_score 평균 점수를 계산 (중복 없는 학생 목록)"""
    students = User.objects.filter(role=User.Role.STUDENT).distinct()
    student_scores = []

    for student in students:
        avg_score = ScoreResult.objects.filter(user=student).aggregate(
            Avg("final_score")
        )["final_score__avg"]

        student_scores.append({
            "student_id": student.id,
            "student_name": get_user_display_name(student),
            "email": getattr(student, "email", ""),
            "avg_score": round(avg_score, 2) if avg_score is not None else 0.0,
        })

    # 평균 점수 내림차순 정렬
    student_scores.sort(key=lambda x: x["avg_score"], reverse=True)
    return student_scores


def get_students_by_percentiles(thresholds=[30.0, 60.0]):
    """퍼센테이지 슬라이더 변경 시 점수대별 수강생 목록 실시간 반환"""
    student_scores = get_student_seed_scores()
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


def assign_seed_based_teams(target_round, num_teams, thresholds=[30.0, 60.0], fixed_student_ids=[]):
    """시드 점수 기반 팀 자동 편성 (고정 수강생 유지 + 구간별 균등 무작위 배정 + 중복 완전 차단)"""
    groups = get_students_by_percentiles(thresholds)
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

    fixed_set = set(fixed_student_ids)

    # 2. 해당 회차 전체에서 고정 수강생이 아닌 팀원 관계 삭제 (중복 생성 방지)
    TeamMember.objects.filter(team__round=target_round).exclude(student_id__in=fixed_set).delete()

    # 3. 고정 수강생 기반 현재 팀별 인원 추적
    team_assignments = {team.id: [] for team in existing_teams}
    for team in existing_teams:
        members = list(TeamMember.objects.filter(team=team).values_list("student_id", flat=True))
        team_assignments[team.id] = members

    # 4. 구간별 학생들을 라운드로빈/최소인원 팀에 배정
    for group in groups:
        unassigned_group_students = [
            s["student_id"] for s in group["students"] if s["student_id"] not in fixed_set
        ]
        random.shuffle(unassigned_group_students)

        for student_id in unassigned_group_students:
            # 팀 인원이 가장 적은 팀들을 찾음
            min_count = min(len(members) for members in team_assignments.values())
            candidate_team_ids = [
                t_id for t_id, members in team_assignments.items() if len(members) == min_count
            ]
            selected_team_id = random.choice(candidate_team_ids)

            # 메모리 및 DB 동시 업데이트
            team_assignments[selected_team_id].append(student_id)
            selected_team = next(t for t in existing_teams if t.id == selected_team_id)
            TeamMember.objects.create(team=selected_team, student_id=student_id)

    return team_assignments