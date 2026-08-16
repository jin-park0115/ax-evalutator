from django.shortcuts import render


# =========================================================
# 회차 관리
# URL: /tutor/rounds/
# =========================================================
def round_list(request):
    rounds = [
        {
            "id": 1,
            "title": "1차 팀 평가",
            "assignment": "Django 프로젝트",
            "start_date": "2026-08-14",
            "end_date": "2026-08-18",
            "team_count": 5,
            "status": "대기",
        },
        {
            "id": 2,
            "title": "2차 팀 평가",
            "assignment": "AI 프로젝트",
            "start_date": "2026-08-20",
            "end_date": "2026-08-25",
            "team_count": 6,
            "status": "진행중",
        },
        {
            "id": 3,
            "title": "3차 팀 평가",
            "assignment": "최종 프로젝트",
            "start_date": "2026-08-28",
            "end_date": "2026-09-01",
            "team_count": 5,
            "status": "완료",
        },
    ]

    # 회차 생성
    if request.method == "POST":
        title = request.POST.get("title")
        assignment = request.POST.get("assignment")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        team_count = request.POST.get("team_count")

        if (
            title
            and assignment
            and start_date
            and end_date
            and team_count
        ):
            new_round = {
                "id": len(rounds) + 1,
                "title": title,
                "assignment": assignment,
                "start_date": start_date,
                "end_date": end_date,
                "team_count": int(team_count),
                "status": "대기",
            }

            rounds.append(new_round)

    return render(
        request,
        "tutor/round_list.html",
        {
            "rounds": rounds,
        },
    )


# =========================================================
# 팀 편성
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
# 팀 평가
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
# 개인 평가
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
# 템플릿 관리
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
# 공개 설정
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
# 평가 현황
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