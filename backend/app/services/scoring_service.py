from app.algorithms.seed_calculator import calculate_seed_scores


def calculate_rankings(scores: dict[int, float]) -> list[tuple[int, float, int]]:
    sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return [(student_id, score, index + 1) for index, (student_id, score) in enumerate(sorted_scores)]


def calculate_seeds(round_scores: list[dict[int, float]]) -> dict[int, float]:
    return calculate_seed_scores(round_scores)

