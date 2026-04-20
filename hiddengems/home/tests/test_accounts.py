# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class SignupTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')

    # --- Happy path ---

    def test_signup_page_loads(self):
        # Signup page should load for unauthenticated users
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user(self):
        # Valid signup should create a new user
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_logs_user_in(self):
        # After signup, user should be logged in and redirected to index
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('index'))

    def test_authenticated_user_redirected_from_signup(self):
        # Logged in users should be redirected away from signup page
        User.objects.create_user(username='existing', password='testpass123')
        self.client.login(username='existing', password='testpass123')
        response = self.client.get(self.signup_url)
        self.assertRedirects(response, reverse('index'))

    # --- Sad path ---

    def test_signup_passwords_dont_match(self):
        # Mismatched passwords should fail
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': 'StrongPass123!',
            'password2': 'WrongPass123!',
        })
        self.assertFalse(User.objects.filter(username='newuser').exists())
        self.assertEqual(response.status_code, 200)

    def test_signup_missing_username(self):
        # Missing username should fail
        response = self.client.post(self.signup_url, {
            'username': '',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertFalse(User.objects.filter(username='').exists())

    def test_signup_duplicate_username(self):
        # Duplicate username should fail
        User.objects.create_user(username='existing', password='testpass123')
        response = self.client.post(self.signup_url, {
            'username': 'existing',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_signup_weak_password(self):
        # Password too simple should fail Django's validators
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'password1': '123',
            'password2': '123',
        })
        self.assertFalse(User.objects.filter(username='newuser').exists())


class LoginTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    # --- Happy path ---

    def test_login_page_loads(self):
        # Login page should load for unauthenticated users
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials(self):
        # Valid credentials should log user in and redirect to index
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('index'))

    def test_authenticated_user_redirected_from_login(self):
        # Logged in users should be redirected away from login page
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.login_url)
        self.assertRedirects(response, reverse('index'))

    def test_login_redirects_to_next(self):
        # Login should redirect to ?next= param if provided
        response = self.client.post(
            f"{self.login_url}?next={reverse('browse')}",
            {'username': 'testuser', 'password': 'testpass123'}
        )
        self.assertRedirects(response, reverse('browse'))

    # --- Sad path ---

    def test_login_wrong_password(self):
        # Wrong password should fail
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_nonexistent_user(self):
        # Nonexistent user should fail
        response = self.client.post(self.login_url, {
            'username': 'nobody',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_empty_fields(self):
        # Empty fields should fail
        response = self.client.post(self.login_url, {
            'username': '',
            'password': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class LogoutTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_logout_redirects_to_index(self):
        # Logout should redirect to homepage
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('index'))

    def test_logout_logs_user_out(self):
        # After logout, user should no longer be authenticated
        self.client.login(username='testuser', password='testpass123')
        self.client.get(self.logout_url)
        response = self.client.get(reverse('index'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)