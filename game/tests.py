import json
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser, UserRole
from game.models import Word, GameSession, GuessAttempt, GameStatus
from game.engine import evaluate_wordle_guess, compute_keyboard_statuses


class WordModelTests(TestCase):
    def test_valid_word_creation(self):
        w = Word.objects.create(word="SMART")
        self.assertEqual(w.word, "SMART")
        self.assertTrue(w.is_active)

    def test_lowercase_word_converted_to_uppercase(self):
        w = Word.objects.create(word="train")
        self.assertEqual(w.word, "TRAIN")

    def test_invalid_word_length(self):
        with self.assertRaises(ValidationError):
            w = Word(word="FOUR")
            w.full_clean()

    def test_invalid_word_non_alpha(self):
        with self.assertRaises(ValidationError):
            w = Word(word="PL4N1")
            w.full_clean()


class WordleAlgorithmTests(TestCase):
    def test_exact_matches_all_green(self):
        result = evaluate_wordle_guess("APPLE", "APPLE")
        expected = [
            {"letter": "A", "status": "green"},
            {"letter": "P", "status": "green"},
            {"letter": "P", "status": "green"},
            {"letter": "L", "status": "green"},
            {"letter": "E", "status": "green"},
        ]
        self.assertEqual(result, expected)

    def test_all_grey(self):
        result = evaluate_wordle_guess("APPLE", "SHIRT")
        for item in result:
            self.assertEqual(item["status"], "grey")

    def test_misplaced_yellow_and_grey(self):
        # Target: CRANE, Guess: OCEAN
        # Target letters: C:1, R:1, A:1, N:1, E:1
        # O: not in target -> grey
        # C: in target, pos 1 != 0 -> yellow
        # E: in target, pos 2 != 4 -> yellow
        # A: in target, pos 3 != 2 -> yellow
        # N: in target, pos 4 != 3 -> yellow
        result = evaluate_wordle_guess("CRANE", "OCEAN")
        statuses = [item["status"] for item in result]
        self.assertEqual(statuses, ["grey", "yellow", "yellow", "yellow", "yellow"])

    def test_duplicate_frequency_bounds(self):
        # Target: EAGLE (E:2, A:1, G:1, L:1)
        # Guess:  APPLE (A, P, P, L, E)
        # Exact: L (index 3), E (index 4) -> green (E: 1 left, L: 0 left)
        # Misplaced: A (index 0) -> yellow (A: 0 left)
        # P (index 1) -> grey
        # P (index 2) -> grey
        result = evaluate_wordle_guess("EAGLE", "APPLE")
        statuses = [item["status"] for item in result]
        self.assertEqual(statuses, ["yellow", "grey", "grey", "green", "green"])

    def test_duplicate_in_guess_exceeding_target(self):
        # Target: WORLD (O:1)
        # Guess:  ROBOT (O at index 1 is exact -> green; O at index 3 exceeds count -> grey)
        # R at index 0 -> yellow
        # B at index 2 -> grey
        # T at index 4 -> grey
        result = evaluate_wordle_guess("WORLD", "ROBOT")
        statuses = [item["status"] for item in result]
        self.assertEqual(statuses, ["yellow", "green", "grey", "grey", "grey"])

    def test_color_precedence(self):
        # Attempt 1: 'E' is yellow
        # Attempt 2: 'E' is green
        # Attempt 3: 'E' is grey in another context
        # Keyboard status must be 'green' (green > yellow > grey)
        attempts = [
            [{"letter": "E", "status": "yellow"}],
            [{"letter": "E", "status": "green"}],
            [{"letter": "E", "status": "grey"}],
        ]
        keyboard = compute_keyboard_statuses(attempts)
        self.assertEqual(keyboard["E"], "green")


class DailyGameLimitAndGameplayTests(TestCase):
    def setUp(self):
        self.player = CustomUser.objects.create_user(
            username="TestPlayer",
            password="PlayerPass1%",
            role=UserRole.PLAYER,
        )
        self.client.login(username="TestPlayer", password="PlayerPass1%")

    def test_daily_quota_limit_blocks_fourth_game(self):
        today = timezone.localdate()

        # Create 3 finished games for today
        for i in range(3):
            GameSession.objects.create(
                user=self.player,
                target_word="CRANE",
                max_attempts=5,
                attempts_used=5,
                status=GameStatus.LOST,
                session_date=today,
            )

        # Attempt to start a 4th game
        response = self.client.get("/game/start/", follow=True)
        self.assertEqual(response.status_code, 200)

        # Total sessions for today should still be 3
        count = GameSession.objects.filter(user=self.player, session_date=today).count()
        self.assertEqual(count, 3)

        # Check dashboard context shows quota = 0
        dash_response = self.client.get("/dashboard/")
        self.assertEqual(dash_response.context["played_count"], 3)
        self.assertEqual(dash_response.context["remaining_quota"], 0)

    def test_game_flow_win(self):
        session = GameSession.objects.create(
            user=self.player,
            target_word="APPLE",
            max_attempts=5,
            attempts_used=0,
            status=GameStatus.IN_PROGRESS,
            session_date=timezone.localdate(),
        )

        response = self.client.post(
            "/game/guess/",
            data=json.dumps({"session_id": session.id, "guess_word": "APPLE"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["status"], "WON")
        self.assertEqual(data["attempts_used"], 1)

        session.refresh_from_db()
        self.assertEqual(session.status, GameStatus.WON)
        self.assertEqual(session.attempts_used, 1)

    def test_game_flow_loss_after_max_attempts(self):
        session = GameSession.objects.create(
            user=self.player,
            target_word="APPLE",
            max_attempts=5,
            attempts_used=4,
            status=GameStatus.IN_PROGRESS,
            session_date=timezone.localdate(),
        )

        response = self.client.post(
            "/game/guess/",
            data=json.dumps({"session_id": session.id, "guess_word": "CRANE"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "LOST")
        self.assertEqual(data["attempts_used"], 5)
        self.assertEqual(data["target_word"], "APPLE")

        session.refresh_from_db()
        self.assertEqual(session.status, GameStatus.LOST)
