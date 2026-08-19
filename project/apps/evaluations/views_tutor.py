from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from apps.evaluations.models import (
    EvaluationRound,
    EvaluationTemplate,
    DEFAULT_TEAM_CRITERIA,
    DEFAULT_INDIVIDUAL_CRITERIA,
)


# =========================================================
# 회차 관리 (실 DB 연동 완료)
# URL: /tutor/rounds/
#
# 팀 수는 여기서 입력받지 않는다 — 실제 팀 수는 팀 편성 화면에서
# 만들어진 Team 레코드 개수(round.teams.count)를 그대로 보여준다.
# (팀 편성에서 자동/수동으로 몇 개 팀을 만들든 그게 곧 회차의
# 팀 수가 되므로, 이중으로 값을 관리할 이유가 없다)
# =========================================================
@staff_member_required
def round_list(request):
    if request.method == "POST":
        round_id = request.POST.get("round_id")
        title = request.POST.get("title") or request.POST.get("name")
        start_date = request.POST.get("start_date") or request.POST.get("start_at")
        end_date = request.POST.get("end_date") or request.POST.get("end_at")

        if title and start_date and end_date:
            if round_id:
                # 회차 수정
                round_obj = get_object_or_404(EvaluationRound, id=round_id)
                round_obj.name = title
                round_obj.start_at = start_date
                round_obj.end_at = end_date
                round_obj.save(update_fields=["name", "start_at", "end_at"])
                messages.success(request, f"{title} 회차가 수정되었습니다.")
            else:
                # 회차 생성
                student_weight = request.POST.get("student_weight", 0.5)
                tutor_weight = request.POST.get("tutor_weight", 0.5)
                EvaluationRound.objects.create(
                    name=title,
                    start_at=start_date,
                    end_at=end_date,
                    student_weight=float(student_weight),
                    tutor_weight=float(tutor_weight),
                )
                messages.success(request, f"{title} 회차가 생성되었습니다.")
            return redirect("tutor_rounds")

    # DB에서 전체 회차 조회
    rounds = EvaluationRound.objects.all().order_by("-id")

    # "회차 종료" 전에 아직 평가를 제출 안 한 학생이 몇 명인지 미리
    # 계산해서, 튜터가 그 수를 보고 종료할지 판단할 수 있게 한다
    # (evaluation_status 화면의 미제출자 판정 기준과 동일).
    from apps.teams.models import TeamMember
    from apps.evaluations.models import IndividualEvaluation, TeamEvaluation

    for round_obj in rounds:
        member_student_ids = set(
            TeamMember.objects.filter(team__round=round_obj).values_list(
                "student_id", flat=True
            )
        )
        submitted_ids = set(
            IndividualEvaluation.objects.filter(
                round=round_obj, is_final=True
            ).values_list("evaluator_id", flat=True)
        ) | set(
            TeamEvaluation.objects.filter(
                round=round_obj, is_final=True
            ).values_list("submitted_by_id", flat=True)
        )
        # DB에 저장되는 필드가 아니라, 템플릿에서 쓸 수 있게 잠깐 붙여두는
        # 값이다 (round.save()를 안 하므로 DB에는 영향 없음).
        round_obj.remaining_count = len(member_student_ids - submitted_ids)

    return render(
        request,
        "tutor/round_list.html",
        {
            "rounds": rounds,
        },
    )


@staff_member_required
def delete_round(request, round_id):
    """회차 삭제. 팀/평가/집계 결과 등 연결된 데이터가 전부 함께
    삭제된다(FK CASCADE) — 삭제 전 화면에서 반드시 경고 후 확인받는다."""
    if request.method == "POST":
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        name = round_obj.name
        round_obj.delete()
        messages.success(request, f"{name} 회차가 삭제되었습니다.")

    return redirect("tutor_rounds")


# =========================================================
# 회차 정보 수정 (새로 추가된 기능)
# URL: /tutor/rounds/<round_id>/edit/
# =========================================================
@staff_member_required
def update_round(request, round_id):
    """기존 회차 이름, 기간, 가중치 정보 수정"""
    if request.method == "POST":
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        
        title = request.POST.get("title") or request.POST.get("name")
        start_date = request.POST.get("start_date") or request.POST.get("start_at")
        end_date = request.POST.get("end_date") or request.POST.get("end_at")
        student_weight = request.POST.get("student_weight")
        tutor_weight = request.POST.get("tutor_weight")

        if title:
            round_obj.name = title
        if start_date:
            round_obj.start_at = start_date
        if end_date:
            round_obj.end_at = end_date
        if student_weight is not None:
            round_obj.student_weight = float(student_weight)
        if tutor_weight is not None:
            round_obj.tutor_weight = float(tutor_weight)

        round_obj.save()
        messages.success(request, f"[{round_obj.name}] 회차 정보가 성공적으로 수정되었습니다.")

    return redirect("tutor_rounds")


# =========================================================
# 회차 상태 변경 및 공개 설정
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
# 팀 편성 확정 기능 (추가됨)
# =========================================================
@staff_member_required
def team_confirm(request, round_id):
    """팀 편성 확정 버튼 클릭 시 회차 상태를 CONFIRMED로 변경"""
    if request.method == "POST":
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        round_obj.status = EvaluationRound.Status.CONFIRMED
        round_obj.save()
        messages.success(request, f"[{round_obj.name}] 팀 편성이 확정되었습니다.")

    return redirect(f"/tutor/team-build/?round_id={round_id}")


# =========================================================
# 점수 집계 (BE2 calculate_round 호출)
# URL: /tutor/rounds/<round_id>/calculate/
# =========================================================
@staff_member_required
def calculate_round_scores(request, round_id):
    from apps.teams.models import TeamMember
    from apps.scoring.services import calculate_round

    round_obj = get_object_or_404(EvaluationRound, id=round_id)

    if request.method != "POST":
        return redirect("tutor_rounds")

    total_students = TeamMember.objects.filter(team__round=round_obj).count()

    if total_students == 0:
        messages.error(
            request,
            f"[{round_obj.name}] 팀에 배정된 학생이 없어 집계할 수 없습니다. "
            "먼저 팀 편성을 완료해주세요.",
        )
        return redirect("tutor_rounds")

    saved = calculate_round(round_obj)
    saved_count = len(saved)
    skipped = total_students - saved_count

    if saved_count == 0:
        messages.error(
            request,
            f"[{round_obj.name}] 집계된 학생이 없습니다. "
            "학생 평가와 튜터 평가가 모두 등록되어야 점수가 계산됩니다.",
        )
    elif skipped > 0:
        messages.warning(
            request,
            f"[{round_obj.name}] {saved_count}명 집계 완료. "
            f"{skipped}명은 평가 데이터가 부족해 제외되었습니다.",
        )
    else:
        messages.success(
            request,
            f"[{round_obj.name}] 전체 {saved_count}명의 점수 집계가 완료되었습니다.",
        )

    return redirect("tutor_rounds")


# =========================================================
# 팀 편성 (실 DB 연동 — apps/teams의 실제 API와 연결)
# URL: /tutor/team-build/
# =========================================================
@staff_member_required
def team_build(request):
    from apps.teams.models import Team, TeamMember
    from apps.teams.views import is_round_editable
    from apps.teams.services import get_user_display_name

    round_id = request.GET.get("round_id")
    if round_id:
        round_obj = get_object_or_404(EvaluationRound, id=round_id)
    else:
        round_obj = EvaluationRound.objects.order_by("-id").first()

    # 종료된 이전 회차에 점수 결과가 있는지 — 시드 구간 설정 슬라이더 노출 여부
    from apps.evaluations.models import ScoreResult
    has_score_history = False
    if round_obj:
        has_score_history = ScoreResult.objects.filter(
            round__status="finished", round_id__lt=round_obj.id
        ).exists()

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
    unassigned_students = User.objects.filter(
        role=User.Role.STUDENT, is_active=True
    ).exclude(id__in=assigned_ids)

    # 편성 화면은 전부 브라우저(JS) 상태로 그리고, "편성 확정"을 눌러야만
    # DB에 저장된다. 초기 화면을 채울 현재 DB 상태를 JSON으로 한 번에
    # 넘겨준다 (json_script로 안전하게 이스케이프).
    initial_state = {
        "teams": {
            team.name: {
                "eval_opened": bool(team.eval_opened_at),
                "members": [
                    {"id": m.student.id, "username": get_user_display_name(m.student)}
                    for m in team.members.all()
                ],
            }
            for team in teams
        },
        "unassigned": [
            {"id": s.id, "username": get_user_display_name(s)}
            for s in unassigned_students
        ],
    }

    return render(
        request,
        "tutor/team_build.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "teams": teams,
            "unassigned_students": unassigned_students,
            "round_editable": is_round_editable(round_obj) if round_obj else False,
            "has_score_history": has_score_history,
            "initial_state": initial_state,
        },
    )


# =========================================================
# 팀 편성 잠금 해제 ("수정" 버튼) — ready -> draft로 되돌려
# is_round_editable이 다시 True가 되게 한다.
# 편성 확정(ready) 상태에서만 허용 — 발표가 이미 시작됐거나
# 회차가 진행 중/종료된 뒤에 팀 구성을 바꾸면 이미 제출된 평가와
# 어긋나므로 그 경우는 막는다.
# URL: /tutor/rounds/<round_id>/unlock-formation/
# =========================================================
@staff_member_required
def unlock_round_formation(request, round_id):
    if request.method == "POST":
        from apps.teams.models import Team

        round_obj = get_object_or_404(EvaluationRound, id=round_id)
        has_eval_started = Team.objects.filter(
            round=round_obj, eval_opened_at__isnull=False
        ).exists()

        if has_eval_started:
            messages.error(request, "이미 발표(평가)가 시작되어 되돌릴 수 없습니다.")
        elif round_obj.status in (
            EvaluationRound.Status.READY,
            EvaluationRound.Status.IN_PROGRESS,
        ):
            round_obj.status = EvaluationRound.Status.DRAFT
            round_obj.save(update_fields=["status"])
            messages.success(request, "팀 편성을 다시 수정할 수 있습니다.")
        else:
            messages.error(
                request,
                f"현재 상태({round_obj.get_status_display()})에서는 수정할 수 없습니다.",
            )
        return redirect(f"/tutor/team-build/?round_id={round_obj.id}")

    return redirect("tutor_team_build")


# =========================================================
# 팀 발표(평가) 시작 — Team.eval_opened_at 세팅
# URL: /tutor/teams/<id>/open/
#
# [수정] 팀 편성이 아직 확정(draft) 전이거나 팀원이 없는 팀은
# 발표를 시작할 수 없도록 서버단에서 막는다. 원래는 아무 검증 없이
# 편성 확정 전에도 발표 시작이 눌리는 문제가 있었다.
# =========================================================
@staff_member_required
def open_team_presentation(request, team_id):
    from django.utils import timezone
    from apps.teams.models import Team

    if request.method == "POST":
        team = get_object_or_404(Team, id=team_id)
        round_obj = team.round

        if round_obj.status == EvaluationRound.Status.DRAFT:
            messages.error(
                request,
                "팀 편성이 아직 확정되지 않았습니다. 먼저 '팀 편성'에서 편성을 확정해주세요.",
            )
        elif team.members.count() == 0:
            messages.error(
                request,
                f"{team.name}에 배정된 팀원이 없어 발표를 시작할 수 없습니다.",
            )
        elif not team.eval_opened_at:
            team.eval_opened_at = timezone.now()
            team.eval_status = Team.EvalStatus.OPEN
            team.save()
            messages.success(request, f"{team.name} 발표가 시작되어 평가가 열렸습니다.")

        return redirect(f"/tutor/team-evaluation/?round_id={round_obj.id}")

    return redirect("tutor_team_evaluation")


# =========================================================
# 튜터 평가 공통 헬퍼
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
                    "member_count": team.members.count(),
                }
            )

    return render(
        request,
        "tutor/team_evaluation.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "evaluations": evaluations,
            # 팀 편성이 확정(draft 이후)돼야 발표 시작 버튼을 노출한다
            "formation_confirmed": bool(
                round_obj and round_obj.status != EvaluationRound.Status.DRAFT
            ),
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
            messages.success(request, f"{target_team.name} 팀에 대한 튜터 평가가 저장되었습니다.")
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
                request, f"{target_student.username} 학생에 대한 튜터 평가가 저장되었습니다."
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

    default_items = {
        "TEAM": DEFAULT_TEAM_CRITERIA,
        "INDIVIDUAL": DEFAULT_INDIVIDUAL_CRITERIA,
        # 튜터 평가 기본값도 팀 평가와 같은 5문항 사용 (EvaluationTemplate.save()의
        # TUTOR 기본값 처리와 동일한 기준)
        "TUTOR": DEFAULT_TEAM_CRITERIA,
    }

    rounds = EvaluationRound.objects.order_by("-id")
    return render(
        request,
        "tutor/template_form.html",
        {
            "rounds": rounds,
            "types": EvaluationTemplate.TemplateType.choices,
            "default_items": default_items,
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

        # 최종 제출(BR-11)은 그 시점의 팀 평가/개인 평가를 함께 잠그지만,
        # 학생에 따라 둘 중 하나만 존재할 수 있다(팀 평가만 했거나 개인 평가만
        # 했거나). 팀 평가 또는 개인 평가 중 하나라도 is_final=True면
        # 그 학생은 제출 완료로 본다.
        submitted_ids = set(
            IndividualEvaluation.objects.filter(
                round=round_obj, is_final=True
            ).values_list("evaluator_id", flat=True)
        ) | set(
            TeamEvaluation.objects.filter(
                round=round_obj, is_final=True
            ).values_list("submitted_by_id", flat=True)
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


# =========================================================
# 전체 학생 성적 조회
# URL: /tutor/students/scores/
#
# 회차별로 흩어져 있는 ScoreResult를 학생 단위로 모아
# 참여 회차 수 / 평균 최종점수 / 최근 회차 점수·석차를 보여준다.
# 아직 채점 결과가 없는 학생도 0점으로 목록에 포함한다.
# =========================================================
@staff_member_required
def student_score_overview(request):
    from django.contrib.auth import get_user_model
    from apps.evaluations.models import ScoreResult

    User = get_user_model()

    results = (
        ScoreResult.objects.filter(user__role=User.Role.STUDENT)
        .select_related("round", "user")
        .order_by("user_id", "-round_id")
    )

    by_student = {}
    for result in results:
        entry = by_student.setdefault(
            result.user_id, {"student": result.user, "results": []}
        )
        entry["results"].append(result)

    overview = []
    for entry in by_student.values():
        scores = [r.final_score for r in entry["results"] if r.final_score is not None]
        overview.append(
            {
                "student": entry["student"],
                "round_count": len(entry["results"]),
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "latest": entry["results"][0],
            }
        )

    scored_ids = set(by_student.keys())
    unscored_students = User.objects.filter(
        role=User.Role.STUDENT, is_active=True
    ).exclude(id__in=scored_ids)
    for student in unscored_students:
        overview.append(
            {"student": student, "round_count": 0, "avg_score": 0.0, "latest": None}
        )

    overview.sort(key=lambda row: (-row["avg_score"], row["student"].username))

    return render(request, "tutor/student_scores.html", {"overview": overview})