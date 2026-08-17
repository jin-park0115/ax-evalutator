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
        "pending-users/<int:user_id>/reject/",
        views.reject_user,
        name="reject_user",
    ),
]