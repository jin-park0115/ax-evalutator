from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from apps.evaluations.models import (
    EvaluationRound,
    EvaluationTemplate,
)


# =========================================================
# 평가 회차 관리
# URL: /tutor/rounds/
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
                round_obj = get_object_or_404(
                    EvaluationRound,
                    id=round_id,
                )

                round_obj.name = title
                round_obj.start_at = start_date
                round_obj.end_at = end_date

                round_obj.save(
                    update_fields=[
                        "name",
                        "start_at",
                        "end_at",
                    ]
                )

                messages.success(
                    request,
                    f"[{title}] 평가 회차가 수정되었습니다.",
                )

            else:
                student_weight = request.POST.get(
                    "student_weight",
                    0.5,
                )
                tutor_weight = request.POST.get(
                    "tutor_weight",
                    0.5,
                )

                EvaluationRound.objects.create(
                    name=title,
                    start_at=start_date,
                    end_at=end_date,
                    student_weight=float(student_weight),
                    tutor_weight=float(tutor_weight),
                )

                messages.success(
                    request,
                    f"[{title}] 평가 회차가 생성되었습니다.",
                )

            return redirect("tutor_rounds")

    rounds = EvaluationRound.objects.all().order_by("-id")

    return render(
        request,
        "tutor/round_list.html",
        {
            "rounds": rounds,
        },
    )


# =========================================================
# 평가 회차 삭제
# =========================================================
@staff_member_required
def delete_round(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

        name = round_obj.name
        round_obj.delete()

        messages.success(
            request,
            f"[{name}] 평가 회차가 삭제되었습니다.",
        )

    return redirect("tutor_rounds")


# =========================================================
# 평가 회차 정보 수정
# =========================================================
@staff_member_required
def update_round(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

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

        messages.success(
            request,
            f"[{round_obj.name}] 평가 회차 정보가 수정되었습니다.",
        )

    return redirect("tutor_rounds")


# =========================================================
# 평가 회차 상태 변경
# =========================================================
@staff_member_required
def update_round_status(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

        new_status = request.POST.get("status")

        if new_status in EvaluationRound.Status.values:
            round_obj.status = new_status
            round_obj.save()

    return redirect("tutor_rounds")


# =========================================================
# 팀 1위 공개 여부 변경
# =========================================================
@staff_member_required
def toggle_team_first_rank(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

        round_obj.team_first_rank_visible = (
            not round_obj.team_first_rank_visible
        )

        round_obj.save()

    return redirect("tutor_rounds")


# =========================================================
# 팀 구성 확정
# =========================================================
@staff_member_required
def team_confirm(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

        round_obj.status = EvaluationRound.Status.CONFIRMED
        round_obj.save()

        messages.success(
            request,
            f"[{round_obj.name}] 팀 구성이 확정되었습니다.",
        )

    return redirect(
        f"/tutor/team-build/?round_id={round_id}"
    )


# =========================================================
# 점수 집계
# URL: /tutor/rounds/<round_id>/calculate/
# =========================================================
@staff_member_required
def calculate_round_scores(request, round_id):
    from apps.teams.models import TeamMember
    from apps.scoring.services import calculate_round

    round_obj = get_object_or_404(
        EvaluationRound,
        id=round_id,
    )

    if request.method != "POST":
        return redirect("tutor_rounds")

    total_students = TeamMember.objects.filter(
        team__round=round_obj
    ).count()

    if total_students == 0:
        messages.error(
            request,
            f"[{round_obj.name}] 배정된 학생이 없어 집계할 수 없습니다. "
            "먼저 팀 구성을 완료해주세요.",
        )

        return redirect("tutor_rounds")

    saved = calculate_round(round_obj)

    saved_count = len(saved)
    skipped = total_students - saved_count

    if saved_count == 0:
        messages.error(
            request,
            f"[{round_obj.name}] 집계할 학생이 없습니다. "
            "학생 평가와 튜터 평가가 모두 등록되어야 점수가 계산됩니다.",
        )

    elif skipped > 0:
        messages.warning(
            request,
            f"[{round_obj.name}] {saved_count}명 집계 완료. "
            f"{skipped}명은 평가 데이터 부족으로 제외되었습니다.",
        )

    else:
        messages.success(
            request,
            f"[{round_obj.name}] 전체 {saved_count}명의 점수 집계가 완료되었습니다.",
        )

    return redirect("tutor_rounds")


# =========================================================
# 팀 구성
# URL: /tutor/team-build/
# =========================================================
@staff_member_required
def team_build(request):
    from apps.teams.models import Team, TeamMember
    from apps.teams.views import is_round_editable

    round_id = request.GET.get("round_id")

    if round_id:
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )
    else:
        round_obj = EvaluationRound.objects.order_by("-id").first()

    from apps.evaluations.models import ScoreResult

    has_score_history = False

    if round_obj:
        has_score_history = ScoreResult.objects.filter(
            round__status="finished",
            round_id__lt=round_obj.id,
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
            TeamMember.objects.filter(
                team__round=round_obj
            ).values_list(
                "student_id",
                flat=True,
            )
        )

    from django.contrib.auth import get_user_model

    User = get_user_model()

    unassigned_students = (
        User.objects.filter(
            role=User.Role.STUDENT
        )
        .exclude(
            id__in=assigned_ids
        )
    )

    return render(
        request,
        "tutor/team_build.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
            "teams": teams,
            "unassigned_students": unassigned_students,
            "round_editable": (
                is_round_editable(round_obj)
                if round_obj
                else False
            ),
            "has_score_history": has_score_history,
        },
    )


# =========================================================
# 팀 구성 잠금 해제
# =========================================================
@staff_member_required
def unlock_round_formation(request, round_id):
    if request.method == "POST":
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

        if round_obj.status == EvaluationRound.Status.READY:
            round_obj.status = EvaluationRound.Status.DRAFT

            round_obj.save(
                update_fields=["status"]
            )

            messages.success(
                request,
                "팀 구성을 다시 수정할 수 있습니다.",
            )

        else:
            messages.error(
                request,
                f"현재 상태({round_obj.get_status_display()})에서는 수정할 수 없습니다.",
            )

        return redirect(
            f"/tutor/team-build/?round_id={round_obj.id}"
        )

    return redirect("tutor_team_build")


# =========================================================
# 팀 발표 시작
# URL: /tutor/teams/<id>/open/
# =========================================================
@staff_member_required
def open_team_presentation(request, team_id):
    from django.utils import timezone
    from apps.teams.models import Team

    if request.method == "POST":
        team = get_object_or_404(
            Team,
            id=team_id,
        )

        round_obj = team.round

        if round_obj.status == EvaluationRound.Status.DRAFT:
            messages.error(
                request,
                "팀 구성이 아직 확정되지 않았습니다. "
                "먼저 팀 구성에서 팀 구성을 확정해주세요.",
            )

        elif team.members.count() == 0:
            messages.error(
                request,
                f"{team.name}에 배정된 학생이 없어 발표를 시작할 수 없습니다.",
            )

        elif not team.eval_opened_at:
            team.eval_opened_at = timezone.now()
            team.eval_status = Team.EvalStatus.OPEN
            team.save()

            messages.success(
                request,
                f"{team.name} 발표가 시작되어 평가가 열렸습니다.",
            )

        return redirect(
            f"/tutor/team-evaluation/?round_id={round_obj.id}"
        )

    return redirect("tutor_team_evaluation")


# =========================================================
# 튜터 평가 공통
# =========================================================
def _selected_round(request):
    round_id = (
        request.GET.get("round_id")
        or request.POST.get("round_id")
    )

    if round_id:
        return get_object_or_404(
            EvaluationRound,
            id=round_id,
        )

    return EvaluationRound.objects.order_by("-id").first()


# =========================================================
# 튜터 평가 문항
#
# 중요:
# 팀 평가  -> TEAM
# 개인 평가 -> INDIVIDUAL
# =========================================================
def _tutor_template_items(round_obj, template_type):
    if not round_obj:
        return []

    template = EvaluationTemplate.objects.filter(
        round=round_obj,
        type=template_type,
    ).first()

    if not template:
        return []

    if not isinstance(template.criteria, list):
        return []

    return template.criteria


# =========================================================
# POST 평가 답변 수집
# =========================================================
def _collect_answers(request, items):
    answers = {}

    for item in items:
        key = item.get("key")

        value = request.POST.get(
            f"item_{key}"
        )

        if value:
            try:
                score = int(value)

                if score < 1 or score > 5:
                    return None, None

                answers[key] = score

            except (TypeError, ValueError):
                return None, None

    if not items:
        return None, None

    if len(answers) != len(items):
        return None, None

    scores = list(answers.values())

    return (
        answers,
        sum(scores) / len(scores),
    )


# =========================================================
# 튜터 팀 평가 목록
# URL: /tutor/team-evaluation/
# =========================================================
@staff_member_required
def team_evaluation(request):
    from apps.teams.models import Team
    from apps.evaluations.models import TutorEvaluation

    round_obj = _selected_round(request)

    evaluations = []

    if round_obj:
        teams = (
            Team.objects.filter(
                round=round_obj
            )
            .order_by("id")
        )

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
                    "score": (
                        existing.score
                        if existing
                        else None
                    ),
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
            "formation_confirmed": bool(
                round_obj
                and round_obj.status
                != EvaluationRound.Status.DRAFT
            ),
        },
    )


# =========================================================
# 튜터 팀 평가 입력
# URL: /tutor/team-evaluation/<team_id>/
#
# TEAM 평가 문항 사용
# =========================================================
@staff_member_required
def team_evaluation_form(request, team_id):
    from apps.teams.models import Team
    from apps.evaluations.models import TutorEvaluation

    target_team = get_object_or_404(
        Team,
        id=team_id,
    )

    round_obj = target_team.round

    items = _tutor_template_items(
        round_obj,
        EvaluationTemplate.TemplateType.TEAM,
    )

    existing = TutorEvaluation.objects.filter(
        round=round_obj,
        evaluator=request.user,
        team=target_team,
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
        answers, avg_score = _collect_answers(
            request,
            display_items,
        )

        if answers is None:
            messages.error(
                request,
                "모든 문항에 1~5점으로 응답해주세요.",
            )

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

            messages.success(
                request,
                f"{target_team.name} 팀 평가가 저장되었습니다.",
            )

            return redirect(
                f"/tutor/team-evaluation/?round_id={round_obj.id}"
            )

    return render(
        request,
        "tutor/team_evaluation_form.html",
        {
            "round": round_obj,
            "target_team": target_team,
            "items": display_items,
        },
    )


# =========================================================
# 튜터 개인 평가 목록
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
            TeamMember.objects.filter(
                team__round=round_obj
            )
            .select_related(
                "student",
                "team",
            )
            .order_by(
                "team__id",
                "student__username",
            )
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
            existing = my_scores.get(
                member.student_id
            )

            evaluations.append(
                {
                    "student": member.student,
                    "team": member.team,
                    "score": (
                        existing.score
                        if existing
                        else None
                    ),
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
# 튜터 개인 평가 입력
# URL: /tutor/individual-evaluation/<student_id>/
#
# INDIVIDUAL 평가 문항 사용
# =========================================================
@staff_member_required
def individual_evaluation_form(request, student_id):
    from apps.teams.models import TeamMember
    from apps.evaluations.models import TutorEvaluation

    round_obj = _selected_round(request)

    if not round_obj:
        messages.error(
            request,
            "평가 회차가 없습니다.",
        )

        return redirect(
            "tutor_individual_evaluation"
        )

    membership = get_object_or_404(
        TeamMember.objects.select_related(
            "student",
            "team",
        ),
        student_id=student_id,
        team__round=round_obj,
    )

    target_student = membership.student

    items = _tutor_template_items(
        round_obj,
        EvaluationTemplate.TemplateType.INDIVIDUAL,
    )

    existing = TutorEvaluation.objects.filter(
        round=round_obj,
        evaluator=request.user,
        user=target_student,
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
        answers, avg_score = _collect_answers(
            request,
            display_items,
        )

        if answers is None:
            messages.error(
                request,
                "모든 문항에 1~5점으로 응답해주세요.",
            )

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
                request,
                f"{target_student.username} 학생의 튜터 개인 평가가 저장되었습니다.",
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
            "items": display_items,
        },
    )


# =========================================================
# 평가 문항 템플릿 관리
# URL: /tutor/templates/
# =========================================================
@staff_member_required
def template_list(request):
    templates = (
        EvaluationTemplate.objects
        .select_related("round")
        .order_by("-id")
    )

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

        keys = request.POST.getlist(
            "item_key"
        )

        texts = request.POST.getlist(
            "item_text"
        )

        criteria = [
            {
                "key": key,
                "text": text,
            }
            for key, text in zip(
                keys,
                texts,
            )
            if key and text
        ]

        if (
            round_id
            and template_type
            and criteria
        ):
            EvaluationTemplate.objects.update_or_create(
                round_id=round_id,
                type=template_type,
                defaults={
                    "criteria": criteria
                },
            )

            return redirect(
                "tutor_templates"
            )

    default_items = {
        "TEAM": [
            {
                "key": "quality",
                "text": "결과물 완성도",
            },
            {
                "key": "contribution",
                "text": "팀 기여도",
            },
            {
                "key": "cooperation",
                "text": "협업 및 소통",
            },
            {
                "key": "presentation",
                "text": "발표 및 전달력",
            },
        ],
        "INDIVIDUAL": [
            {
                "key": "attitude",
                "text": "참여 태도 및 성실성",
            },
            {
                "key": "task_completion",
                "text": "맡은 역할 수행",
            },
            {
                "key": "communication",
                "text": "의사소통",
            },
        ],
        "TUTOR": [
            {
                "key": "understanding",
                "text": "주제 이해도 및 기술력",
            },
            {
                "key": "output",
                "text": "최종 결과물 완성도",
            },
            {
                "key": "growth",
                "text": "프로젝트 발전 가능성",
            },
        ],
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
# 공개 설정
# URL: /tutor/settings/
# =========================================================
@staff_member_required
def tutor_settings(request):
    round_id = (
        request.GET.get("round_id")
        or request.POST.get("round_id")
    )

    if round_id:
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )
    else:
        round_obj = EvaluationRound.objects.order_by(
            "-id"
        ).first()

    if request.method == "POST" and round_obj:
        round_obj.team_first_rank_visible = (
            "team_first_rank_visible"
            in request.POST
        )

        round_obj.team_rank_visible = (
            "team_rank_visible"
            in request.POST
        )

        round_obj.individual_score_visible = (
            "individual_score_visible"
            in request.POST
        )

        round_obj.individual_rank_visible = (
            "individual_rank_visible"
            in request.POST
        )

        round_obj.save()

        return redirect(
            f"/tutor/settings/?round_id={round_obj.id}"
        )

    return render(
        request,
        "tutor/settings.html",
        {
            "round": round_obj,
            "rounds": EvaluationRound.objects.order_by("-id"),
        },
    )


# =========================================================
# 평가 현황
# URL: /tutor/evaluation-status/
# =========================================================
@staff_member_required
def evaluation_status(request):
    from apps.teams.models import Team, TeamMember
    from apps.evaluations.models import (
        IndividualEvaluation,
        TeamEvaluation,
    )

    round_id = request.GET.get("round_id")

    if round_id:
        round_obj = get_object_or_404(
            EvaluationRound,
            id=round_id,
        )
    else:
        round_obj = EvaluationRound.objects.order_by(
            "-id"
        ).first()

    status = None
    non_submitters = []

    if round_obj:
        members = (
            TeamMember.objects.filter(
                team__round=round_obj
            )
            .select_related(
                "student",
                "team",
            )
            .order_by(
                "student__username"
            )
        )

        total_students = members.count()

        submitted_ids = set(
            IndividualEvaluation.objects.filter(
                round=round_obj,
                is_final=True,
            ).values_list(
                "evaluator_id",
                flat=True,
            )
        )

        completed_students = len(
            {
                m.student_id
                for m in members
                if m.student_id in submitted_ids
            }
        )

        remaining_students = (
            total_students
            - completed_students
        )

        completion_rate = (
            round(
                completed_students
                / total_students
                * 100
            )
            if total_students
            else 0
        )

        non_submitters = [
            m.student
            for m in members
            if m.student_id not in submitted_ids
        ]

        teams = Team.objects.filter(
            round=round_obj
        )

        total_teams = teams.count()
        completed_teams = 0

        for team in teams:
            evaluators_count = (
                TeamEvaluation.objects.filter(
                    round=round_obj,
                    target_team=team,
                )
                .values(
                    "evaluator_team"
                )
                .distinct()
                .count()
            )

            if (
                total_teams > 1
                and evaluators_count
                >= total_teams - 1
            ):
                completed_teams += 1

        remaining_teams = (
            total_teams
            - completed_teams
        )

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
# =========================================================
@staff_member_required
def student_score_overview(request):
    from django.contrib.auth import get_user_model
    from apps.evaluations.models import ScoreResult

    User = get_user_model()

    results = (
        ScoreResult.objects.filter(
            user__role=User.Role.STUDENT
        )
        .select_related(
            "round",
            "user",
        )
        .order_by(
            "user_id",
            "-round_id",
        )
    )

    by_student = {}

    for result in results:
        entry = by_student.setdefault(
            result.user_id,
            {
                "student": result.user,
                "results": [],
            },
        )

        entry["results"].append(result)

    overview = []

    for entry in by_student.values():
        scores = [
            r.final_score
            for r in entry["results"]
            if r.final_score is not None
        ]

        overview.append(
            {
                "student": entry["student"],
                "round_count": len(
                    entry["results"]
                ),
                "avg_score": (
                    round(
                        sum(scores)
                        / len(scores),
                        2,
                    )
                    if scores
                    else 0.0
                ),
                "latest": entry["results"][0],
            }
        )

    scored_ids = set(
        by_student.keys()
    )

    unscored_students = (
        User.objects.filter(
            role=User.Role.STUDENT,
            is_active=True,
        )
        .exclude(
            id__in=scored_ids
        )
    )

    for student in unscored_students:
        overview.append(
            {
                "student": student,
                "round_count": 0,
                "avg_score": 0.0,
                "latest": None,
            }
        )

    overview.sort(
        key=lambda row: (
            -row["avg_score"],
            row["student"].username,
        )
    )

    return render(
        request,
        "tutor/student_scores.html",
        {
            "overview": overview,
        },
    )