from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

from apps.accounts.views import home


def tutor_rounds(request):
    return HttpResponse("tutor rounds - coming soon")


urlpatterns = [
    path("", home, name="home"),
    path("student/", include("apps.students.urls")),
    path("tutor/rounds/", tutor_rounds, name="tutor_rounds"),
    path("admin/", admin.site.urls),
]