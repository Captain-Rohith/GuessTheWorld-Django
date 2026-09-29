from django.urls import path
from .views import player_dashboard, start_game, game_session_view, submit_guess

urlpatterns = [
    path("dashboard/", player_dashboard, name="dashboard"),
    path("game/start/", start_game, name="start_game"),
    path("game/", game_session_view, name="current_game"),
    path("game/<int:session_id>/", game_session_view, name="game_session"),
    path("game/guess/", submit_guess, name="submit_guess"),
]
