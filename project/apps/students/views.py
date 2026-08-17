from django.contrib.auth.decorators import login_required
from django.shortcuts import render

#수강생(Student) 본인이 로그인해서 자신의 홈 화면, 팀 정보, 성적을 보는 학생용 뷰
@login_required
def student_home(request):
    # state = get_student_state(request.user)  ← BE 함수 나오면 이 한 줄로 교체
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
    """BE1의 team_service.get_my_team()이 나오면 이 함수만 교체한다."""
    from apps.teams.models import TeamMember

    student = getattr(user, "student", None)
    if not student:
        return None, []

    tm = TeamMember.objects.select_related("team").filter(student=student).first()
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
    """BE2의 score_service.get_visible_result()가 나오면 이 함수만 교체한다."""
    return None


# ==========================================
# 관리자 전용 수강생 관리 API (이어서 추가)
# ==========================================
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods

User = get_user_model()


# 1. 승인된 학생 목록 조회 (GET)
@staff_member_required
@require_http_methods(["GET"])
def student_list(request):
    students = User.objects.filter(role=User.Role.STUDENT).values(
        "id", "username", "email", "date_joined"
    )
    return JsonResponse({"students": list(students)}, status=200)


# 2. 학생 정보 수정 (POST / PUT)
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


# 3. 학생 삭제 (role을 PENDING으로 변경)
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