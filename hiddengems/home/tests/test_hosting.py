# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from home.models import Game


class GameModelSadPathTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testdev',
            password='testpass123'
        )

    # --- Slug edge cases ---

    def test_slug_not_generated_from_empty_title(self):
        # A game with a blank-ish title should still get a fallback slug
        game = Game.objects.create(
            title='   ',
            description='No real title',
            price='9.99',
        )
        self.assertNotEqual(game.slug, '')

    def test_duplicate_slug_gets_incremented(self):
        # Two games with same title should not share a slug
        game1 = Game.objects.create(title='Same Title', description='First', price='9.99')
        game2 = Game.objects.create(title='Same Title', description='Second', price='9.99')
        game3 = Game.objects.create(title='Same Title', description='Third', price='9.99')
        slugs = {game1.slug, game2.slug, game3.slug}
        self.assertEqual(len(slugs), 3)

    # --- Field edge cases ---

    def test_game_str_returns_title(self):
        # __str__ should return the game title
        game = Game.objects.create(title='My Game', description='desc', price='9.99')
        self.assertEqual(str(game), 'My Game')

    def test_developer_field_can_be_blank(self):
        # Developer field is optional
        game = Game.objects.create(title='No Dev Game', description='desc', price='9.99')
        self.assertEqual(game.developer, '')

    def test_publisher_field_can_be_blank(self):
        # Publisher field is optional
        game = Game.objects.create(title='No Publisher Game', description='desc', price='9.99')
        self.assertEqual(game.publisher, '')

    def test_other_platforms_can_be_blank(self):
        # other_platforms field is optional
        game = Game.objects.create(title='Solo Platform Game', description='desc', price='9.99')
        self.assertEqual(game.other_platforms, '')

    def test_game_id_can_be_null(self):
        # game_id is optional and can be null
        game = Game.objects.create(title='No ID Game', description='desc', price='9.99')
        self.assertIsNone(game.game_id)

    def test_storefront_defaults_to_steam(self):
        # storefront should default to 'steam'
        game = Game.objects.create(title='Default Store Game', description='desc', price='9.99')
        self.assertEqual(game.storefront, 'steam')

    # --- Relationship edge cases ---

    def test_uploaded_by_can_be_null(self):
        # uploaded_by is optional
        game = Game.objects.create(title='Orphan Game', description='desc', price='9.99')
        self.assertIsNone(game.uploaded_by)

    def test_authorized_users_can_be_empty(self):
        # A game with no authorized users should still be valid
        game = Game.objects.create(title='Restricted Game', description='desc', price='9.99')
        self.assertEqual(game.authorized_users.count(), 0)

    def test_authorized_users_can_have_multiple(self):
        # Multiple users can be authorized for the same game
        user2 = User.objects.create_user(username='otherdev', password='testpass123')
        game = Game.objects.create(title='Collab Game', description='desc', price='9.99')
        game.authorized_users.add(self.user, user2)
        self.assertEqual(game.authorized_users.count(), 2)

    def test_deleting_user_deletes_their_uploaded_games(self):
        # Deleting a user should cascade delete their uploaded games
        game = Game.objects.create(
            title='User Game',
            description='desc',
            price='9.99',
            uploaded_by=self.user
        )
        self.user.delete()
        self.assertFalse(Game.objects.filter(title='User Game').exists())

    # --- Upload view edge cases ---

    def test_upload_redirects_unauthenticated_to_index(self):
        # Unauthenticated users should be redirected to index, not login
        response = self.client.post(reverse('upload_game'), {
            'title': 'Sneaky Game',
            'description': 'Should not save',
            'price': '9.99',
            'genre': 'RPG',
        })
        self.assertRedirects(response, reverse('index'))

    def test_upload_get_request_shows_form(self):
        # GET request to upload page should show the form, not crash
        self.client.login(username='testdev', password='testpass123')
        response = self.client.get(reverse('upload_game'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_upload_does_not_save_on_invalid_post(self):
        # Invalid POST should not save anything to the database
        self.client.login(username='testdev', password='testpass123')
        self.client.post(reverse('upload_game'), {
            'title': '',
            'description': '',
            'price': 'not-a-number',
            'genre': '',
        })
        self.assertFalse(Game.objects.exists())