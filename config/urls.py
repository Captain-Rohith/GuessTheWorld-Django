from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def root_redirect(request):
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect("admin_daily_report")
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", root_redirect, name="root"),
    path("", include("accounts.urls")),
    path("", include("game.urls")),
    path("", include("admin_dashboard.urls")),
]
