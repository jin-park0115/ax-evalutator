from django.urls import path

from app.api.health import health_check

urlpatterns = [
    path("api/health/", health_check, name="health-check"),
]

