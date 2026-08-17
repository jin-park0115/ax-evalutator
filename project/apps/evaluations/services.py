from django.db import IntegrityError, transaction

from apps.evaluations.models import Evaluation, IndividualEvaluation


def create_evaluation(
    *,
    round_id: int,
    evaluator_id: int,
    target_id: int,
    score: int,
) -> Evaluation:
    if evaluator_id == target_id:
        raise ValueError("자기 자신은 평가할 수 없습니다.")

    if not (1 <= score <= 5):
        raise ValueError("점수는 1점에서 5점 사이여야 합니다.")

    try:
        with transaction.atomic():
            return Evaluation.objects.create(
                round_id=round_id,
                evaluator_id=evaluator_id,
                target_id=target_id,
                score=score,
            )
    except IntegrityError:
        raise ValueError(
            "Evaluation already exists for this evaluator and target."
        )


def save_team_evaluation(
    *,
    round_id: int,
    evaluator_id: int,
    target_team_id: int,
    score: int,
    responses: dict | None = None,
    is_final: bool = False,
) -> TeamEvaluation:
    """
    학생의 팀평가를 임시저장하거나 최종 제출한다.

    - 자기 팀 평가 금지
    - 같은 평가 회차의 팀만 평가 가능
    - 점수는 1~5점
    - 기존 임시저장 평가가 있으면 수정
    - 최종 제출된 평가는 수정 불가
    """

    from apps.evaluations.models import TeamEvaluation
    from apps.teams.models import Team, TeamMember

    # 1. 평가 대상 팀 확인
    try:
        target_team = Team.objects.get(
            id=target_team_id,
            round_id=round_id,
        )
    except Team.DoesNotExist:
        raise ValueError("해당 평가 회차에 존재하지 않는 팀입니다.")

    # 2. 평가자의 팀 확인
    membership = (
        TeamMember.objects
        .select_related("team")
        .filter(
            student_id=evaluator_id,
            team__round_id=round_id,
        )
        .first()
    )

    if membership is None:
        raise ValueError("해당 평가 회차에 소속된 팀이 없습니다.")

    evaluator_team = membership.team

    # 3. 자기 팀 평가 방지
    if evaluator_team.id == target_team.id:
        raise ValueError("자기 팀은 평가할 수 없습니다.")

    # 4. 점수 검증
    if not (1 <= score <= 5):
        raise ValueError("점수는 1점에서 5점 사이여야 합니다.")

    # 5. 기존 평가 확인 및 저장
    with transaction.atomic():
        evaluation = (
            TeamEvaluation.objects
            .select_for_update()
            .filter(
                round_id=round_id,
                evaluator_team_id=evaluator_team.id,
                target_team_id=target_team.id,
                submitted_by_id=evaluator_id,
            )
            .first()
        )

        # 이미 최종 제출된 평가라면 수정 불가
        if evaluation is not None and evaluation.is_final:
            raise ValueError("최종 제출된 평가는 수정할 수 없습니다.")

        # 기존 임시저장 평가가 있으면 수정
        if evaluation is not None:
            evaluation.score = score
            evaluation.responses = responses or {}
            evaluation.is_final = is_final

            evaluation.save(
                update_fields=[
                    "score",
                    "responses",
                    "is_final",
                ]
            )

            return evaluation

        # 처음 저장하는 평가
        return TeamEvaluation.objects.create(
            round_id=round_id,
            evaluator_team_id=evaluator_team.id,
            target_team_id=target_team.id,
            submitted_by_id=evaluator_id,
            score=score,
            responses=responses or {},
            is_final=is_final,
        )


def save_individual_evaluation(
    *,
    round_id: int,
    team_id: int,
    evaluator_id: int,
    target_id: int,
    score: int,
    responses: dict | None = None,
    is_final: bool = False,
) -> IndividualEvaluation:
    """
    학생이 다른 학생을 평가한다.

    - 자기 자신 평가 금지
    - 점수는 1~5점
    - 평가자와 대상자는 같은 평가 회차의 학생이어야 함
    - 임시저장 가능
    - 임시저장된 평가는 수정 가능
    - 최종 제출된 평가는 수정 불가
    """

    from apps.teams.models import Team, TeamMember

    # 1. 자기 자신 평가 방지
    if evaluator_id == target_id:
        raise ValueError("자기 자신은 평가할 수 없습니다.")

    # 2. 점수 검증
    if not (1 <= score <= 5):
        raise ValueError("점수는 1점에서 5점 사이여야 합니다.")

    # 3. 평가 대상 팀 확인
    try:
        team = Team.objects.get(
            id=team_id,
            round_id=round_id,
        )
    except Team.DoesNotExist:
        raise ValueError("해당 평가 회차에 존재하지 않는 팀입니다.")

    # 4. 평가자가 해당 회차의 학생인지 확인
    evaluator_membership = (
        TeamMember.objects
        .filter(
            student_id=evaluator_id,
            team__round_id=round_id,
        )
        .first()
    )

    if evaluator_membership is None:
        raise ValueError("평가자가 해당 평가 회차에 소속되어 있지 않습니다.")

    # 5. 평가 대상자가 해당 회차의 학생인지 확인
    target_membership = (
        TeamMember.objects
        .filter(
            student_id=target_id,
            team__round_id=round_id,
        )
        .first()
    )

    if target_membership is None:
        raise ValueError("평가 대상자가 해당 평가 회차에 소속되어 있지 않습니다.")

    # 6. 기존 평가 확인 및 저장
    with transaction.atomic():
        evaluation = (
            IndividualEvaluation.objects
            .select_for_update()
            .filter(
                round_id=round_id,
                evaluator_id=evaluator_id,
                target_id=target_id,
            )
            .first()
        )

        # 이미 최종 제출된 평가라면 수정 불가
        if evaluation is not None and evaluation.is_final:
            raise ValueError("최종 제출된 평가는 수정할 수 없습니다.")

        # 기존 임시저장 평가가 있으면 수정
        if evaluation is not None:
            evaluation.team = team
            evaluation.score = score
            evaluation.responses = responses or {}
            evaluation.is_final = is_final

            evaluation.save(
                update_fields=[
                    "team",
                    "score",
                    "responses",
                    "is_final",
                ]
            )

            return evaluation

        # 처음 저장하는 평가
        return IndividualEvaluation.objects.create(
            round_id=round_id,
            team_id=team_id,
            evaluator_id=evaluator_id,
            target_id=target_id,
            score=score,
            responses=responses or {},
            is_final=is_final,
        )