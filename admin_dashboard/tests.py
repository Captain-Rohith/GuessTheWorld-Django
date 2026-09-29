from datetime import date, timedelta
from django.test import TestCase
from accounts.models import CustomUser, UserRole
from game.models import Word, GameSession, GameStatus


class AdminReportTests(TestCase):
    def setUp(self):
        # Admin User
        self.admin_user = CustomUser.objects.create_superuser(
            username="AdminTester",
            password="AdminPassword1$",
            role=UserRole.ADMIN,
        )

        # Player Users
        self.player1 = CustomUser.objects.create_user(
            username="PlayerAlpha",
            password="PlayerPassword1%",
            role=UserRole.PLAYER,
        )
        self.player2 = CustomUser.objects.create_user(
            username="PlayerBeta",
            password="PlayerPassword1%",
            role=UserRole.PLAYER,
        )

        today = date.today()
        yesterday = today - timedelta(days=1)

        # Player 1 Sessions (Today: 2 sessions, 1 WON, 1 LOST)
        GameSession.objects.create(
            user=self.player1,
            target_word="APPLE",
            attempts_used=3,
            status=GameStatus.WON,
            session_date=today,
        )
        GameSession.objects.create(
            user=self.player1,
            target_word="CRANE",
            attempts_used=5,
            status=GameStatus.LOST,
            session_date=today,
        )

        # Player 2 Sessions (Today: 1 session, 1 WON)
        GameSession.objects.create(
            user=self.player2,
            target_word="LIGHT",
            attempts_used=4,
            status=GameStatus.WON,
            session_date=today,
        )

        # Player 1 Session (Yesterday: 1 session, 1 WON)
        GameSession.objects.create(
            user=self.player1,
            target_word="OCEAN",
            attempts_used=2,
            status=GameStatus.WON,
            session_date=yesterday,
        )

    def test_admin_access_control(self):
        # Non-authenticated user cannot access admin dashboard
        response = self.client.get("/admin-dashboard/daily/")
        self.assertEqual(response.status_code, 302)

        # Player cannot access admin dashboard
        self.client.login(username="PlayerAlpha", password="PlayerPassword1%")
        player_response = self.client.get("/admin-dashboard/daily/")
        self.assertEqual(player_response.status_code, 302)
        self.client.logout()

        # Admin can access admin dashboard
        self.client.login(username="AdminTester", password="AdminPassword1$")
        admin_response = self.client.get("/admin-dashboard/daily/")
        self.assertEqual(admin_response.status_code, 200)

    def test_daily_report_aggregations(self):
        self.client.login(username="AdminTester", password="AdminPassword1$")
        response = self.client.get("/admin-dashboard/daily/")
        self.assertEqual(response.status_code, 200)

        # Total sessions across all dates: 4 (3 won, 1 lost) -> 75.0%
        # Active users: 2
        summary = response.context["summary"]
        self.assertEqual(summary["active_users"], 2)
        self.assertEqual(summary["words_tried"], 4)
        self.assertEqual(summary["correct_guesses"], 3)
        self.assertEqual(summary["success_rate"], "75.0%")

        # Test Date filter for today
        today_str = date.today().strftime("%Y-%m-%d")
        today_resp = self.client.get(f"/admin-dashboard/daily/?date={today_str}")
        self.assertEqual(today_resp.status_code, 200)
        today_summary = today_resp.context["summary"]
        self.assertEqual(today_summary["active_users"], 2)
        self.assertEqual(today_summary["words_tried"], 3)
        self.assertEqual(today_summary["correct_guesses"], 2)
        self.assertEqual(today_summary["success_rate"], "66.7%")

    def test_user_performance_report_excludes_admin_and_aggregates_properly(self):
        self.client.login(username="AdminTester", password="AdminPassword1$")
        response = self.client.get("/admin-dashboard/users/")
        self.assertEqual(response.status_code, 200)

        # Dropdown must contain only players
        dropdown_players = response.context["players"]
        usernames = [p.username for p in dropdown_players]
        self.assertIn("PlayerAlpha", usernames)
        self.assertIn("PlayerBeta", usernames)
        self.assertNotIn("AdminTester", usernames)
        self.assertNotIn("AdminUser", usernames)

        # Filter by Player 1
        p1_resp = self.client.get(f"/admin-dashboard/users/?user_id={self.player1.id}")
        self.assertEqual(p1_resp.status_code, 200)
        table_data = p1_resp.context["table_data"]
        for row in table_data:
            self.assertEqual(row["username"], "PlayerAlpha")

    def test_word_pool_crud(self):
        self.client.login(username="AdminTester", password="AdminPassword1$")

        # Add valid word
        add_resp = self.client.post("/admin-dashboard/words/", {"word": "STORM"}, follow=True)
        self.assertEqual(add_resp.status_code, 200)
        word_obj = Word.objects.get(word="STORM")
        self.assertTrue(word_obj.is_active)

        # Toggle word status
        toggle_resp = self.client.post(f"/admin-dashboard/words/{word_obj.id}/toggle/", follow=True)
        self.assertEqual(toggle_resp.status_code, 200)
        word_obj.refresh_from_db()
        self.assertFalse(word_obj.is_active)

        # Delete word
        del_resp = self.client.post(f"/admin-dashboard/words/{word_obj.id}/delete/", follow=True)
        self.assertEqual(del_resp.status_code, 200)
        self.assertFalse(Word.objects.filter(word="STORM").exists())
