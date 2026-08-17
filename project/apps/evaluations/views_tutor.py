from django.shortcuts import render, redirect, get_object_or_404
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
        },
    )


# =========================================================
# 팀 평가 (다른 팀원 목업 유지)
# URL: /tutor/team-evaluation/
# =========================================================
def team_evaluation(request):
    evaluations = [
        {
            "team_no": 1,
            "team_name": "1팀",
            "project": "Django 프로젝트",
            "score": 85,
            "status": "평가 완료",
        },
        {
            "team_no": 2,
            "team_name": "2팀",
            "project": "Django 프로젝트",
            "score": 82,
            "status": "평가 완료",
        },
        {
            "team_no": 3,
            "team_name": "3팀",
            "project": "Django 프로젝트",
            "score": 78,
            "status": "평가 대기",
        },
    ]

    return render(
        request,
        "tutor/team_evaluation.html",
        {
            "evaluations": evaluations,
        },
    )


# =========================================================
# 개인 평가 (다른 팀원 목업 유지)
# URL: /tutor/individual-evaluation/
# =========================================================
def individual_evaluation(request):
    evaluations = [
        {
            "name": "김철수",
            "team": 1,
            "score": 88,
            "status": "평가 완료",
        },
        {
            "name": "이영희",
            "team": 1,
            "score": 91,
            "status": "평가 완료",
        },
        {
            "name": "박민수",
            "team": 2,
            "score": 84,
            "status": "평가 대기",
        },
        {
            "name": "최지우",
            "team": 2,
            "score": 86,
            "status": "평가 대기",
        },
        {
            "name": "정수빈",
            "team": 3,
            "score": 79,
            "status": "평가 완료",
        },
        {
            "name": "한지민",
            "team": 3,
            "score": 83,
            "status": "평가 완료",
        },
    ]

    return render(
        request,
        "tutor/individual_evaluation.html",
        {
            "evaluations": evaluations,
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