# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from .forms import CustomUserCreationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render

User = get_user_model()

# 홈 화면
def home(request):
    return render(request, "home.html")


# 회원가입 (승인 대기 상태로 저장)
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "회원가입 신청이 완료되었습니다. 관리자 승인 후 로그인 가능합니다.")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})


# 로그인
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('home')
        else:
            messages.error(request, "이메일 또는 비밀번호가 올바르지 않거나, 승인 대기 중인 계정입니다.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


# 로그아웃
def logout_view(request):
    auth_logout(request)
    return redirect('login')

# 1. 승인 대기 / 역할 부여 대기 회원 목록 조회
@staff_member_required
def pending_user_list(request):
    pending_users = User.objects.filter(role=User.Role.PENDING)
    approved_users = User.objects.filter(role=User.Role.APPROVED)
    return render(
        request,
        "accounts/pending_list.html",
        {
            "pending_users": pending_users,
            "approved_users": approved_users,
        },
    )


# 2. 회원 가입 승인 처리 (PENDING -> APPROVED, 역할부여 대기 상태로만 전환)
@staff_member_required
def approve_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        user.role = User.Role.APPROVED
        user.save()
        messages.success(
            request, f"{user.username} ({user.email}) 님이 승인되었습니다. 역할 부여가 필요합니다."
        )
    return redirect("pending_user_list")


# 3. 역할 부여 처리 (APPROVED -> STUDENT/ADMIN, 이 시점부터 로그인 가능)
@staff_member_required
def assign_role(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id, role=User.Role.APPROVED)
        role = request.POST.get("role")
        if role not in (User.Role.STUDENT, User.Role.ADMIN):
            messages.error(request, "역할은 학생 또는 관리자 중에서 선택해야 합니다.")
            return redirect("pending_user_list")
        user.role = role
        if role == User.Role.ADMIN:
            user.is_staff = True
        user.save()
        messages.success(
            request, f"{user.username} ({user.email}) 님에게 {user.get_role_display()} 역할이 부여되었습니다."
        )
    return redirect("pending_user_list")


# 4. 회원 가입 거절 처리
@staff_member_required
def reject_user(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(User, id=user_id)
        user.delete()  # 거절 시 DB에서 삭제
        messages.warning(
            request, f"{user.username} ({user.email}) 님의 가입 신청이 거절되었습니다."
        )
    return redirect("pending_user_list")


# 5. 이미 역할이 부여된(STUDENT/ADMIN) 회원 목록 조회
# assign_role은 role=APPROVED인 사람만 대상으로 하므로, 이미 역할이
# 부여된 회원을 다시 조회/변경하려면 별도 화면이 필요하다.
@staff_member_required
def user_list(request):
    query = request.GET.get("q", "").strip()
    users = User.objects.filter(
        role__in=[User.Role.STUDENT, User.Role.ADMIN]
    ).order_by("-role", "username")
    if query:
        users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
    return render(request, "accounts/user_list.html", {"users": users, "query": query})


# 6. 이미 역할이 부여된 회원의 역할 변경 (학생 <-> 관리자)
@staff_member_required
def update_user_role(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(
            User, id=user_id, role__in=[User.Role.STUDENT, User.Role.ADMIN]
        )
        role = request.POST.get("role")
        if role not in (User.Role.STUDENT, User.Role.ADMIN):
            messages.error(request, "역할은 학생 또는 관리자 중에서 선택해야 합니다.")
            return redirect("user_list")
        if user == request.user and role != User.Role.ADMIN:
            messages.error(request, "본인의 관리자 권한은 스스로 해제할 수 없습니다.")
            return redirect("user_list")
        user.role = role
        # ADMIN으로 바꾸면 is_staff도 켜주고, ADMIN에서 내려오면 꺼준다
        # (기존 assign_role은 승격만 다뤄서 강등 시 is_staff를 그대로
        # 두는 문제가 있었다)
        user.is_staff = role == User.Role.ADMIN
        user.save()
        messages.success(
            request,
            f"{user.username} ({user.email}) 님의 역할이 {user.get_role_display()}(으)로 변경되었습니다.",
        )
    return redirect("user_list")


# 7. 이미 역할이 부여된 회원 활성/비활성 전환 (탈퇴 대신 로그인만 차단)
@staff_member_required
def toggle_user_active(request, user_id):
    if request.method == "POST":
        user = get_object_or_404(
            User, id=user_id, role__in=[User.Role.STUDENT, User.Role.ADMIN]
        )
        if user == request.user:
            messages.error(request, "본인 계정은 비활성화할 수 없습니다.")
            return redirect("user_list")
        user.is_active = not user.is_active
        user.save()
        state = "활성화" if user.is_active else "비활성화"
        messages.success(request, f"{user.username} ({user.email}) 님의 계정이 {state}되었습니다.")
    return redirect("user_list")