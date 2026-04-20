from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from home.models import Game

class BrowserPlayableGameTests(TestCase):

    def setUp(self):
        # Create a test user and log them in before each test
        self.client = Client()
        self.user = User.objects.create_user(
            username='testdev',
            password='testpass123'
        )
        self.client.login(username='testdev', password='testpass123')
        self.upload_url = reverse('upload_game')

        # A minimal valid HTML file to simulate a game build upload
        self.fake_build = SimpleUploadedFile(
            'fakegame.html',
            b'<html><body>Game</body></html>',
            content_type='text/html'
        )

        # A minimal thumbnail image (1x1 pixel PNG)
        self.fake_thumbnail = SimpleUploadedFile(
            'thumb.png',
            b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
            content_type='image/png'
        )

    # --- Happy path tests ---

    def test_upload_game_with_browser_playable_checked(self):
        # Should succeed — game marked as playable in browser with a build file
        response = self.client.post(self.upload_url, {
            'title': 'Browser Game',
            'description': 'A game you can play in the browser',
            'price': '0.00',
            'genre': 'Arcade',
            'playable_in_browser': True,
            'build_file': self.fake_build,
        })
        # Should redirect to index on success
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Game.objects.filter(title='Browser Game').exists())
        game = Game.objects.get(title='Browser Game')
        self.assertTrue(game.playable_in_browser)

    def test_upload_game_without_browser_playable(self):
        # Should succeed — game not marked as playable in browser
        response = self.client.post(self.upload_url, {
            'title': 'Non-Browser Game',
            'description': 'A game you download',
            'price': '4.99',
            'genre': 'RPG',
        })
        self.assertEqual(response.status_code, 302)
        game = Game.objects.get(title='Non-Browser Game')
        self.assertFalse(game.playable_in_browser)

    def test_game_detail_page_loads(self):
        # Should return 200 for a valid game slug
        game = Game.objects.create(
            title='Test Game',
            description='A test game',
            price='9.99',
            genre='Action',
            playable_in_browser=False,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertEqual(response.status_code, 200)

    def test_game_detail_contains_title(self):
        # Game title should appear on the detail page
        game = Game.objects.create(
            title='My Awesome Game',
            description='A great game',
            price='4.99',
            genre='Puzzle',
            playable_in_browser=False,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertContains(response, 'My Awesome Game')

    def test_game_detail_shows_play_demo_when_playable(self):
        # Play Demo section should appear when game is browser playable with a build file
        build = SimpleUploadedFile(
            'game.html',
            b'<html><body>Game</body></html>',
            content_type='text/html'
        )
        game = Game.objects.create(
            title='Playable Game',
            description='Play me in the browser',
            price='0.00',
            genre='Arcade',
            playable_in_browser=True,
            build_file=build,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertContains(response, 'Play Demo in Browser')

    def test_game_detail_hides_play_demo_when_not_playable(self):
        # Play Demo section should NOT appear when game is not browser playable
        game = Game.objects.create(
            title='Download Only Game',
            description='Download me',
            price='9.99',
            genre='RPG',
            playable_in_browser=False,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertNotContains(response, 'Play Demo in Browser')

    def test_game_detail_hides_play_demo_when_no_build_file(self):
        # Play Demo section should NOT appear when playable_in_browser is True but no build file
        game = Game.objects.create(
            title='No Build Game',
            description='Marked playable but no file',
            price='0.00',
            genre='Arcade',
            playable_in_browser=True,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertNotContains(response, 'Play Demo in Browser')

    def test_game_detail_shows_browser_badge_when_playable(self):
        # Playable in Browser badge should appear on the game card
        build = SimpleUploadedFile(
            'game.html',
            b'<html><body>Game</body></html>',
            content_type='text/html'
        )
        game = Game.objects.create(
            title='Badge Game',
            description='Has a badge',
            price='0.00',
            genre='Arcade',
            playable_in_browser=True,
            build_file=build,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertContains(response, 'Playable in Browser')

    # --- Sad path tests ---

    def test_game_detail_404_for_invalid_slug(self):
        # Should return 404 for a slug that doesn't exist
        response = self.client.get(reverse('game_detail', args=['nonexistent-game']))
        self.assertEqual(response.status_code, 404)

    def test_upload_playable_game_without_build_file(self):
        # Should still succeed — build_file is optional
        response = self.client.post(self.upload_url, {
            'title': 'No Build Game',
            'description': 'Playable but no file yet',
            'price': '0.00',
            'genre': 'Arcade',
            'playable_in_browser': True,
        })
        # Game saves successfully, build_file just stays blank
        self.assertEqual(response.status_code, 302)
        game = Game.objects.get(title='No Build Game')
        self.assertTrue(game.playable_in_browser)
        self.assertFalse(game.build_file)

    def test_unauthenticated_user_cannot_upload(self):
        # Should redirect unauthenticated users away from upload
        self.client.logout()
        response = self.client.post(self.upload_url, {
            'title': 'Sneaky Game',
            'description': 'Trying to upload without login',
            'price': '0.00',
            'genre': 'Stealth',
            'playable_in_browser': True,
        })
        self.assertFalse(Game.objects.exists())

    def test_game_detail_passes_game_object_to_template(self):
        # Template should receive the full game object, not individual fields
        game = Game.objects.create(
            title='Context Game',
            description='Check the context',
            price='1.99',
            genre='Puzzle',
            playable_in_browser=False,
            uploaded_by=self.user,
            developer=self.user.username,
        )
        response = self.client.get(reverse('game_detail', args=[game.slug]))
        self.assertIn('game', response.context)
        self.assertEqual(response.context['game'], game)