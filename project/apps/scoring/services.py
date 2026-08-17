from apps.evaluations.models import (
    IndividualEvaluation,
    TeamEvaluation,
    TutorEvaluation,
    ScoreResult,
)
from apps.teams.models import TeamMember


def calculate_seed_scores(
    round_scores: list[dict[int, float]],
) -> dict[int, float]:
    """
    여러 회차의 학생별 점수를 받아
    학생별 평균 점수를 계산한다.

    예:
    1회차: {1: 80, 2: 90}
    2회차: {1: 90, 2: 80}

    결과:
    {1: 85, 2: 85}
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

        student_scores.setdefault(student_id, []).append(final_score)

    return {
        student_id: sum(scores) / len(scores)
        for student_id, scores in student_scores.items()
    }


def calculate_rankings(
    scores: dict[int, float],
    names: dict[int, str],
) -> list[tuple[int, float, int]]:
    """
    점수가 높은 순서로 석차를 계산한다.

    동점자는 같은 석차를 사용하고,
    이름을 보조 정렬 기준으로 사용한다.
    """

    sorted_ids = sorted(
        scores.keys(),
        key=lambda student_id: (
            -scores[student_id],
            names[student_id],
        ),
    )

    rankings = []

    for index, student_id in enumerate(sorted_ids):
        score = scores[student_id]

        if index > 0 and score == scores[sorted_ids[index - 1]]:
            rank = rankings[index - 1][2]
        else:
            rank = index + 1

        rankings.append(
            (student_id, score, rank)
        )

    return rankings


def calculate_axis_score(
    student_score: float,
    tutor_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
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
    return calculate_axis_score(
        student_individual_score,
        tutor_individual_score,
        student_weight,
        tutor_weight,
    )


def calculate_final_score(
    team_score: float,
    individual_score: float,
    team_weight: float = 0.4,
    individual_weight: float = 0.6,
) -> float:
    return (
        team_score * team_weight
        + individual_score * individual_weight
    )


def calculate_trimmed_mean(
    scores: list[float],
) -> float:
    if len(scores) < 5:
        return sum(scores) / len(scores)

    sorted_scores = sorted(scores)
    trimmed = sorted_scores[1:-1]

    return sum(trimmed) / len(trimmed)


def calculate_average_excluding_missing(
    scores: list[float | None],
) -> float | None:
    valid_scores = [
        score
        for score in scores
        if score is not None
    ]

    if not valid_scores:
        return None

    return sum(valid_scores) / len(valid_scores)


def get_team_score_from_db(
    round_id: int,
    team_id: int,
) -> float | None:
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

    return calculate_average_excluding_missing(scores)


def get_individual_score_from_db(
    round_id: int,
    student_id: int,
) -> float | None:
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

    return (
        calculate_trimmed_mean(scores)
        if len(scores) >= 1
        else None
    )


def get_tutor_team_score_from_db(
    round_id: int,
    team_id: int,
) -> float | None:
    scores = list(
        TutorEvaluation.objects.filter(
            round_id=round_id,
            team_id=team_id,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average_excluding_missing(scores)


def get_tutor_individual_score_from_db(
    round_id: int,
    student_id: int,
) -> float | None:
    scores = list(
        TutorEvaluation.objects.filter(
            round_id=round_id,
            user_id=student_id,
        ).values_list(
            "score",
            flat=True,
        )
    )

    return calculate_average_excluding_missing(scores)


def calculate_student_result(
    round,
    student_id: int,
    team_id: int,
) -> dict:
    """
    학생 1명의 팀/개인/최종 점수를 계산한다.

    팀 평가 또는 개인 평가가 아직 없는 경우
    해당 점수는 None으로 처리하고,
    최종 점수도 None으로 반환한다.

    이렇게 하면 평가가 덜 끝난 학생 때문에
    전체 calculate_round()가 중단되지 않는다.
    """

    student_team_score = get_team_score_from_db(
        round.id,
        team_id,
    )

    student_individual_score = get_individual_score_from_db(
        round.id,
        student_id,
    )

    tutor_team_score = get_tutor_team_score_from_db(
        round.id,
        team_id,
    )

    tutor_individual_score = get_tutor_individual_score_from_db(
        round.id,
        student_id,
    )

    # 팀 평가 또는 개인 평가가 아직 없는 경우
    if student_team_score is None or student_individual_score is None:
        team_score = (
            calculate_team_score(
                student_team_score,
                tutor_team_score,
                round.student_weight,
                round.tutor_weight,
            )
            if student_team_score is not None
            else None
        )

        individual_score = (
            calculate_individual_score(
                student_individual_score,
                tutor_individual_score,
                round.student_weight,
                round.tutor_weight,
            )
            if student_individual_score is not None
            else None
        )

        return {
            "team_score": team_score,
            "individual_score": individual_score,
            "final_score": None,
        }

    # 팀 평가와 개인 평가가 모두 존재하는 경우에만
    # 팀 점수, 개인 점수, 최종 점수를 계산한다.
    team_score = calculate_team_score(
        student_team_score,
        tutor_team_score,
        round.student_weight,
        round.tutor_weight,
    )

    individual_score = calculate_individual_score(
        student_individual_score,
        tutor_individual_score,
        round.student_weight,
        round.tutor_weight,
    )

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


def calculate_round(round) -> list[dict]:
    """
    특정 평가 회차의 모든 학생 점수를 계산하고
    ScoreResult 테이블에 저장한다.

    처리 순서:
    1. 해당 회차의 팀에 속한 학생을 조회한다.
    2. 학생별 팀/개인/최종 점수를 계산한다.
    3. 최종 점수를 기준으로 전체 석차를 계산한다.
    4. ScoreResult에 결과를 저장하거나 갱신한다.

    아직 평가가 완료되지 않은 학생은 결과를 저장하지 않는다.
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

        # 평가가 덜 끝난 학생은 건너뛴다.
        # 다른 학생들의 계산은 계속 진행된다.
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