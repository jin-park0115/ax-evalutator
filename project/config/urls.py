from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
from django.urls import path, include

from apps.accounts.views import home
from apps.evaluations.views_tutor import round_list, team_build


urlpatterns = [
    path("", home, name="home"),
    path("student/", include("apps.students.urls")),
    path("tutor/rounds/", tutor_rounds, name="tutor_rounds"),
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="accounts/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
]