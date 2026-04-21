# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from home.models import Game


class GameUploadSadPathTests(TestCase):

    def setUp(self):
        # Create a test user and log them in before each test
        self.client = Client()
        self.user = User.objects.create_user(
            username='testdev',
            password='testpass123'
        )
        self.client.login(username='testdev', password='testpass123')
        self.upload_url = reverse('upload_game')

    # --- Missing required fields ---

    def test_missing_title(self):
        # Should fail - title is required
        response = self.client.post(self.upload_url, {
            'description': 'A cool game',
            'price': '9.99',
            'genre': 'RPG',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Game.objects.exists())

    def test_missing_description(self):
        # Should fail - description is required
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'price': '9.99',
            'genre': 'RPG',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Game.objects.exists())

    def test_missing_price(self):
        # Should fail - price is required
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'genre': 'RPG',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Game.objects.exists())

    def test_missing_genre(self):
        # genre is optional (blank=True) — should succeed without it
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '9.99',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Game.objects.filter(title='My Game').exists())

    # --- Wild/weird input ---

    def test_negative_price(self):
        # Should fail - price cannot be negative (validated in forms.py)
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '-99.99',
            'genre': 'RPG',
        })
        self.assertFalse(Game.objects.exists())

    def test_price_too_large(self):
        # Should fail - price exceeds allowed maximum (validated in forms.py)
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '99999999.99',
            'genre': 'RPG',
        })
        self.assertFalse(Game.objects.exists())

    def test_price_is_text(self):
        # Should fail - price must be a number
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': 'free',
            'genre': 'RPG',
        })
        self.assertFalse(Game.objects.exists())

    def test_title_too_long(self):
        # Should fail - title exceeds max_length of 200
        response = self.client.post(self.upload_url, {
            'title': 'A' * 300,
            'description': 'A cool game',
            'price': '9.99',
            'genre': 'RPG',
        })
        self.assertFalse(Game.objects.exists())

    def test_empty_strings(self):
        # Should fail - empty strings are not valid
        response = self.client.post(self.upload_url, {
            'title': '',
            'description': '',
            'price': '',
            'genre': '',
        })
        self.assertFalse(Game.objects.exists())

    def test_sql_injection_in_title(self):
        # Django's ORM safely parameterizes queries — SQL injection is not possible.
        # The game saves normally; the important thing is the DB table still exists.
        response = self.client.post(self.upload_url, {
            'title': "'; DROP TABLE home_game; --",
            'description': 'A cool game',
            'price': '9.99',
            'genre': 'RPG',
        })
        # Django's ORM safely stores the string without executing it - table still exists
        # and the data is stored as a plain string, not interpreted as SQL
        self.assertTrue(Game.objects.filter(
            title="'; DROP TABLE home_game; --"
        ).exists())

    def test_xss_in_description(self):
        # Django templates auto-escape XSS at render time, not save time.
        # The game saves to the DB normally — escaping happens when displayed.
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': '<script>alert("hacked")</script>',
            'price': '9.99',
            'genre': 'RPG',
        })
        # Django stores the raw string and auto-escapes it on render - the data is safe
        self.assertTrue(Game.objects.filter(
            description='<script>alert("hacked")</script>'
        ).exists())

    def test_unauthenticated_upload(self):
        # Should fail - user must be logged in to upload
        self.client.logout()
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '9.99',
            'genre': 'RPG',
        })
        # Should redirect to login, not save game
        self.assertFalse(Game.objects.exists())

    def test_get_request_shows_empty_form(self):
        # GET request should show the form, not crash
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)