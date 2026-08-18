# apps/evaluations/views_eval.py
#
# 서비스 함수(services.py의 save_team_evaluation,
# save_individual_evaluation)가 완성되어, 저장 로직을 그 함수 호출로
# 교체했다. 화면단(목록 조회, 폼 렌더링, 문항 누락 검증)은 기존 그대로다.
#
# 확정된 규칙 (2026-08-17, 채희주/전예진/안형준 합의):
# - 팀 발표 순서대로 평가가 "누적" 오픈된다. 1조 발표 시 1조만 열리고,
#   2조 발표 시 1조는 열린 채로 2조도 함께 열린다 (닫히지 않음).
#   → 화면 목록 단(eval_opened_at__isnull=False)과 서버 저장 단
#     (save_team_evaluation 내부) 양쪽에서 이중으로 막는다.
# - 열려 있는 동안은 임시저장/수정이 자유롭다 (TeamEvaluation/
#   IndividualEvaluation.is_final=False).
# - 학생이 "최종 제출"을 누르는 순간 그 학생의 해당 회차 답변 전체가
#   한 번에 is_final=True로 잠긴다. 그 전까지는 팀별 개별 제출/잠금이 없다.

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


def _has_finalized(user, round_obj):
    """이 학생이 이번 회차 최종 제출을 이미 눌렀는지"""
    if not round_obj:
        return False
    return (
        TeamEvaluation.objects.filter(
            round=round_obj, submitted_by=user, is_final=True
        ).exists()
        or IndividualEvaluation.objects.filter(
            round=round_obj, evaluator=user, is_final=True
        ).exists()
    )


# =====================================================
# 팀 평가
# URL: eval_team_list, eval_team_form
# =====================================================

@login_required
def team_evaluation_list(request):
    """get_evaluable_teams(user, round) 계약
    — 내 팀 제외 + eval_opened_at이 설정된(발표 시작된) 팀만, 누적 오픈이라
      한번 열리면 계속 목록에 남는다 (이미 임시저장했어도 사라지지 않음)."""
    round_obj = _current_round()
    my_team = _get_my_team(request.user, round_obj)
    finalized = _has_finalized(request.user, round_obj)

    teams = Team.objects.none()
    saved_team_ids = set()
    if round_obj:
        teams = Team.objects.filter(
            round=round_obj, eval_opened_at__isnull=False
        )
        if my_team:
            teams = teams.exclude(id=my_team.id)
        teams = teams.order_by("eval_opened_at")

        saved_team_ids = set(
            TeamEvaluation.objects.filter(
                round=round_obj, submitted_by=request.user
            ).values_list("target_team_id", flat=True)
        )

    return render(
        request,
        "eval/team_evaluation_list.html",
        {
            "round": round_obj,
            "my_team": my_team,
            "teams": teams,
            "saved_team_ids": saved_team_ids,
            "finalized": finalized,
        },
    )


@login_required
def team_evaluation_form(request, team_id):
    """get_template_items + save_team_evaluation(user, round, target_team, answers) 계약
    — 최종 제출 전까지는 임시저장(is_final=False)이라 여러 번 다시 열어 수정 가능.
    — 자기 팀 여부/발표 오픈 여부/최종 제출 여부는 화면 단에서 먼저 안내하고,
      실제 저장 시에는 services.save_team_evaluation 안에서 다시 한 번 검증한다
      (URL 직접 호출로 우회하는 경우까지 서버 단에서 막기 위함)."""
    round_obj = _current_round()
    target_team = get_object_or_404(Team, id=team_id)
    my_team = _get_my_team(request.user, round_obj)
    finalized = _has_finalized(request.user, round_obj)

    if my_team and my_team.id == target_team.id:
        messages.error(request, "본인 팀은 평가할 수 없습니다.")
        return redirect("eval_team_list")

    if not target_team.eval_opened_at:
        messages.error(request, "아직 발표가 시작되지 않은 팀입니다.")
        return redirect("eval_team_list")

    if finalized:
        messages.error(request, "이미 최종 제출을 완료해 수정할 수 없습니다.")
        return redirect("eval_team_list")

    items = _get_template_items(round_obj, EvaluationTemplate.TemplateType.TEAM)

    existing = TeamEvaluation.objects.filter(
        round=round_obj, submitted_by=request.user, target_team=target_team
    ).first()
    existing_answers = existing.responses if existing else {}
    # 템플릿은 변수 키로 dict 조회를 못 하므로 미리 값을 붙여서 넘긴다
    items = [
        {**item, "existing_value": existing_answers.get(item.get("key"))}
        for item in items
    ]

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
                messages.error(request, str(exc))
                return redirect("eval_team_list")

            messages.success(request, f"{target_team.name} 평가가 임시저장되었습니다.")
            return redirect("eval_team_list")

    return render(
        request,
        "eval/team_evaluation_form.html",
        {
            "round": round_obj,
            "target_team": target_team,
            "items": items,
            "existing_answers": existing_answers,
        },
    )


# =====================================================
# 개인 상호평가
# URL: eval_peer_form
# =====================================================

def _build_member_rows(members, items, existing_answers):
    """템플릿이 변수 키로 dict 조회를 못 하므로, 팀원별 문항에
    기존 답변을 미리 붙여서 순수 리스트 구조로 만든다."""
    rows = []
    for member in members:
        member_answers = existing_answers.get(member.student_id, {})
        rows.append({
            "member": member,
            "items": [
                {**item, "existing_value": member_answers.get(item.get("key"))}
                for item in items
            ],
        })
    return rows


@login_required
def peer_evaluation_form(request):
    """get_evaluable_members + save_peer_evaluations(user, round, answers) 계약
    — 임시저장 방식, 최종 제출 전까지 몇 번이든 다시 저장 가능."""
    round_obj = _current_round()
    my_team = _get_my_team(request.user, round_obj)
    finalized = _has_finalized(request.user, round_obj)

    members = TeamMember.objects.none()
    if my_team and round_obj:
        members = (
            TeamMember.objects.filter(team=my_team)
            .exclude(student=request.user)
            .select_related("student")
        )

    items = _get_template_items(round_obj, EvaluationTemplate.TemplateType.INDIVIDUAL)

    existing_answers = {}
    if round_obj:
        for ie in IndividualEvaluation.objects.filter(
            round=round_obj, evaluator=request.user
        ):
            existing_answers[ie.target_id] = ie.responses

    if request.method == "POST":
        if finalized:
            messages.error(request, "이미 최종 제출을 완료해 수정할 수 없습니다.")
            return redirect("eval_peer_form")

        if not my_team:
            messages.error(request, "소속된 팀이 없어 개인 평가를 진행할 수 없습니다.")
            return redirect("eval_peer_form")

        # 1단계 — 먼저 팀원 전원의 답변을 걷어서 문항 누락만 검증한다.
        member_answers = {}
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
                        "member_rows": _build_member_rows(members, items, existing_answers),
                        "finalized": finalized,
                    },
                )
            member_answers[member] = answers

        # 2단계 — 문항 누락이 없으면 실제 저장.
        try:
            with transaction.atomic():
                for member, answers in member_answers.items():
                    scores = list(answers.values())
                    avg_score = sum(scores) / len(scores)

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
            messages.error(request, str(exc))
            return render(
                request,
                "eval/peer_evaluation_form.html",
                {
                    "round": round_obj,
                    "member_rows": _build_member_rows(members, items, existing_answers),
                    "finalized": finalized,
                },
            )

        messages.success(request, "개인 상호평가가 임시저장되었습니다.")
        return redirect("eval_peer_form")

    return render(
        request,
        "eval/peer_evaluation_form.html",
        {
            "round": round_obj,
            "member_rows": _build_member_rows(members, items, existing_answers),
            "finalized": finalized,
        },
    )


# =====================================================
# 최종 제출
# URL: eval_submit_final
# =====================================================

@login_required
def submit_final(request):
    """submit_final(user, round) 계약
    — 평가 완결성 검증 후, 학생이 임시저장해둔 TeamEvaluation/IndividualEvaluation 
      전체를 한 번에 is_final=True로 잠근다."""
    round_obj = _current_round()
    if not round_obj:
        messages.error(request, "현재 진행 중인 평가 회차가 없습니다.")
        return redirect("eval_team_list")

    if request.method == "POST":
        # 1. 이미 최종 제출을 완료했는지 가드
        if _has_finalized(request.user, round_obj):
            messages.error(request, "이미 최종 제출을 완료했습니다.")
            return redirect("eval_team_list")

        my_team = _get_my_team(request.user, round_obj)

        # 2. 필수 팀 평가 작성 여부 검증 (오픈된 팀 중 내 팀을 제외한 모든 팀)
        open_teams = Team.objects.filter(
            round=round_obj, eval_opened_at__isnull=False
        )
        if my_team:
            open_teams = open_teams.exclude(id=my_team.id)

        saved_team_ids = set(
            TeamEvaluation.objects.filter(
                round=round_obj, submitted_by=request.user
            ).values_list("target_team_id", flat=True)
        )
        required_team_ids = set(open_teams.values_list("id", flat=True))

        missing_teams = required_team_ids - saved_team_ids
        if missing_teams:
            messages.error(request, "아직 작성하지 않은 팀 평가가 있습니다. 모든 팀 평가를 완료해 주세요.")
            return redirect("eval_team_list")

        # 3. 필수 개인 상호평가 작성 여부 검증 (본인 팀 팀원 전원)
        if my_team:
            team_members = TeamMember.objects.filter(team=my_team).exclude(student=request.user)
            saved_member_ids = set(
                IndividualEvaluation.objects.filter(
                    round=round_obj, evaluator=request.user
                ).values_list("target_id", flat=True)
            )
            required_member_ids = set(team_members.values_list("student_id", flat=True))

            missing_members = required_member_ids - saved_member_ids
            if missing_members:
                messages.error(request, "아직 작성하지 않은 팀원 개인 평가가 있습니다. 모든 팀원 평가를 완료해 주세요.")
                return redirect("eval_peer_form")

        # 4. 검증 통과 시 트랜잭션 내에서 최종 제출(is_final=True) 처리
        with transaction.atomic():
            TeamEvaluation.objects.filter(
                round=round_obj, submitted_by=request.user
            ).update(is_final=True)
            IndividualEvaluation.objects.filter(
                round=round_obj, evaluator=request.user
            ).update(is_final=True)

        messages.success(request, "최종 제출이 완료되었습니다. 더 이상 수정할 수 없습니다.")

    return redirect("eval_team_list")