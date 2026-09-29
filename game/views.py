import json
import random
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET

from .models import Word, GameSession, GuessAttempt, GameStatus
from .engine import evaluate_wordle_guess, compute_keyboard_statuses


@login_required
def player_dashboard(request):
    if request.user.is_admin and not request.user.is_player:
        return redirect("admin_daily_report")

    today = timezone.localdate()
    today_sessions = GameSession.objects.filter(
        user=request.user, session_date=today
    ).prefetch_related("guesses").order_by("-created_at")

    played_count = today_sessions.count()
    remaining_quota = max(0, 3 - played_count)
    active_session = today_sessions.filter(status=GameStatus.IN_PROGRESS).first()

    return render(
        request,
        "game/dashboard.html",
        {
            "today_sessions": today_sessions,
            "played_count": played_count,
            "remaining_quota": remaining_quota,
            "max_daily_quota": 3,
            "active_session": active_session,
            "today": today,
        },
    )


@login_required
def start_game(request):
    today = timezone.localdate()
    today_sessions = GameSession.objects.filter(user=request.user, session_date=today)

    active_session = today_sessions.filter(status=GameStatus.IN_PROGRESS).first()
    if active_session:
        return redirect("game_session", session_id=active_session.id)

    if today_sessions.count() >= 3:
        messages.error(request, "Daily game limit reached! You can play at most 3 games per day.")
        return redirect("dashboard")

    active_words = list(Word.objects.filter(is_active=True).values_list("word", flat=True))
    if not active_words:
        messages.error(request, "No active words found in the word pool. Please contact an administrator.")
        return redirect("dashboard")

    target_word = random.choice(active_words).upper()

    session = GameSession.objects.create(
        user=request.user,
        target_word=target_word,
        max_attempts=5,
        attempts_used=0,
        status=GameStatus.IN_PROGRESS,
        session_date=today,
    )
    return redirect("game_session", session_id=session.id)


@login_required
def game_session_view(request, session_id=None):
    today = timezone.localdate()
    if session_id:
        session = get_object_or_404(GameSession, id=session_id, user=request.user)
    else:
        session = GameSession.objects.filter(
            user=request.user, session_date=today, status=GameStatus.IN_PROGRESS
        ).first()
        if not session:
            return redirect("start_game")

    guesses = session.guesses.all().order_by("attempt_number")
    evaluated_attempts = []
    for g in guesses:
        evaluated_attempts.append(evaluate_wordle_guess(session.target_word, g.guess_word))

    keyboard_statuses = compute_keyboard_statuses(evaluated_attempts)

    grid_rows = []
    for row_idx in range(session.max_attempts):
        if row_idx < len(evaluated_attempts):
            grid_rows.append(evaluated_attempts[row_idx])
        else:
            grid_rows.append([{"letter": "", "status": "empty"} for _ in range(5)])

    context = {
        "session": session,
        "grid_rows": grid_rows,
        "evaluated_attempts_json": json.dumps(evaluated_attempts),
        "keyboard_statuses_json": json.dumps(keyboard_statuses),
        "game_status": session.status,
        "target_word_revealed": session.target_word if session.status != GameStatus.IN_PROGRESS else "",
    }
    return render(request, "game/game_board.html", context)


@login_required
@require_POST
def submit_guess(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    session_id = data.get("session_id")
    guess_word = data.get("guess_word", "").strip().upper()

    if not session_id or not guess_word:
        return JsonResponse({"error": "session_id and guess_word are required."}, status=400)

    session = get_object_or_404(GameSession, id=session_id)
    if session.user != request.user:
        return JsonResponse({"error": "Unauthorized session access."}, status=403)

    if session.status != GameStatus.IN_PROGRESS:
        return JsonResponse({
            "error": "This game session is already finished.",
            "status": session.status,
            "target_word": session.target_word
        }, status=400)

    if len(guess_word) != 5 or not guess_word.isalpha():
        return JsonResponse({"error": "Guess must be exactly 5 alphabetic letters."}, status=400)

    evaluation = evaluate_wordle_guess(session.target_word, guess_word)
    current_attempt_num = session.attempts_used + 1

    GuessAttempt.objects.create(
        game_session=session,
        attempt_number=current_attempt_num,
        guess_word=guess_word,
    )

    session.attempts_used = current_attempt_num

    modal_title = None
    modal_message = None

    if guess_word == session.target_word:
        session.status = GameStatus.WON
        session.completed_at = timezone.now()
        modal_title = "Congratulations!"
        modal_message = "Congratulations!"
    elif session.attempts_used >= session.max_attempts:
        session.status = GameStatus.LOST
        session.completed_at = timezone.now()
        modal_title = "Game Over"
        modal_message = f"Better luck next time! The word was: {session.target_word}"

    session.save()

    all_attempts = session.guesses.all().order_by("attempt_number")
    all_evaluations = [evaluate_wordle_guess(session.target_word, a.guess_word) for a in all_attempts]
    keyboard_statuses = compute_keyboard_statuses(all_evaluations)

    return JsonResponse({
        "success": True,
        "evaluation": evaluation,
        "attempt_number": session.attempts_used,
        "attempts_used": session.attempts_used,
        "max_attempts": session.max_attempts,
        "status": session.status,
        "is_game_over": session.status != GameStatus.IN_PROGRESS,
        "target_word": session.target_word if session.status != GameStatus.IN_PROGRESS else None,
        "modal_title": modal_title,
        "modal_message": modal_message,
        "keyboard_statuses": keyboard_statuses,
    })
