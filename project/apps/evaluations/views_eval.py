from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.evaluations import services
from apps.evaluations.models import (
    EvaluationRound,
    EvaluationTemplate,
    IndividualEvaluation,
    TeamEvaluation,
)
from apps.teams.models import Team, TeamMember


def _current_round():
    return (
        EvaluationRound.objects.filter(
            status=EvaluationRound.Status.IN_PROGRESS
        )
        .order_by("-id")
        .first()
        or EvaluationRound.objects.order_by("-id").first()
    )


def _get_my_team(user, round_obj):
    if not round_obj:
        return None

    membership = (
        TeamMember.objects.filter(
            student=user,
            team__round=round_obj,
        )
        .select_related("team")
        .first()
    )

    return membership.team if membership else None


def _get_template_items(round_obj, template_type):
    if not round_obj:
        return []

    template = EvaluationTemplate.objects.filter(
        round=round_obj,
        type=template_type,
    ).first()

    if not template or not isinstance(template.criteria, list):
        return []

    return template.criteria


# =========================================================
# 팀 평가 최종 제출 여부
# =========================================================
def _has_team_finalized(user, round_obj):
    if not round_obj:
        return False

    return TeamEvaluation.objects.filter(
        round=round_obj,
        submitted_by=user,
        is_final=True,
    ).exists()


# =========================================================
# 개인 평가 최종 제출 여부
# =========================================================
def _has_individual_finalized(user, round_obj):
    if not round_obj:
        return False

    return IndividualEvaluation.objects.filter(
        round=round_obj,
        evaluator=user,
        is_final=True,
    ).exists()


# =========================================================
# 팀 평가 목록
# =========================================================
@login_required
def team_evaluation_list(request):
    round_obj = _current_round()
    my_team = _get_my_team(request.user, round_obj)

    team_finalized = _has_team_finalized(
        request.user,
        round_obj,
    )

    teams = Team.objects.none()
    saved_team_ids = set()

    if round_obj:
        teams = Team.objects.filter(
            round=round_obj,
            eval_opened_at__isnull=False,
        )

        if my_team:
            teams = teams.exclude(id=my_team.id)

        teams = teams.order_by(
            "eval_opened_at",
            "id",
        )

        saved_team_ids = set(
            TeamEvaluation.objects.filter(
                round=round_obj,
                submitted_by=request.user,
            ).values_list(
                "target_team_id",
                flat=True,
            )
        )

    return render(
        request,
        "eval/team_evaluation_list.html",
        {
            "round": round_obj,
            "my_team": my_team,
            "teams": teams,
            "saved_team_ids": saved_team_ids,
            "finalized": team_finalized,
            "team_finalized": team_finalized,
        },
    )


# =========================================================
# 팀 평가 작성
# =========================================================
@login_required
def team_evaluation_form(request, team_id):
    round_obj = _current_round()
    target_team = get_object_or_404(
        Team,
        id=team_id,
    )
    my_team = _get_my_team(
        request.user,
        round_obj,
    )

    team_finalized = _has_team_finalized(
        request.user,
        round_obj,
    )

    if not round_obj:
        messages.error(
            request,
            "현재 평가 회차가 없습니다.",
        )
        return redirect("eval_team_list")

    if target_team.round_id != round_obj.id:
        messages.error(
            request,
            "현재 평가 회차의 팀이 아닙니다.",
        )
        return redirect("eval_team_list")

    if my_team and my_team.id == target_team.id:
        messages.error(
            request,
            "본인 팀은 평가할 수 없습니다.",
        )
        return redirect("eval_team_list")

    if not target_team.eval_opened_at:
        messages.error(
            request,
            "아직 평가가 열리지 않은 팀입니다.",
        )
        return redirect("eval_team_list")

    if team_finalized:
        messages.error(
            request,
            "팀 평가 최종 제출을 완료하여 더 이상 수정할 수 없습니다.",
        )
        return redirect("eval_team_list")

    items = _get_template_items(
        round_obj,
        EvaluationTemplate.TemplateType.TEAM,
    )

    existing = TeamEvaluation.objects.filter(
        round=round_obj,
        submitted_by=request.user,
        target_team=target_team,
    ).first()

    existing_answers = (
        existing.responses
        if existing
        else {}
    )

    display_items = [
        {
            **item,
            "existing_value": existing_answers.get(
                item.get("key")
            ),
        }
        for item in items
    ]

    if request.method == "POST":
        answers = {}

        for item in items:
            key = item.get("key")
            value = request.POST.get(
                f"item_{key}"
            )

            if value:
                try:
                    answers[key] = int(value)
                except (TypeError, ValueError):
                    messages.error(
                        request,
                        "점수 형식이 올바르지 않습니다.",
                    )
                    return render(
                        request,
                        "eval/team_evaluation_form.html",
                        {
                            "round": round_obj,
                            "target_team": target_team,
                            "items": display_items,
                            "existing_answers": existing_answers,
                        },
                    )

        if not items:
            messages.error(
                request,
                "등록된 팀 평가 문항이 없습니다.",
            )
        elif len(answers) != len(items):
            messages.error(
                request,
                "모든 문항에 응답해야 합니다.",
            )
        elif any(
            score < 1 or score > 5
            for score in answers.values()
        ):
            messages.error(
                request,
                "평가는 1점에서 5점까지 입력할 수 있습니다.",
            )
        else:
            avg_score = (
                sum(answers.values())
                / len(answers)
            )

            try:
                services.save_team_evaluation(
                    round_id=round_obj.id,
                    evaluator_id=request.user.id,
                    target_team_id=target_team.id,
                    score=avg_score,
                    responses=answers,
                    is_final=False,
                )
            except ValueError as exc:
                messages.error(
                    request,
                    str(exc),
                )
                return redirect(
                    "eval_team_list"
                )

            messages.success(
                request,
                f"{target_team.name} 팀 평가가 저장되었습니다.",
            )

            return redirect(
                "eval_team_list"
            )

    return render(
        request,
        "eval/team_evaluation_form.html",
        {
            "round": round_obj,
            "target_team": target_team,
            "items": display_items,
            "existing_answers": existing_answers,
            "team_finalized": team_finalized,
            "finalized": team_finalized,
        },
    )


# =========================================================
# 개인 평가 행 생성
# =========================================================
def _build_member_rows(
    members,
    items,
    existing_answers,
):
    rows = []

    for member in members:
        member_answers = existing_answers.get(
            member.student_id,
            {},
        )

        rows.append(
            {
                "member": member,
                "items": [
                    {
                        **item,
                        "existing_value": member_answers.get(
                            item.get("key")
                        ),
                    }
                    for item in items
                ],
            }
        )

    return rows


# =========================================================
# 개인 평가 작성
# =========================================================
@login_required
def peer_evaluation_form(request):
    round_obj = _current_round()
    my_team = _get_my_team(
        request.user,
        round_obj,
    )

    individual_finalized = _has_individual_finalized(
        request.user,
        round_obj,
    )

    members = TeamMember.objects.none()

    if my_team and round_obj:
        members = (
            TeamMember.objects.filter(
                team=my_team
            )
            .exclude(
                student=request.user
            )
            .select_related("student")
        )

    items = _get_template_items(
        round_obj,
        EvaluationTemplate.TemplateType.INDIVIDUAL,
    )

    existing_answers = {}

    if round_obj:
        evaluations = IndividualEvaluation.objects.filter(
            round=round_obj,
            evaluator=request.user,
        )

        for evaluation in evaluations:
            existing_answers[
                evaluation.target_id
            ] = evaluation.responses

    if request.method == "POST":

        if individual_finalized:
            messages.error(
                request,
                "개인 평가 최종 제출을 완료하여 더 이상 수정할 수 없습니다.",
            )
            return redirect(
                "eval_peer_form"
            )

        if not round_obj:
            messages.error(
                request,
                "현재 평가 회차가 없습니다.",
            )
            return redirect(
                "eval_peer_form"
            )

        if not my_team:
            messages.error(
                request,
                "소속 팀이 없어 개인 평가를 진행할 수 없습니다.",
            )
            return redirect(
                "eval_peer_form"
            )

        member_answers = {}

        for member in members:
            answers = {}

            for item in items:
                key = item.get("key")

                value = request.POST.get(
                    f"item_{member.student.id}_{key}"
                )

                if value:
                    try:
                        answers[key] = int(value)
                    except (TypeError, ValueError):
                        messages.error(
                            request,
                            f"{member.student.username} 학생의 점수 형식이 올바르지 않습니다.",
                        )

                        return render(
                            request,
                            "eval/peer_evaluation_form.html",
                            {
                                "round": round_obj,
                                "member_rows": _build_member_rows(
                                    members,
                                    items,
                                    existing_answers,
                                ),
                                "finalized": individual_finalized,
                                "individual_finalized": individual_finalized,
                            },
                        )

            if not items:
                messages.error(
                    request,
                    "등록된 개인 평가 문항이 없습니다.",
                )

                return render(
                    request,
                    "eval/peer_evaluation_form.html",
                    {
                        "round": round_obj,
                        "member_rows": _build_member_rows(
                            members,
                            items,
                            existing_answers,
                        ),
                        "finalized": individual_finalized,
                        "individual_finalized": individual_finalized,
                    },
                )

            elif len(answers) != len(items):
                messages.error(
                    request,
                    f"{member.student.username} 학생에 대한 모든 문항에 응답해야 합니다.",
                )

                return render(
                    request,
                    "eval/peer_evaluation_form.html",
                    {
                        "round": round_obj,
                        "member_rows": _build_member_rows(
                            members,
                            items,
                            existing_answers,
                        ),
                        "finalized": individual_finalized,
                        "individual_finalized": individual_finalized,
                    },
                )

            if any(
                score < 1 or score > 5
                for score in answers.values()
            ):
                messages.error(
                    request,
                    "평가는 1점에서 5점까지 입력할 수 있습니다.",
                )

                return render(
                    request,
                    "eval/peer_evaluation_form.html",
                    {
                        "round": round_obj,
                        "member_rows": _build_member_rows(
                            members,
                            items,
                            existing_answers,
                        ),
                        "finalized": individual_finalized,
                        "individual_finalized": individual_finalized,
                    },
                )

            member_answers[member] = answers

        try:
            with transaction.atomic():
                for member, answers in member_answers.items():

                    avg_score = (
                        sum(answers.values())
                        / len(answers)
                    )

                    services.save_individual_evaluation(
                        round_id=round_obj.id,
                        team_id=my_team.id,
                        evaluator_id=request.user.id,
                        target_id=member.student.id,
                        score=avg_score,
                        responses=answers,
                        is_final=False,
                    )

        except ValueError as exc:
            messages.error(
                request,
                str(exc),
            )

            return render(
                request,
                "eval/peer_evaluation_form.html",
                {
                    "round": round_obj,
                    "member_rows": _build_member_rows(
                        members,
                        items,
                        existing_answers,
                    ),
                    "finalized": individual_finalized,
                    "individual_finalized": individual_finalized,
                },
            )

        messages.success(
            request,
            "개인 평가가 저장되었습니다.",
        )

        return redirect(
            "eval_peer_form"
        )

    return render(
        request,
        "eval/peer_evaluation_form.html",
        {
            "round": round_obj,
            "member_rows": _build_member_rows(
                members,
                items,
                existing_answers,
            ),
            "finalized": individual_finalized,
            "individual_finalized": individual_finalized,
        },
    )


# =========================================================
# 팀 평가 최종 제출
#
# 팀 평가만 is_final=True 처리
# 개인 평가에는 영향을 주지 않음
# =========================================================
@login_required
def submit_team_final(request):
    round_obj = _current_round()

    if not round_obj:
        messages.error(
            request,
            "현재 진행 중인 평가 회차가 없습니다.",
        )
        return redirect(
            "eval_team_list"
        )

    if request.method != "POST":
        return redirect(
            "eval_team_list"
        )

    if _has_team_finalized(
        request.user,
        round_obj,
    ):
        messages.error(
            request,
            "이미 팀 평가 최종 제출을 완료했습니다.",
        )
        return redirect(
            "eval_team_list"
        )

    with transaction.atomic():
        TeamEvaluation.objects.filter(
            round=round_obj,
            submitted_by=request.user,
            is_final=False,
        ).update(
            is_final=True
        )

    messages.success(
        request,
        "팀 평가 최종 제출이 완료되었습니다. 이후 팀 평가를 수정할 수 없습니다.",
    )

    return redirect(
        "eval_team_list"
    )


# =========================================================
# 개인 평가 최종 제출
#
# 개인 평가만 is_final=True 처리
# 팀 평가에는 영향을 주지 않음
# =========================================================
@login_required
def submit_individual_final(request):
    round_obj = _current_round()

    if not round_obj:
        messages.error(
            request,
            "현재 진행 중인 평가 회차가 없습니다.",
        )
        return redirect(
            "eval_peer_form"
        )

    if request.method != "POST":
        return redirect(
            "eval_peer_form"
        )

    if _has_individual_finalized(
        request.user,
        round_obj,
    ):
        messages.error(
            request,
            "이미 개인 평가 최종 제출을 완료했습니다.",
        )
        return redirect(
            "eval_peer_form"
        )

    with transaction.atomic():
        IndividualEvaluation.objects.filter(
            round=round_obj,
            evaluator=request.user,
            is_final=False,
        ).update(
            is_final=True
        )

    messages.success(
        request,
        "개인 평가 최종 제출이 완료되었습니다. 이후 개인 평가를 수정할 수 없습니다.",
    )

    return redirect(
        "eval_peer_form"
    )