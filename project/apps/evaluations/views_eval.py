# apps/evaluations/views_eval.py
# BE2(전예진) 담당 서비스 함수가 아직 없어서, 계약(get_evaluable_teams 등)에
# 맞춰 실제 모델을 직접 조회/저장하는 임시 구현. BE2 함수가 나오면
# 표시된 지점만 그 함수 호출로 교체하면 된다.

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

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
    tm = (
        TeamMember.objects.filter(student=user, team__round=round_obj)
        .select_related("team")
        .first()
    )
    return tm.team if tm else None


def _get_template_items(round_obj, template_type):
    """get_template_items(round, type) 계약 — criteria가 list가 아니면 빈 목록 취급"""
    if not round_obj:
        return []
    template = EvaluationTemplate.objects.filter(
        round=round_obj, type=template_type
    ).first()
    if not template or not isinstance(template.criteria, list):
        return []
    return template.criteria


# =====================================================
# 팀 평가
# URL: eval_team_list, eval_team_form
# =====================================================

@login_required
def team_evaluation_list(request):
    """get_evaluable_teams(user, round) 계약 — 내 팀 제외 + 이미 평가한 팀 제외"""
    round_obj = _current_round()
    my_team = _get_my_team(request.user, round_obj)

    teams = Team.objects.none()
    if round_obj:
        already_evaluated_ids = TeamEvaluation.objects.filter(
            round=round_obj, submitted_by=request.user
        ).values_list("target_team_id", flat=True)

        teams = Team.objects.filter(round=round_obj)
        if my_team:
            teams = teams.exclude(id=my_team.id)
        teams = teams.exclude(id__in=already_evaluated_ids).order_by("name")

    return render(
        request,
        "eval/team_evaluation_list.html",
        {"round": round_obj, "my_team": my_team, "teams": teams},
    )


@login_required
def team_evaluation_form(request, team_id):
    """get_template_items + save_team_evaluation(user, round, target_team, answers) 계약"""
    round_obj = _current_round()
    target_team = get_object_or_404(Team, id=team_id)
    my_team = _get_my_team(request.user, round_obj)

    # 서버 측 검증 (화면에서 목록을 숨기는 것과 별개로, URL 직접 입력 방어)
    if my_team and my_team.id == target_team.id:
        messages.error(request, "본인 팀은 평가할 수 없습니다.")
        return redirect("eval_team_list")

    if round_obj and TeamEvaluation.objects.filter(
        round=round_obj, submitted_by=request.user, target_team=target_team
    ).exists():
        messages.error(request, "이미 평가한 팀입니다.")
        return redirect("eval_team_list")

    items = _get_template_items(round_obj, EvaluationTemplate.TemplateType.TEAM)

    if request.method == "POST":
        answers = {}
        for item in items:
            key = item.get("key")
            value = request.POST.get(f"item_{key}")
            if value:
                answers[key] = int(value)

        if not items or len(answers) != len(items):
            messages.error(request, "모든 문항에 응답해야 합니다.")
        else:
            scores = list(answers.values())
            avg_score = sum(scores) / len(scores)

            with transaction.atomic():
                # save_team_evaluation(user, round, target_team, answers)
                # ← BE2 함수 나오면 아래 create() 블록을 그 함수 호출로 교체
                TeamEvaluation.objects.create(
                    round=round_obj,
                    evaluator_team=my_team,
                    target_team=target_team,
                    submitted_by=request.user,
                    score=avg_score,
                    responses=answers,
                    is_final=True,
                )
            messages.success(request, f"{target_team.name} 평가가 제출되었습니다.")
            return redirect("eval_team_list")

    return render(
        request,
        "eval/team_evaluation_form.html",
        {"round": round_obj, "target_team": target_team, "items": items},
    )


# =====================================================
# 개인 상호평가
# URL: eval_peer_form
# =====================================================

@login_required
def peer_evaluation_form(request):
    """get_evaluable_members + save_peer_evaluations(user, round, answers) 계약"""
    round_obj = _current_round()
    my_team = _get_my_team(request.user, round_obj)

    members = TeamMember.objects.none()
    already_done = False
    if my_team and round_obj:
        members = (
            TeamMember.objects.filter(team=my_team)
            .exclude(student=request.user)
            .select_related("student")
        )
        already_done = IndividualEvaluation.objects.filter(
            round=round_obj, evaluator=request.user
        ).exists()

    items = _get_template_items(round_obj, EvaluationTemplate.TemplateType.INDIVIDUAL)

    if request.method == "POST":
        if already_done:
            messages.error(request, "이미 제출한 개인 상호평가입니다.")
            return redirect("eval_peer_form")

        with transaction.atomic():
            for member in members:
                answers = {}
                for item in items:
                    key = item.get("key")
                    value = request.POST.get(f"item_{member.student.id}_{key}")
                    if value:
                        answers[key] = int(value)

                if not items or len(answers) != len(items):
                    messages.error(
                        request,
                        f"{member.student.username}님에 대한 모든 문항에 응답해야 합니다.",
                    )
                    return render(
                        request,
                        "eval/peer_evaluation_form.html",
                        {
                            "round": round_obj,
                            "members": members,
                            "items": items,
                            "already_done": already_done,
                        },
                    )

                scores = list(answers.values())
                avg_score = sum(scores) / len(scores)

                # save_peer_evaluations(user, round, answers)
                # ← BE2 함수 나오면 아래 update_or_create() 블록을 그 함수 호출로 교체
                IndividualEvaluation.objects.update_or_create(
                    round=round_obj,
                    team=my_team,
                    evaluator=request.user,
                    target=member.student,
                    defaults={
                        "score": avg_score,
                        "responses": answers,
                        "is_final": True,
                    },
                )

        messages.success(request, "개인 상호평가가 제출되었습니다.")
        return redirect("student_home")

    return render(
        request,
        "eval/peer_evaluation_form.html",
        {
            "round": round_obj,
            "members": members,
            "items": items,
            "already_done": already_done,
        },
    )
