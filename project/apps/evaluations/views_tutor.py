from django.shortcuts import render


def round_list(request):
    rounds = [
        {
            "id": 1,
            "title": "1차 팀 프로젝트 평가",
            "status": "draft",
        },
        {
            "id": 2,
            "title": "2차 Django 평가",
            "status": "진행중",
        },
        {
            "id": 3,
            "title": "최종 평가",
            "status": "완료",
        },
    ]

    return render(
        request,
        "tutor/round_list.html",
        {"rounds": rounds},
    )