# apps/accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # 관리자 전용 회원 승인 관련 URL
    path("pending-users/", views.pending_user_list, name="pending_user_list"),
    path(
        "pending-users/<int:user_id>/approve/",
        views.approve_user,
        name="approve_user",
    ),
    path(
        "pending-users/<int:user_id>/assign-role/",
        views.assign_role,
        name="assign_role",
    ),
    path(
        "pending-users/<int:user_id>/reject/",
        views.reject_user,
        name="reject_user",
    ),
    # 이미 역할이 부여된 회원 관리
    path("users/", views.user_list, name="user_list"),
    path(
        "users/<int:user_id>/update-role/",
        views.update_user_role,
        name="update_user_role",
    ),
    path(
        "users/<int:user_id>/toggle-active/",
        views.toggle_user_active,
        name="toggle_user_active",
    ),
]