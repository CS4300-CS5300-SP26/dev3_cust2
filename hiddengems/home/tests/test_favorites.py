from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from home.models import Game


class FavoriteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.game = Game.objects.create(
            title="Fav Test Game",
            description="A game to test favorites",
            price="9.99",
            genre="RPG",
            developer="Dev One",
        )
        self.toggle_url = reverse("toggle_favorite", args=[self.game.id])

    # --- Happy path tests ---

    def test_user_can_favorite_game(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.toggle_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.game, self.user.profile.favorites.all())

    def test_user_can_unfavorite_game(self):
        self.client.login(username="testuser", password="testpass123")
        # First favorite it
        self.client.post(self.toggle_url)
        # Then unfavorite it
        response = self.client.post(self.toggle_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.game, self.user.profile.favorites.all())

    def test_favorite_endpoint_returns_json(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(self.toggle_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())

    # --- Sad path tests ---

    def test_favorite_requires_login(self):
        response = self.client.post(self.toggle_url)
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_favorite_invalid_game_id(self):
        self.client.login(username="testuser", password="testpass123")
        bad_url = reverse("toggle_favorite", args=[99999])
        response = self.client.post(bad_url)
        self.assertEqual(response.status_code, 404)
