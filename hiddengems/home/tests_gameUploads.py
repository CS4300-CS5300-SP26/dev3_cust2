
# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Game


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
        # Should fail - genre is required
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '9.99',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Game.objects.exists())

    # --- Wild/weird input ---

    def test_negative_price(self):
        # Should fail - price cannot be negative
        response = self.client.post(self.upload_url, {
            'title': 'My Game',
            'description': 'A cool game',
            'price': '-99.99',
            'genre': 'RPG',
        })
        self.assertFalse(Game.objects.exists())

    def test_price_too_large(self):
        # Should fail - price exceeds max_digits in model
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
        # Should be safely handled by Django's ORM
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
        # Should be safely escaped by Django templates
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
