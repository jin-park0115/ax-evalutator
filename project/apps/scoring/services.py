def calculate_seed_scores(round_scores: list[dict[int, float]]) -> dict[int, float]:
    totals: dict[int, float] = {}
    counts: dict[int, int] = {}

    for scores in round_scores:
        for student_id, score in scores.items():
            totals[student_id] = totals.get(student_id, 0.0) + score
            counts[student_id] = counts.get(student_id, 0) + 1

    return {student_id: totals[student_id] / counts[student_id] for student_id in totals}


def calculate_rankings(scores: dict[int, float]) -> list[tuple[int, float, int]]:
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [(student_id, score, index + 1) for index, (student_id, score) in enumerate(sorted_scores)]


def calculate_seeds(round_scores: list[dict[int, float]]) -> dict[int, float]:
    return calculate_seed_scores(round_scores)


def calculate_axis_score(
    student_score: float,
    tutor_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    if tutor_score is None:
        return student_score
    return student_score * student_weight + tutor_score * tutor_weight


def calculate_team_score(
    student_team_score: float,
    tutor_team_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    return calculate_axis_score(
        student_team_score, tutor_team_score, student_weight, tutor_weight
    )


def calculate_individual_score(
    student_individual_score: float,
    tutor_individual_score: float | None,
    student_weight: float,
    tutor_weight: float,
) -> float:
    return calculate_axis_score(
        student_individual_score, tutor_individual_score, student_weight, tutor_weight
    )


def calculate_final_score(
    team_score: float,
    individual_score: float,
    team_weight: float = 0.4,
    individual_weight: float = 0.6,
) -> float:
    return team_score * team_weight + individual_score * individual_weight

def calculate_trimmed_mean(scores: list[float]) -> float:
    if len(scores) < 5:
        return sum(scores) / len(scores)
    sorted_scores = sorted(scores)
    trimmed = sorted_scores[1:-1]
    return sum(trimmed) / len(trimmed)


def calculate_average_excluding_missing(scores: list[float | None]) -> float | None:
    valid_scores = [score for score in scores if score is not None]
    if not valid_scores:
        return None
    return sum(valid_scores) / len(valid_scores)