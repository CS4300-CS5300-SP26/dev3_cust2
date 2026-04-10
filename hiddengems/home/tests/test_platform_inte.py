# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Game


class BrowserPlayableTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testdev',
            password='testpass123'
        )
        self.browser_game = Game.objects.create(
            title='Browser Game',
            description='Play me in your browser!',
            price='0.00',
            genre='Puzzle',
            developer='Web Dev',
            playable_in_browser=True,
        )
        self.non_browser_game = Game.objects.create(
            title='Download Only Game',
            description='You must download me.',
            price='9.99',
            genre='RPG',
            developer='Desktop Dev',
            playable_in_browser=False,
        )

    # --- Happy path ---

    def test_browser_game_flag_is_true(self):
        # playable_in_browser should be True for browser games
        self.assertTrue(self.browser_game.playable_in_browser)

    def test_non_browser_game_flag_is_false(self):
        # playable_in_browser should be False for non-browser games
        self.assertFalse(self.non_browser_game.playable_in_browser)

    def test_browser_game_appears_on_browse_page(self):
        # Browser games should appear on the browse page
        response = self.client.get(reverse('browse'))
        self.assertContains(response, 'Browser Game')

    def test_non_browser_game_appears_on_browse_page(self):
        # Non-browser games should also appear on the browse page
        response = self.client.get(reverse('browse'))
        self.assertContains(response, 'Download Only Game')

    def test_browser_game_detail_page_loads(self):
        # Browser game detail page should load correctly
        response = self.client.get(reverse('game_detail', args=[self.browser_game.slug]))
        self.assertEqual(response.status_code, 200)

    def test_upload_game_as_browser_playable(self):
        # Developer should be able to upload a browser-playable game
        self.client.login(username='testdev', password='testpass123')
        response = self.client.post(reverse('upload_game'), {
            'title': 'My Web Game',
            'description': 'Runs in the browser',
            'price': '0.00',
            'genre': 'Arcade',
            'playable_in_browser': True,
        })
        self.assertTrue(Game.objects.filter(title='My Web Game', playable_in_browser=True).exists())

    def test_upload_game_as_non_browser_playable(self):
        # Developer should be able to upload a non-browser game
        self.client.login(username='testdev', password='testpass123')
        response = self.client.post(reverse('upload_game'), {
            'title': 'My Desktop Game',
            'description': 'Download required',
            'price': '14.99',
            'genre': 'Strategy',
            'playable_in_browser': False,
        })
        self.assertTrue(Game.objects.filter(title='My Desktop Game', playable_in_browser=False).exists())

    # --- Sad path ---

    def test_browser_playable_defaults_to_false(self):
        # If not specified, playable_in_browser should default to False
        game = Game.objects.create(
            title='Default Game',
            description='No browser flag set',
            price='4.99',
        )
        self.assertFalse(game.playable_in_browser)

    def test_unauthenticated_user_cannot_upload_browser_game(self):
        # Unauthenticated users should not be able to upload any game
        response = self.client.post(reverse('upload_game'), {
            'title': 'Sneaky Game',
            'description': 'Should not be saved',
            'price': '0.00',
            'genre': 'Arcade',
            'playable_in_browser': True,
        })
        self.assertFalse(Game.objects.filter(title='Sneaky Game').exists())