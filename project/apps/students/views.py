from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def student_home(request):
    state = request.GET.get("state", "before")
    team, members = get_my_team(request.user)
    return render(request, "student/home.html", {"state": state, "team": team})


@login_required
def student_team(request):
    team, members = get_my_team(request.user)
    return render(request, "student/team.html", {"team": team, "members": members})


@login_required
def student_result(request):
    result = get_visible_result(request.user)
    return render(request, "student/result.html", {"result": result})


def get_my_team(user):
    from apps.teams.models import TeamMember

    # Student 모델 제거 -> user를 직접 FK로 조회
    tm = TeamMember.objects.select_related("team").filter(student=user).first()
    if not tm:
        return None, []

    members = (
        TeamMember.objects
        .filter(team=tm.team)
        .select_related("student")
        .order_by("id")
    )
    return tm.team, members


def get_visible_result(user):
    """get_visible_result(user, round) 계약의 임시 구현.
    BE2의 calculate_round()/score_service.get_visible_result()가 나오면
    이 함수 전체를 그걸로 교체한다.

    team_first(1위 팀명), formula(계산 과정 문자열)는 집계 로직이
    있어야 나오는 값이라 여기서는 채우지 않는다.
    """
    from apps.evaluations.models import EvaluationRound, ScoreResult

    round_obj = (
        EvaluationRound.objects.filter(
            status=EvaluationRound.Status.IN_PROGRESS
        )
        .order_by("-id")
        .first()
        or EvaluationRound.objects.order_by("-id").first()
    )
    if not round_obj:
        return None

    score = ScoreResult.objects.filter(round=round_obj, user=user).first()
    if not score:
        return None

    return {
        "team_score": score.team_score if round_obj.team_rank_visible else None,
        "personal_score": score.individual_score if round_obj.individual_score_visible else None,
        "final_score": score.final_score,
        "rank": score.rank if round_obj.individual_rank_visible else None,
    }


# ==========================================
# 관리자 전용 수강생 관리 API
# ==========================================
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

User = get_user_model()


@staff_member_required
@require_http_methods(["GET"])
def student_list(request):
    students = User.objects.filter(role=User.Role.STUDENT).values(
        "id", "username", "email", "date_joined"
    )
    return JsonResponse({"students": list(students)}, status=200)


@staff_member_required
@require_http_methods(["POST", "PUT"])
def update_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = request.POST

    username = data.get("username")
    email = data.get("email")

    if username:
        student.username = username
    if email:
        if User.objects.filter(email=email).exclude(id=student.id).exists():
            return JsonResponse({"error": "이미 사용 중인 이메일입니다."}, status=400)
        student.email = email

    student.save()
    return JsonResponse(
        {"message": f"{student.username} 학생의 정보가 수정되었습니다."},
        status=200,
    )


@staff_member_required
@require_http_methods(["POST", "DELETE"])
def delete_student(request, student_id):
    student = get_object_or_404(User, id=student_id, role=User.Role.STUDENT)
    student.role = User.Role.PENDING
    student.save()
    
    return JsonResponse(
        {"message": f"{student.username} 학생이 목록에서 삭제되고 승인 대기 상태로 변경되었습니다."},
        status=200,
    )