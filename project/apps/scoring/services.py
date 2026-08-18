from django.db import transaction

from apps.evaluations.models import (
    IndividualEvaluation,
    TeamEvaluation,
    TutorEvaluation,
    ScoreResult,
)
from apps.teams.models import Team, TeamMember, TeamUserScoreSeed


# ==============================================================================
# 여러 회차의 학생별 점수 평균
# ==============================================================================

def calculate_seed_scores(
    round_scores: list[dict[int, float]],
) -> dict[int, float]:
    """
    여러 회차의 학생별 점수를 받아
    학생별 평균 점수를 계산한다.
    """

    totals: dict[int, float] = {}
    counts: dict[int, int] = {}

    for scores in round_scores:
        for student_id, score in scores.items():
            totals[student_id] = totals.get(student_id, 0.0) + score
            counts[student_id] = counts.get(student_id, 0) + 1

    return {
        student_id: totals[student_id] / counts[student_id]
        for student_id in totals
    }


# ==============================================================================
# 종료된 회차의 최종 점수 조회
# ==============================================================================

def get_seed_scores_from_db() -> dict[int, float]:
    """
    종료된 회차의 ScoreResult.final_score를 가져와
    학생별 평균 점수를 계산한다.
    """

    results = (
        ScoreResult.objects
        .filter(round__status="finished")
        .values("user_id", "final_score")
        .order_by("round_id", "user_id")
    )

    student_scores: dict[int, list[float]] = {}

    for result in results:
        student_id = result["user_id"]
        final_score = result["final_score"]

        if final_score is None:
            continue

        student_scores.setdefault(student_id, []).append(final_score)

    return {
        student_id: sum(scores) / len(scores)
        for student_id, scores in student_scores.items()
        if scores
    }


# ==============================================================================
# 학생 순위 계산
# ==============================================================================

def calculate_rankings(
    scores: dict[int, float],
    names: dict[int, str],
) -> list[tuple[int, float, int]]:
    """
    점수가 높은 순서로 학생 순위를 계산한다.

    동점자는 같은 순위를 사용하고,
    이름을 가나다순 보조 정렬 기준으로 사용한다.

    예:
        4.5 → 1위
        4.2 → 2위
        4.2 → 2위
        3.8 → 4위
    """

    sorted_ids = sorted(
        scores.keys(),
        key=lambda student_id: (
            -scores[student_id],
            names.get(student_id, ""),
        ),
    )

    rankings = []

    for index, student_id in enumerate(sorted_ids):
        score = scores[student_id]

        if (
            index > 0
            and score == scores[sorted_ids[index - 1]]
        ):
            rank = rankings[index - 1][2]
        else:
            rank = index + 1

        rankings.append(
            (student_id, score, rank)
        )

    return rankings


# ==============================================================================
# 팀 순위 계산
# ==============================================================================

def calculate_team_rankings(
    team_scores_or_round,
    team_names: dict[int, str] | None = None,
):
    """
    팀별 점수를 받아 팀 순위를 계산한다.

    dict를 전달하면:
        [(team_id, score, rank), ...]

    EvaluationRound 객체 또는 round_id를 전달하면:
        [
            {
                "team_id": ...,
                "team_name": ...,
                "score": ...,
                "rank": ...,
            }
        ]
    """

    # --------------------------------------------------------------------------
    # Round 객체 또는 round_id가 들어온 경우
    # --------------------------------------------------------------------------

    if not isinstance(team_scores_or_round, dict):
        round_obj = team_scores_or_round

        round_id = (
            round_obj.id
            if hasattr(round_obj, "id")
            else round_obj
        )

        teams = Team.objects.filter(round_id=round_id)

        team_scores = {}
        team_names_dict = {}

        for team in teams:
            score = get_team_score_from_db(
                round_id,
                team.id,
            )

            if score is not None:
                team_scores[team.id] = score
                team_names_dict[team.id] = team.name

        if not team_scores:
            return []

        sorted_team_ids = sorted(
            team_scores.keys(),
            key=lambda team_id: (
                -team_scores[team_id],
                team_names_dict.get(team_id, ""),
            ),
        )

        rankings = []

        for index, team_id in enumerate(sorted_team_ids):
            score = team_scores[team_id]

            if (
                index > 0
                and score
                == team_scores[sorted_team_ids[index - 1]]
            ):
                rank = rankings[index - 1]["rank"]
            else:
                rank = index + 1

            rankings.append(
                {
                    "team_id": team_id,
                    "team_name": team_names_dict[team_id],
                    "score": score,
                    "rank": rank,
                }
            )

        return rankings

    # --------------------------------------------------------------------------
    # 기존 dict 방식
    # --------------------------------------------------------------------------

    team_scores = team_scores_or_round

    if team_names is None:
        team_names = {}

    sorted_team_ids = sorted(
        team_scores.keys(),
        key=lambda team_id: (
            -team_scores[team_id],
            team_names.get(team_id, ""),
        ),
    )

    rankings = []

    for index, team_id in enumerate(sorted_team_ids):
        score = team_scores[team_id]

        if (
            index > 0
            and score
            == team_scores[sorted_team_ids[index - 1]]
        ):
            rank = rankings[index - 1][2]
        else:
            rank = index + 1

        rankings.append(
            (team_id, score, rank)
        )

    return rankings


# ==============================================================================
# 학생 + 튜터 평가 비율 계산
# ==============================================================================

def calculate_axis_score(
    student_score: float,
    tutor_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    """
    학생 평가와 튜터 평가를 가중 평균한다.

    점수는 1~5점 척도를 그대로 사용한다.

    예:
        학생 4.2
        튜터 4.5
        학생 70%
        튜터 30%

        결과 = 4.29
    """

    # 튜터 평가를 사용하지 않는 경우
    # 학생 평가 점수를 그대로 사용한다.
    if tutor_score is None:
        return student_score

    return (
        student_score * student_weight
        + tutor_score * tutor_weight
    )


def calculate_team_score(
    student_team_score: float,
    tutor_team_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    """
    최종 팀 평가점수를 계산한다.
    """

    return calculate_axis_score(
        student_team_score,
        tutor_team_score,
        student_weight,
        tutor_weight,
    )


def calculate_individual_score(
    student_individual_score: float,
    tutor_individual_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    """
    최종 개인 평가점수를 계산한다.
    """

    return calculate_axis_score(
        student_individual_score,
        tutor_individual_score,
        student_weight,
        tutor_weight,
    )


# ==============================================================================
# 최종 점수 계산
# ==============================================================================

def calculate_final_score(
    team_score: float,
    individual_score: float,
    team_weight: float = 0.4,
    individual_weight: float = 0.6,
) -> float:
    """
    팀 40% + 개인 60%로 최종 점수를 계산한다.

    점수는 1~5점 척도를 그대로 유지한다.

    예:
        팀 4.29
        개인 3.92

        4.29 × 0.4
        + 3.92 × 0.6
        = 4.068
    """

    return (
        team_score * team_weight
        + individual_score * individual_weight
    )


# ==============================================================================
# 평균 계산
# ==============================================================================

def calculate_average(
    scores: list[float],
) -> float | None:
    """
    모든 평가 점수의 평균을 계산한다.

    최저점 제거 ❌
    최고점 제거 ❌

    모든 점수를 그대로 평균낸다.

    예:
        [4.0, 5.0, 3.0, 4.0]
        → 4.0
    """

    if not scores:
        return None

    return sum(scores) / len(scores)


def calculate_average_excluding_missing(
    scores: list[float | None],
) -> float | None:
    """
    None을 제외하고 모든 점수의 평균을 계산한다.

    최저점/최고점 제거는 하지 않는다.
    """

    valid_scores = [
        score
        for score in scores
        if score is not None
    ]

    if not valid_scores:
        return None

    return sum(valid_scores) / len(valid_scores)


# ==============================================================================
# 팀 평가 점수 조회
# ==============================================================================

def get_team_score_from_db(
    round_id: int,
    team_id: int,
) -> float | None:
    """
    특정 팀이 받은 학생 팀 평가 점수를 계산한다.

    최종 제출(is_final=True)된 평가만 사용한다.

    모든 평가 점수를 그대로 평균한다.
    최저점/최고점 제거 없음.

    점수는 1~5점 척도를 그대로 유지한다.
    """

    scores = list(
        TeamEvaluation.objects.filter(
            round_id=round_id,
            target_team_id=team_id,
            is_final=True,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average(scores)


# ==============================================================================
# 개인 평가 점수 조회
# ==============================================================================

def get_individual_score_from_db(
    round_id: int,
    student_id: int,
) -> float | None:
    """
    특정 학생이 받은 학생 개인 평가 점수를 계산한다.

    최종 제출(is_final=True)된 평가만 사용한다.

    모든 평가 점수를 그대로 평균한다.
    최저점/최고점 제거 없음.

    점수는 1~5점 척도를 그대로 유지한다.
    """

    scores = list(
        IndividualEvaluation.objects.filter(
            round_id=round_id,
            target_id=student_id,
            is_final=True,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average(scores)


# ==============================================================================
# 튜터 팀 평가 점수 조회
# ==============================================================================

def get_tutor_team_score_from_db(
    round_id: int,
    team_id: int,
) -> float | None:
    """
    특정 팀이 받은 튜터 팀 평가 점수를 계산한다.

    모든 튜터 평가 점수를 그대로 평균한다.
    """

    scores = list(
        TutorEvaluation.objects.filter(
            round_id=round_id,
            team_id=team_id,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average(scores)


# ==============================================================================
# 튜터 개인 평가 점수 조회
# ==============================================================================

def get_tutor_individual_score_from_db(
    round_id: int,
    student_id: int,
) -> float | None:
    """
    특정 학생이 받은 튜터 개인 평가 점수를 계산한다.

    모든 튜터 평가 점수를 그대로 평균한다.
    """

    scores = list(
        TutorEvaluation.objects.filter(
            round_id=round_id,
            user_id=student_id,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average(scores)


# ==============================================================================
# 학생 1명 점수 계산
# ==============================================================================

def calculate_student_result(
    round,
    student_id: int,
    team_id: int,
) -> dict:
    """
    학생 1명의 팀/개인/최종 점수를 계산한다.

    점수는 모두 1~5점 척도를 그대로 사용한다.

    계산 순서:

    1. 학생 팀 평가 평균
    2. 튜터 팀 평가 평균
    3. 학생/튜터 비율 적용 → 팀 점수

    4. 학생 개인 평가 평균
    5. 튜터 개인 평가 평균
    6. 학생/튜터 비율 적용 → 개인 점수

    7. 팀 점수 × 40%
       + 개인 점수 × 60%
       → 최종 점수
    """

    # --------------------------------------------------------------------------
    # 학생 팀 평가
    # --------------------------------------------------------------------------

    student_team_score = get_team_score_from_db(
        round.id,
        team_id,
    )

    # --------------------------------------------------------------------------
    # 학생 개인 평가
    # --------------------------------------------------------------------------

    student_individual_score = get_individual_score_from_db(
        round.id,
        student_id,
    )

    # --------------------------------------------------------------------------
    # 튜터 팀 평가
    # --------------------------------------------------------------------------

    tutor_team_score = get_tutor_team_score_from_db(
        round.id,
        team_id,
    )

    # --------------------------------------------------------------------------
    # 튜터 개인 평가
    # --------------------------------------------------------------------------

    tutor_individual_score = get_tutor_individual_score_from_db(
        round.id,
        student_id,
    )

    # --------------------------------------------------------------------------
    # 팀 점수 계산
    # --------------------------------------------------------------------------

    team_score = None

    if student_team_score is not None:
        team_score = calculate_team_score(
            student_team_score,
            tutor_team_score,
            round.student_weight,
            round.tutor_weight,
        )

    # --------------------------------------------------------------------------
    # 개인 점수 계산
    # --------------------------------------------------------------------------

    individual_score = None

    if student_individual_score is not None:
        individual_score = calculate_individual_score(
            student_individual_score,
            tutor_individual_score,
            round.student_weight,
            round.tutor_weight,
        )

    # --------------------------------------------------------------------------
    # 둘 중 하나라도 없으면 최종점수 계산 불가
    # --------------------------------------------------------------------------

    if team_score is None or individual_score is None:
        return {
            "team_score": team_score,
            "individual_score": individual_score,
            "final_score": None,
        }

    # --------------------------------------------------------------------------
    # 최종 점수
    #
    # 팀 40% + 개인 60%
    # --------------------------------------------------------------------------

    final_score = calculate_final_score(
        team_score,
        individual_score,
        round.team_weight,
        round.individual_weight,
    )

    return {
        "team_score": team_score,
        "individual_score": individual_score,
        "final_score": final_score,
    }


# ==============================================================================
# 회차 전체 점수 계산 및 ScoreResult 저장
# ==============================================================================

@transaction.atomic
def calculate_round(round) -> list[dict]:
    """
    특정 평가 회차의 모든 학생 점수를 계산하고
    ScoreResult 테이블에 저장한다.

    계산되지 않은 학생은 ScoreResult에 저장하지 않는다.
    """

    team_members = list(
        TeamMember.objects.filter(
            team__round=round,
        ).select_related(
            "student",
            "team",
        )
    )

    calculated_results = []

    for membership in team_members:
        student = membership.student
        team = membership.team

        result = calculate_student_result(
            round,
            student.id,
            team.id,
        )

        if (
            result["team_score"] is None
            or result["individual_score"] is None
            or result["final_score"] is None
        ):
            continue

        calculated_results.append(
            {
                "student": student,
                "team": team,
                "team_score": result["team_score"],
                "individual_score": result["individual_score"],
                "final_score": result["final_score"],
            }
        )

    if not calculated_results:
        return []

    # --------------------------------------------------------------------------
    # 학생별 최종점수로 순위 계산
    # --------------------------------------------------------------------------

    scores = {
        item["student"].id: item["final_score"]
        for item in calculated_results
    }

    names = {
        item["student"].id: str(item["student"])
        for item in calculated_results
    }

    rankings = calculate_rankings(
        scores,
        names,
    )

    rank_by_student_id = {
        student_id: rank
        for student_id, score, rank in rankings
    }

    # --------------------------------------------------------------------------
    # ScoreResult 저장
    # --------------------------------------------------------------------------

    saved_results = []

    for item in calculated_results:
        student = item["student"]
        team = item["team"]

        score_result, created = ScoreResult.objects.update_or_create(
            round=round,
            user=student,
            team=team,
            defaults={
                "team_score": item["team_score"],
                "individual_score": item["individual_score"],
                "final_score": item["final_score"],
                "rank": rank_by_student_id[student.id],
            },
        )

        saved_results.append(
            {
                "score_result": score_result,
                "created": created,
            }
        )

    return saved_results


# ==============================================================================
# 누적 시드 저장
# ==============================================================================

@transaction.atomic
def save_cumulative_seeds(
    round_id: int,
) -> dict[int, float]:
    """
    종료된 평가 회차의 최종 점수를 기준으로
    학생별 누적 시드를 계산하고 저장한다.

    누적 시드
    = 종료된 모든 회차의 최종 점수 평균
    """

    results = (
        ScoreResult.objects
        .filter(
            round__status="finished",
            round_id__lte=round_id,
        )
        .values(
            "user_id",
            "round_id",
            "team_id",
            "final_score",
        )
        .order_by(
            "user_id",
            "round_id",
        )
    )

    student_scores: dict[int, list[float]] = {}
    latest_team: dict[int, int] = {}

    for result in results:
        user_id = result["user_id"]
        final_score = result["final_score"]

        if final_score is None:
            continue

        student_scores.setdefault(
            user_id,
            [],
        ).append(final_score)

        latest_team[user_id] = result["team_id"]

    saved_seeds: dict[int, float] = {}

    for user_id, scores in student_scores.items():
        cumulative_seed = sum(scores) / len(scores)

        TeamUserScoreSeed.objects.update_or_create(
            user_id=user_id,
            round_id=round_id,
            defaults={
                "team_id": latest_team[user_id],
                "cumulative_seed": cumulative_seed,
            },
        )

        saved_seeds[user_id] = cumulative_seed

    return saved_seeds


# ==============================================================================
# 누적 시드 조회
# ==============================================================================

def get_cumulative_seed(
    user_id: int,
    round_id: int,
) -> float | None:
    """
    특정 학생의 특정 평가 회차 누적 시드를 조회한다.

    해당 회차에 직접 저장된 시드가 없으면
    가장 최근 누적 시드를 조회한다.
    """

    seed = (
        TeamUserScoreSeed.objects
        .filter(
            user_id=user_id,
            round_id=round_id,
        )
        .values_list(
            "cumulative_seed",
            flat=True,
        )
        .first()
    )

    if seed is None:
        seed = (
            TeamUserScoreSeed.objects
            .filter(
                user_id=user_id,
                round_id__lte=round_id,
            )
            .order_by("-round_id")
            .values_list(
                "cumulative_seed",
                flat=True,
            )
            .first()
        )

    return seed