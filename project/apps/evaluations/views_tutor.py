from django.shortcuts import render


def round_list(request):
    rounds = [
        {
            "id": 1,
            "title": "1차 팀 평가",
            "assignment": "Django 프로젝트",
            "start_date": "2026-08-14",
            "end_date": "2026-08-18",
            "team_count": 5,
            "status": "draft",
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

    return render(
        request,
        "tutor/round_list.html",
        {"rounds": rounds},
    )
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