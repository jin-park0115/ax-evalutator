def assign_teams(student_ids: list[int], team_size: int = 5) -> list[list[int]]:
    if team_size <= 0:
        raise ValueError("team_size must be greater than 0")

    return [student_ids[index : index + team_size] for index in range(0, len(student_ids), team_size)]

