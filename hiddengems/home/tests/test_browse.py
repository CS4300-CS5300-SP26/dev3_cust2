from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Game
 
 
class BrowsePageTests(TestCase):
 
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.browse_url = reverse('browse')
 
        # Create some test games
        self.game1 = Game.objects.create(
            title='Test Game One',
            description='A great game',
            price='9.99',
            genre='RPG',
            developer='Dev One',
        )
        self.game2 = Game.objects.create(
            title='Test Game Two',
            description='Another great game',
            price='14.99',
            genre='Platformer',
            developer='Dev Two',
        )
 
    # --- Happy path tests ---
 
    def test_browse_page_loads(self):
        # Browse page should be accessible without login
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)
 
    def test_browse_page_loads_when_authenticated(self):
        # Browse page should also work when logged in
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)
 
    def test_browse_shows_all_games(self):
        # Both games should appear on the browse page
        response = self.client.get(self.browse_url)
        self.assertContains(response, 'Test Game One')
        self.assertContains(response, 'Test Game Two')
 
    def test_browse_shows_no_games_when_empty(self):
        # If no games exist, page should still load without error
        Game.objects.all().delete()
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)
 
    def test_browse_games_ordered_by_newest(self):
        # Most recently created game should appear first
        response = self.client.get(self.browse_url)
        games = list(response.context['games'])
        self.assertEqual(games[0].title, 'Test Game Two')
        self.assertEqual(games[1].title, 'Test Game One')
 
    def test_browse_context_contains_games(self):
        # Context should contain a 'games' key
        response = self.client.get(self.browse_url)
        self.assertIn('games', response.context)
        self.assertEqual(len(response.context['games']), 2)
 
    # --- Sad path tests ---
 
    def test_browse_post_request_not_allowed(self):
        # Browse page should not accept POST requests
        response = self.client.post(self.browse_url, {})
        self.assertNotEqual(response.status_code, 200)
 
    def test_browse_game_with_missing_optional_fields(self):
        # Game with only required fields should still appear on browse page
        Game.objects.create(
            title='Minimal Game',
            description='Bare minimum',
            price='0.00',
        )
        response = self.client.get(self.browse_url)
        self.assertContains(response, 'Minimal Game')