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
