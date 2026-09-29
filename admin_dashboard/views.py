from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.models import CustomUser, UserRole
from game.models import Word, GameSession, GameStatus, validate_five_letter_word


def admin_check(user):
    return user.is_authenticated and (user.role == UserRole.ADMIN or user.is_staff or user.is_superuser)


@user_passes_test(admin_check, login_url="login")
def admin_root_redirect(request):
    return redirect("admin_daily_report")


@user_passes_test(admin_check, login_url="login")
def daily_report_view(request):
    selected_date_str = request.GET.get("date", "").strip()
    selected_date = None

    player_users = CustomUser.objects.filter(role=UserRole.PLAYER, is_staff=False, is_superuser=False)
    base_sessions = GameSession.objects.filter(user__in=player_users)

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
            filtered_sessions = base_sessions.filter(session_date=selected_date)
        except ValueError:
            filtered_sessions = base_sessions
            selected_date_str = ""
    else:
        filtered_sessions = base_sessions

    total_words_tried = filtered_sessions.count()
    active_users_count = filtered_sessions.values("user").distinct().count()
    correct_guesses_count = filtered_sessions.filter(status=GameStatus.WON).count()
    success_rate = (
        round((correct_guesses_count / total_words_tried) * 100, 1)
        if total_words_tried > 0
        else 0.0
    )

    dates_qs = (
        filtered_sessions.values("session_date")
        .annotate(
            user_count=Count("user", distinct=True),
            words_tried=Count("id"),
            correct_guesses=Count("id", filter=Q(status=GameStatus.WON)),
        )
        .order_by("-session_date")
    )

    table_data = []
    for row in dates_qs:
        tried = row["words_tried"]
        won = row["correct_guesses"]
        rate = round((won / tried) * 100, 1) if tried > 0 else 0.0
        table_data.append({
            "date": row["session_date"],
            "user_count": row["user_count"],
            "words_tried": tried,
            "correct_guesses": won,
            "success_rate": f"{rate}%",
        })

    context = {
        "active_tab": "daily",
        "selected_date": selected_date_str,
        "summary": {
            "active_users": active_users_count,
            "words_tried": total_words_tried,
            "correct_guesses": correct_guesses_count,
            "success_rate": f"{success_rate}%",
        },
        "table_data": table_data,
    }
    return render(request, "admin_dashboard/daily_report.html", context)


@user_passes_test(admin_check, login_url="login")
def user_performance_report_view(request):
    players = CustomUser.objects.filter(
        role=UserRole.PLAYER, is_staff=False, is_superuser=False
    ).order_by("username")

    selected_player_id = request.GET.get("user_id", "").strip()
    selected_player = None

    base_sessions = GameSession.objects.filter(user__in=players)

    if selected_player_id:
        try:
            selected_player = players.get(id=int(selected_player_id))
            filtered_sessions = base_sessions.filter(user=selected_player)
        except (ValueError, CustomUser.DoesNotExist):
            filtered_sessions = base_sessions
            selected_player_id = ""
    else:
        filtered_sessions = base_sessions

    user_date_qs = (
        filtered_sessions.values("user__username", "session_date")
        .annotate(
            words_tried=Count("id"),
            correct_guesses=Count("id", filter=Q(status=GameStatus.WON)),
        )
        .order_by("-session_date", "user__username")
    )

    table_data = []
    total_words_tried = 0
    total_correct = 0

    for row in user_date_qs:
        tried = row["words_tried"]
        won = row["correct_guesses"]
        rate = round((won / tried) * 100, 1) if tried > 0 else 0.0
        total_words_tried += tried
        total_correct += won
        table_data.append({
            "username": row["user__username"],
            "date": row["session_date"],
            "words_tried": tried,
            "correct_guesses": won,
            "success_rate": f"{rate}%",
        })

    overall_rate = (
        round((total_correct / total_words_tried) * 100, 1)
        if total_words_tried > 0
        else 0.0
    )

    context = {
        "active_tab": "users",
        "players": players,
        "selected_player_id": selected_player_id,
        "selected_player": selected_player,
        "summary": {
            "total_players": players.count(),
            "words_tried": total_words_tried,
            "correct_guesses": total_correct,
            "success_rate": f"{overall_rate}%",
        },
        "table_data": table_data,
    }
    return render(request, "admin_dashboard/user_report.html", context)


@user_passes_test(admin_check, login_url="login")
def word_pool_view(request):
    words = Word.objects.all().order_by("word")

    if request.method == "POST":
        new_word_input = request.POST.get("word", "").strip().upper()
        if not new_word_input:
            messages.error(request, "Please enter a word.")
        elif len(new_word_input) != 5 or not new_word_input.isalpha():
            messages.error(request, "Word must consist of exactly 5 alphabetic letters.")
        elif Word.objects.filter(word=new_word_input).exists():
            messages.error(request, f"Word '{new_word_input}' already exists in the word pool.")
        else:
            try:
                Word.objects.create(word=new_word_input, is_active=True)
                messages.success(request, f"Word '{new_word_input}' added successfully to the pool.")
                return redirect("admin_word_pool")
            except ValidationError as e:
                messages.error(request, str(e))

    active_count = words.filter(is_active=True).count()
    inactive_count = words.filter(is_active=False).count()

    context = {
        "active_tab": "words",
        "words": words,
        "total_words": words.count(),
        "active_count": active_count,
        "inactive_count": inactive_count,
    }
    return render(request, "admin_dashboard/word_pool.html", context)


@user_passes_test(admin_check, login_url="login")
@require_POST
def toggle_word_status(request, word_id):
    word_obj = get_object_or_404(Word, id=word_id)
    word_obj.is_active = not word_obj.is_active
    word_obj.save()
    status_str = "Active" if word_obj.is_active else "Inactive"
    messages.success(request, f"Status for '{word_obj.word}' changed to {status_str}.")
    return redirect("admin_word_pool")


@user_passes_test(admin_check, login_url="login")
@require_POST
def delete_word(request, word_id):
    word_obj = get_object_or_404(Word, id=word_id)
    word_str = word_obj.word
    word_obj.delete()
    messages.success(request, f"Word '{word_str}' deleted from word pool.")
    return redirect("admin_word_pool")
