from django.urls import path
from .views import (
    admin_root_redirect,
    daily_report_view,
    user_performance_report_view,
    word_pool_view,
    toggle_word_status,
    delete_word,
)

urlpatterns = [
    path("admin-dashboard/", admin_root_redirect, name="admin_dashboard"),
    path("admin-dashboard/daily/", daily_report_view, name="admin_daily_report"),
    path("admin-dashboard/users/", user_performance_report_view, name="admin_user_report"),
    path("admin-dashboard/words/", word_pool_view, name="admin_word_pool"),
    path("admin-dashboard/words/<int:word_id>/toggle/", toggle_word_status, name="admin_toggle_word"),
    path("admin-dashboard/words/<int:word_id>/delete/", delete_word, name="admin_delete_word"),
]
