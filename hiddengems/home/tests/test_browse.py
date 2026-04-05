from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Game


class BrowsePageTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.browse_url = reverse('browse')
        self.user = User.objects.create_user(
            username='testdev',
            password='testpassword'
        )

    def _create_game(self, title='Test Game', price='9.99', genre='Indie', description='A test game.'):
        return Game.objects.create(
            title=title,
            description=description,
            developer=self.user,
            price=price,
            genre=genre,
        )

    '''Browse page access'''

    def test_browse_accessible_without_login(self):
        # Browse page should be publicly accessible
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)

    def test_browse_accessible_when_logged_in(self):
        self.client.login(username='testdev', password='testpassword')
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)

    '''No games in database'''

    def test_browse_empty_state_when_no_games(self):
        response = self.client.get(self.browse_url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['games'], [])
        self.assertContains(response, 'No games have been submitted yet.')

    '''Game information displayed'''

    def test_browse_shows_single_game(self):
        game = self._create_game(title='Cool Platformer')
        response = self.client.get(self.browse_url)
        self.assertContains(response, 'Cool Platformer')
        self.assertIn(game, response.context['games'])

    def test_browse_shows_multiple_games(self):
        self._create_game(title='Game One')
        self._create_game(title='Game Two')
        self._create_game(title='Game Three')
        response = self.client.get(self.browse_url)
        self.assertEqual(response.context['games'].count(), 3)

    def test_browse_displays_game_genre(self):
        self._create_game(title='Pixels', genre='RPG')
        response = self.client.get(self.browse_url)
        self.assertContains(response, 'RPG')

    def test_browse_displays_game_price(self):
        self._create_game(title='Hollow Knight', price='14.99')
        response = self.client.get(self.browse_url)
        self.assertContains(response, '14.99')

    def test_browse_displays_free_label_for_zero_price(self):
        self._create_game(title='This Game is Free', price='0.00')
        response = self.client.get(self.browse_url)
        self.assertContains(response, 'Free')

    '''Game Context'''

    def test_browse_passes_games_context(self):
        self._create_game()
        response = self.client.get(self.browse_url)
        self.assertIn('games', response.context)

    '''Search bar'''

    def test_browse_contains_search_bar(self):
        response = self.client.get(self.browse_url)
        self.assertContains(response, '<input')
        self.assertContains(response, 'name="q"')

    '''Link to game page'''

    def test_browse_links_to_game_detail(self):
        game = self._create_game(title='Linked Game')
        response = self.client.get(self.browse_url)
        detail_url = reverse('game_detail', args=[game.slug])
        self.assertContains(response, detail_url)