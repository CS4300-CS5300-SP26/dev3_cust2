from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from home.models import Game, Rating


class RatingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.game = Game.objects.create(
            title="Rating Test Game",
            description="A game to test ratings",
            price="4.99",
            genre="Puzzle",
            developer="Dev Two",
        )
        self.rate_url = reverse("rate_game", args=[self.game.id])

    # --- Happy path tests ---

    def test_user_can_rate_game(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.rate_url, {"score": 4})

        self.assertEqual(response.status_code, 200)
        rating = Rating.objects.get(user=self.user, game=self.game)
        self.assertEqual(rating.score, 4)

    def test_user_can_update_rating(self):
        self.client.login(username="testuser", password="testpass123")
        self.client.post(self.rate_url, {"score": 3})
        self.client.post(self.rate_url, {"score": 5})

        rating = Rating.objects.get(user=self.user, game=self.game)
        self.assertEqual(rating.score, 5)

    def test_rating_returns_average(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.rate_url, {"score": 5})

        self.assertIn("average", response.json())

    # --- Sad path tests ---

    def test_rating_requires_login(self):
        response = self.client.post(self.rate_url, {"score": 4})
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_rating_invalid_game_id(self):
        self.client.login(username="testuser", password="testpass123")
        bad_url = reverse("rate_game", args=[99999])
        response = self.client.post(bad_url, {"score": 4})
        self.assertEqual(response.status_code, 404)

    def test_rating_rejects_invalid_score(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.rate_url, {"score": 99})

        # Should not create a rating
        self.assertFalse(Rating.objects.filter(user=self.user, game=self.game).exists())
