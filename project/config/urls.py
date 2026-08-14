from django.contrib import admin
from django.urls import path

from apps.accounts.views import home
from apps.evaluations.views_tutor import round_list, team_build


urlpatterns = [
    path("", home, name="home"),

    path("tutor/rounds/", round_list, name="tutor_rounds"),
    path("tutor/team-build/", team_build, name="tutor_team_build"),

    path("admin/", admin.site.urls),
]