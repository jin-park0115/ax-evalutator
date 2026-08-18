from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from apps.evaluations.models import EvaluationRound, EvaluationTemplate


# =========================================================
# 회차 관리 (실 DB 연동 완료)
# URL: /tutor/rounds/
# =========================================================
@staff_member_required
def round_list(request):
    # 회차 생성
    if request.method == "POST":
        title = request.POST.get("title") or request.POST.get("name")
        start_date = request.POST.get("start_date") or request.POST.get("start_at")
        end_date = request.POST.get("end_date") or request.POST.get("end_at")
        student_weight = request.POST.get("student_weight", 0.5)
        tutor_weight = request.POST.get("tutor_weight", 0.5)

        if title and start_date and end_date:
            EvaluationRound.objects.create(
                name=title,
                start_at=start_date,
                end_at=end_date,
                student_weight=float(student_weight),
                tutor_weight=float(tutor_weight),
            )
            return redirect("tutor_rounds")

    # DB에서 전체 회차 조회
    rounds = EvaluationRound.objects.all().order_by("-id")

    return render(
        request,
        "tutor/round_list.html",
        {
            "rounds": rounds,
        },
    )


# =========================================================
# 회차 상태 변경 및 공개 설정 (추가)
# =========================================================
@staff_member_required
def update_round_status(request, round_id):
    """회차 상태 변경 (draft -> in_progress -> finished 등)"""
    if request.method == "POST":
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        new_status = request.POST.get("status")

        if new_status in EvaluationRound.Status.values:
            round_obj.status = new_status
            round_obj.save()

    return redirect("tutor_rounds")


@staff_member_required
def toggle_team_first_rank(request, round_id):
    """팀 1위 공개 여부 변경 (컨펌)"""
    if request.method == "POST":
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        round_obj.team_first_rank_visible = not round_obj.team_first_rank_visible
        round_obj.save()

    return redirect("tutor_rounds")


# =========================================================
# 팀 편성 (실 DB 연동 — apps/teams의 실제 API와 연결)
# URL: /tutor/team-build/
# =========================================================
@staff_member_required
def team_build(request):
    from apps.teams.models import Team, TeamMember
    from apps.teams.views import is_round_editable

    round_id = request.GET.get("round_id")
    if round_id:
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
    else:
        round_obj = EvaluationRound.objects.order_by("-id").first()

    teams = []
    if round_obj:
        teams = (
            Team.objects.filter(round=round_obj)
            .prefetch_related("members__student")
            .order_by("id")
        )

    assigned_ids = set()
    if round_obj:
        assigned_ids = set(
            TeamMember.objects.filter(team__round=round_obj).values_list(
                "student_id", flat=True
            )
        )

    from django.contrib.auth import get_user_model
    User = get_user_model()
    unassigned_students = User.objects.filter(role=User.Role.STUDENT).exclude(
        id__in=assigned_ids
    )

    return render(
        request,
        "tutor/team_build.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "teams": teams,
            "unassigned_students": unassigned_students,
            "round_editable": is_round_editable(round_obj) if round_obj else False,
        },
    )


# =========================================================
# 팀 발표(평가) 시작 — Team.eval_opened_at 세팅
# 확정된 규칙: 한 번 열리면 다른 팀이 열려도 안 닫힘(누적).
# URL: /tutor/teams/<id>/open/
# =========================================================
@staff_member_required
def open_team_presentation(request, team_id):
    from django.utils import timezone
    from apps.teams.models import Team

    if request.method == "POST":
        team = get_object_or_404(Team, id=team_id)
        if not team.eval_opened_at:
            team.eval_opened_at = timezone.now()
            team.eval_status = Team.EvalStatus.OPEN
            team.save()

    return redirect(f"/tutor/team-build/?round_id={request.POST.get('round_id', '')}")


# =========================================================
# 튜터 평가 공통 헬퍼
#
# TutorEvaluation은 팀 평가와 개인 평가를 한 테이블에 담는다.
# scoring.services는 팀 점수를 team_id로만, 개인 점수를 user_id로만
# 필터링하므로 한 행에 team/user를 동시에 채우면 양쪽에서 중복
# 집계된다. 따라서 저장 시 반드시 둘 중 하나만 채운다.
# =========================================================
def _selected_round(request):
    round_id = request.GET.get("round_id") or request.POST.get("round_id")
    if round_id:
        return get_object_or_404(EvaluationRound, id=round_id)
    return EvaluationRound.objects.order_by("-id").first()


def _tutor_template_items(round_obj):
    """튜터 평가 문항 목록. criteria가 list가 아니면 빈 목록으로 취급."""
    if not round_obj:
        return []
    template = EvaluationTemplate.objects.filter(
        round=round_obj,
        type=EvaluationTemplate.TemplateType.TUTOR,
    ).first()
    if not template or not isinstance(template.criteria, list):
        return []
    return template.criteria


def _collect_answers(request, items):
    """POST에서 문항 응답을 모아 (answers, avg_score)를 반환.
    미응답 문항이 하나라도 있으면 (None, None)."""
    answers = {}
    for item in items:
        key = item.get("key")
        value = request.POST.get(f"item_{key}")
        if value:
            answers[key] = int(value)

    if not items or len(answers) != len(items):
        return None, None

    scores = list(answers.values())
    return answers, sum(scores) / len(scores)


# =========================================================
# 튜터 팀 평가 (실 DB 연동 — TutorEvaluation)
# URL: /tutor/team-evaluation/
# =========================================================
@staff_member_required
def team_evaluation(request):
    from apps.teams.models import Team
    from apps.evaluations.models import TutorEvaluation

    round_obj = _selected_round(request)

    evaluations = []
    if round_obj:
        teams = Team.objects.filter(round=round_obj).order_by("id")
        my_scores = {
            te.team_id: te
            for te in TutorEvaluation.objects.filter(
                round=round_obj,
                evaluator=request.user,
                team__isnull=False,
            )
        }
        for team in teams:
            existing = my_scores.get(team.id)
            evaluations.append(
                {
                    "team": team,
                    "score": existing.score if existing else None,
                    "done": existing is not None,
                }
            )

    return render(
        request,
        "tutor/team_evaluation.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "evaluations": evaluations,
        },
    )


# =========================================================
# 튜터 팀 평가 입력 폼
# URL: /tutor/team-evaluation/<team_id>/
# =========================================================
@staff_member_required
def team_evaluation_form(request, team_id):
    from apps.teams.models import Team
    from apps.evaluations.models import TutorEvaluation

    target_team = get_object_or_404(Team, id=team_id)
    round_obj = target_team.round

    items = _tutor_template_items(round_obj)

    existing = TutorEvaluation.objects.filter(
        round=round_obj,
        evaluator=request.user,
        team=target_team,
    ).first()
    existing_answers = existing.responses if existing else {}
    # 템플릿에서는 변수 키로 dict 조회를 못 하므로 미리 값을 붙여서 넘긴다
    items = [
        {**item, "existing_value": existing_answers.get(item.get("key"))}
        for item in items
    ]

    if request.method == "POST":
        answers, avg_score = _collect_answers(request, items)
        if answers is None:
            messages.error(request, "모든 문항에 응답해야 합니다.")
        else:
            TutorEvaluation.objects.update_or_create(
                round=round_obj,
                evaluator=request.user,
                team=target_team,
                user=None,
                defaults={
                    "score": avg_score,
                    "responses": answers,
                },
            )
            messages.success(request, f"{target_team.name} 튜터 평가가 저장되었습니다.")
            return redirect(f"/tutor/team-evaluation/?round_id={round_obj.id}")

    return render(
        request,
        "tutor/team_evaluation_form.html",
        {
            "round": round_obj,
            "target_team": target_team,
            "items": items,
        },
    )


# =========================================================
# 튜터 개인 평가 (실 DB 연동 — TutorEvaluation)
# URL: /tutor/individual-evaluation/
# =========================================================
@staff_member_required
def individual_evaluation(request):
    from apps.teams.models import TeamMember
    from apps.evaluations.models import TutorEvaluation

    round_obj = _selected_round(request)

    evaluations = []
    if round_obj:
        members = (
            TeamMember.objects.filter(team__round=round_obj)
            .select_related("student", "team")
            .order_by("team__id", "student__username")
        )
        my_scores = {
            te.user_id: te
            for te in TutorEvaluation.objects.filter(
                round=round_obj,
                evaluator=request.user,
                user__isnull=False,
            )
        }
        for member in members:
            existing = my_scores.get(member.student_id)
            evaluations.append(
                {
                    "student": member.student,
                    "team": member.team,
                    "score": existing.score if existing else None,
                    "done": existing is not None,
                }
            )

    return render(
        request,
        "tutor/individual_evaluation.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "evaluations": evaluations,
        },
    )


# =========================================================
# 튜터 개인 평가 입력 폼
# URL: /tutor/individual-evaluation/<student_id>/
# =========================================================
@staff_member_required
def individual_evaluation_form(request, student_id):
    from apps.teams.models import TeamMember
    from apps.evaluations.models import TutorEvaluation

    round_obj = _selected_round(request)
    if not round_obj:
        messages.error(request, "평가 회차가 없습니다.")
        return redirect("tutor_individual_evaluation")

    membership = get_object_or_404(
        TeamMember.objects.select_related("student", "team"),
        student_id=student_id,
        team__round=round_obj,
    )
    target_student = membership.student

    items = _tutor_template_items(round_obj)

    existing = TutorEvaluation.objects.filter(
        round=round_obj,
        evaluator=request.user,
        user=target_student,
    ).first()
    existing_answers = existing.responses if existing else {}
    items = [
        {**item, "existing_value": existing_answers.get(item.get("key"))}
        for item in items
    ]

    if request.method == "POST":
        answers, avg_score = _collect_answers(request, items)
        if answers is None:
            messages.error(request, "모든 문항에 응답해야 합니다.")
        else:
            TutorEvaluation.objects.update_or_create(
                round=round_obj,
                evaluator=request.user,
                user=target_student,
                team=None,
                defaults={
                    "score": avg_score,
                    "responses": answers,
                },
            )
            messages.success(
                request, f"{target_student.username} 튜터 평가가 저장되었습니다."
            )
            return redirect(
                f"/tutor/individual-evaluation/?round_id={round_obj.id}"
            )

    return render(
        request,
        "tutor/individual_evaluation_form.html",
        {
            "round": round_obj,
            "target_student": target_student,
            "target_team": membership.team,
            "items": items,
        },
    )


# =========================================================
# 템플릿 관리 (실 DB 연동 — EvaluationTemplate.criteria)
# URL: /tutor/templates/
# =========================================================
@staff_member_required
def template_list(request):
    templates = EvaluationTemplate.objects.select_related("round").order_by("-id")
    return render(
        request,
        "tutor/templates.html",
        {
            "templates": templates,
        },
    )


@staff_member_required
def template_create(request):
    if request.method == "POST":
        round_id = request.POST.get("round_id")
        template_type = request.POST.get("type")
        keys = request.POST.getlist("item_key")
        texts = request.POST.getlist("item_text")

        criteria = [
            {"key": key, "text": text}
            for key, text in zip(keys, texts)
            if key and text
        ]

        if round_id and template_type and criteria:
            EvaluationTemplate.objects.update_or_create(
                round_id=round_id,
                type=template_type,
                defaults={"criteria": criteria},
            )
            return redirect("tutor_templates")

    rounds = EvaluationRound.objects.order_by("-id")
    return render(
        request,
        "tutor/template_form.html",
        {
            "rounds": rounds,
            "types": EvaluationTemplate.TemplateType.choices,
        },
    )


# =========================================================
# 공개 설정 (실 DB 연동 — EvaluationRound의 4개 visible 필드)
# URL: /tutor/settings/
# =========================================================
@staff_member_required
def tutor_settings(request):
    round_id = request.GET.get("round_id") or request.POST.get("round_id")
    if round_id:
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
    else:
        round_obj = EvaluationRound.objects.order_by("-id").first()

    if request.method == "POST" and round_obj:
        round_obj.team_first_rank_visible = "team_first_rank_visible" in request.POST
        round_obj.team_rank_visible = "team_rank_visible" in request.POST
        round_obj.individual_score_visible = "individual_score_visible" in request.POST
        round_obj.individual_rank_visible = "individual_rank_visible" in request.POST
        round_obj.save()
        return redirect(f"/tutor/settings/?round_id={round_obj.id}")

    return render(
        request,
        "tutor/settings.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
        },
    )


# =========================================================
# 평가 현황 (실 DB 연동 — 제출률/미제출자)
# URL: /tutor/evaluation-status/
# =========================================================
@staff_member_required
def evaluation_status(request):
    from apps.teams.models import Team, TeamMember
    from apps.evaluations.models import IndividualEvaluation, TeamEvaluation

    round_id = request.GET.get("round_id")
    if round_id:
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
    else:
        round_obj = EvaluationRound.objects.order_by("-id").first()

    status = None
    non_submitters = []

    if round_obj:
        members = (
            TeamMember.objects.filter(team__round=round_obj)
            .select_related("student", "team")
            .order_by("student__username")
        )
        total_students = members.count()

        # 개인 상호평가는 팀원 전원을 한 번에 제출하는 구조라
        # is_final=True 레코드가 하나라도 있으면 그 학생은 제출 완료로 본다
        submitted_ids = set(
            IndividualEvaluation.objects.filter(
                round=round_obj, is_final=True
            ).values_list("evaluator_id", flat=True)
        )
        completed_students = len({m.student_id for m in members if m.student_id in submitted_ids})
        remaining_students = total_students - completed_students
        completion_rate = (
            round(completed_students / total_students * 100) if total_students else 0
        )

        non_submitters = [m.student for m in members if m.student_id not in submitted_ids]

        teams = Team.objects.filter(round=round_obj)
        total_teams = teams.count()
        completed_teams = 0
        for team in teams:
            evaluators_count = (
                TeamEvaluation.objects.filter(round=round_obj, target_team=team)
                .values("evaluator_team")
                .distinct()
                .count()
            )
            if total_teams > 1 and evaluators_count >= total_teams - 1:
                completed_teams += 1
        remaining_teams = total_teams - completed_teams

        status = {
            "total_students": total_students,
            "completed_students": completed_students,
            "remaining_students": remaining_students,
            "completion_rate": completion_rate,
            "total_teams": total_teams,
            "completed_teams": completed_teams,
            "remaining_teams": remaining_teams,
        }

    return render(
        request,
        "tutor/evaluation_status.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "status": status,
            "non_submitters": non_submitters,
        },
    )