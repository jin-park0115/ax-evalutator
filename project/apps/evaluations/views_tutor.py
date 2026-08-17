from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from apps.evaluations.models import EvaluationRound


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
# 팀 편성 (다른 팀원 목업 유지)
# URL: /tutor/team-build/
# =========================================================
def team_build(request):
    print("team_build 호출됨")
    print("요청 방식:", request.method)
    print("POST 데이터:", request.POST)

    if request.method == "POST":
        if "auto_assign" in request.POST:
            print("자동 편성 실행!")

    teams = [
        {
            "team_no": 1,
            "avg_seed": 82.4,
            "members": [
                {"name": "김철수", "team_no": 1},
                {"name": "이영희", "team_no": 1},
            ],
        },
        {
            "team_no": 2,
            "avg_seed": 81.9,
            "members": [
                {"name": "박민수", "team_no": 2},
                {"name": "최지우", "team_no": 2},
            ],
        },
        {
            "team_no": 3,
            "avg_seed": 80.7,
            "members": [
                {"name": "정수빈", "team_no": 3},
                {"name": "한지민", "team_no": 3},
            ],
        },
    ]

    students = [
        {"name": "김철수", "team_no": 1},
        {"name": "이영희", "team_no": 1},
        {"name": "박민수", "team_no": 2},
        {"name": "최지우", "team_no": 2},
        {"name": "정수빈", "team_no": 3},
        {"name": "한지민", "team_no": 3},
    ]

    return render(
        request,
        "tutor/team_build.html",
        {
            "teams": teams,
            "students": students,
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
# 템플릿 관리 (다른 팀원 목업 유지)
# URL: /tutor/templates/
# =========================================================
def template_list(request):
    templates = [
        {
            "id": 1,
            "name": "기본 팀 평가 템플릿",
            "type": "팀 평가",
            "question_count": 5,
            "status": "사용중",
        },
        {
            "id": 2,
            "name": "기본 개인 평가 템플릿",
            "type": "개인 평가",
            "question_count": 6,
            "status": "사용중",
        },
        {
            "id": 3,
            "name": "최종 프로젝트 평가",
            "type": "팀 평가",
            "question_count": 8,
            "status": "보관",
        },
    ]

    return render(
        request,
        "tutor/templates.html",
        {
            "templates": templates,
        },
    )


# =========================================================
# 공개 설정 (다른 팀원 목업 유지)
# URL: /tutor/settings/
# =========================================================
def tutor_settings(request):
    settings = {
        "evaluation_open": True,
        "result_open": False,
        "student_visible": True,
        "anonymous": False,
    }

    return render(
        request,
        "tutor/settings.html",
        {
            "settings": settings,
        },
    )


# =========================================================
# 평가 현황 (다른 팀원 목업 유지)
# URL: /tutor/evaluation-status/
# =========================================================
def evaluation_status(request):
    status = {
        "total_students": 6,
        "completed_students": 4,
        "remaining_students": 2,
        "completion_rate": 66,
        "total_teams": 3,
        "completed_teams": 2,
        "remaining_teams": 1,
    }

    return render(
        request,
        "tutor/evaluation_status.html",
        {
            "status": status,
        },
    )