# Create your tests here.
import home.utils as util
from django.test import TestCase
from django.core.cache import cache
from home.models import Game, SimilarGame


class GameFactory:
    """Helper to create Game instances with sensible defaults."""
    @staticmethod
    def create(**kwargs):
        defaults = {
            "title": "Default Game",
            "description": "A default description.",
            "genre": "Strategy",
            "publisher": "Default Publisher",
            "developer": "Default Developer",
            "price": 10.00,
            "slug": "default-game",
        }
        defaults.update(kwargs)
        return Game.objects.create(**defaults)


class GameToTextTestCase(TestCase):
    def setUp(self):
        self.game = GameFactory.create(
            title="Factorio",
            description="Build and manage automated factories.",
            genre="Strategy",
            publisher="Wube Software LTD.",
            developer="Wube Software LTD.",
            slug="factorio",
        )

    def test_includes_title(self):
        self.assertIn("Factorio", util.game_to_text(self.game))

    def test_includes_genre(self):
        self.assertIn("Strategy", util.game_to_text(self.game))

    def test_includes_description(self):
        self.assertIn("factories", util.game_to_text(self.game))


class TitleSimilarityBoostTestCase(TestCase):
    def test_exact_match(self):
        self.assertEqual(util.title_similarity_boost("Factorio", "Factorio"), 1.3)

    def test_subset_title(self):
        boost = util.title_similarity_boost("Factorio", "Factorio: Space Age")
        self.assertGreater(boost, 0)

    def test_no_match(self):
        self.assertEqual(util.title_similarity_boost("Factorio", "Dragon Quest"), 0.0)

    def test_strips_punctuation(self):
        boost = util.title_similarity_boost("Half-Life", "Half-Life: Source")
        self.assertGreater(boost, 0)


class PublisherDeveloperBoostTestCase(TestCase):
    def setUp(self):
        self.base_game = GameFactory.create(
            title="Factorio",
            publisher="Wube Software LTD.",
            developer="Wube Software LTD.",
            slug="factorio",
        )
        self.similar_game = GameFactory.create(
            title="Factorio: Space Age",
            publisher="Wube Software LTD.",
            developer="Wube Software LTD.",
            slug="factorio-space-age",
        )
        self.unrelated_game = GameFactory.create(
            title="Unrelated RPG",
            publisher="Other Studio",
            developer="Other Studio",
            slug="unrelated-rpg",
        )

    def test_both_match(self):
        self.assertEqual(util.publisher_developer_boost(self.base_game, self.similar_game), 0.4)

    def test_publisher_only(self):
        self.unrelated_game.publisher = "Wube Software LTD."
        self.assertEqual(util.publisher_developer_boost(self.base_game, self.unrelated_game), 0.2)

    def test_no_match(self):
        self.assertEqual(util.publisher_developer_boost(self.base_game, self.unrelated_game), 0.0)


class DeduplicateByTitleTestCase(TestCase):
    def setUp(self):
        self.base_game = GameFactory.create(
            title="Factorio",
            slug="factorio",
        )
        self.similar_game = GameFactory.create(
            title="Factorio: Space Age",
            slug="factorio-space-age",
        )

    def test_removes_duplicates(self):
        scored = [(self.base_game, 0.9), (self.base_game, 0.5), (self.similar_game, 0.7)]
        result = util.deduplicate_by_title(scored)
        self.assertEqual(len(result), 2)

    def test_keeps_first_occurrence(self):
        scored = [(self.base_game, 0.9), (self.base_game, 0.5)]
        result = util.deduplicate_by_title(scored)
        self.assertEqual(result[0][1], 0.9)


class GetSimilarGamesTestCase(TestCase):
    def setUp(self):
        self.base_game = GameFactory.create(
            title="Factorio",
            description="Build and manage automated factories.",
            genre="Strategy",
            publisher="Wube Software LTD.",
            developer="Wube Software LTD.",
            slug="factorio",
        )
        self.similar_game = GameFactory.create(
            title="Factorio: Space Age",
            description="Continue your journey after launching rockets into space.",
            genre="Strategy",
            publisher="Wube Software LTD.",
            developer="Wube Software LTD.",
            price=35.00,
            slug="factorio-space-age",
        )

    def tearDown(self):
        cache.clear()

    def test_returns_list(self):
        result = util.get_similar_games(self.base_game)
        self.assertIsInstance(result, list)

    def test_excludes_self(self):
        result = util.get_similar_games(self.base_game)
        self.assertNotIn(self.base_game, result)

    def test_caches_result(self):
        util.get_similar_games(self.base_game)
        cached = cache.get(f"similar_games_{self.base_game.pk}")
        self.assertIsNotNone(cached)

    def test_stores_in_db(self):
        util.get_similar_games(self.base_game)
        self.assertTrue(SimilarGame.objects.filter(game=self.base_game).exists())

    def test_empty_db(self):
        # Only base_game exists — no other games to be similar to
        self.similar_game.delete()
        result = util.get_similar_games(self.base_game)
        self.assertEqual(result, [])

