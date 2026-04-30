import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, Client
from django.urls import reverse

from home.models import Game
from home.views import _ai_parse_query


def make_ai_response(keywords=None, vibe_keywords=None, genre=None, free_only=False, max_price=None):
    """Helper that builds the dict _ai_parse_query returns."""
    return {
        "keywords": keywords or [],
        "vibe_keywords": vibe_keywords or [],
        "genre": genre,
        "free_only": free_only,
        "max_price": max_price,
    }


# ---------------------------------------------------------------------------
# Unit tests for _ai_parse_query
# ---------------------------------------------------------------------------

class AiParseQueryTests(TestCase):

    def _mock_response(self, text):
        """Build a mock OpenAI response object whose .output_text is *text*."""
        mock_resp = MagicMock()
        mock_resp.output_text = text
        return mock_resp

    @patch("home.views.OpenAI")
    def test_returns_parsed_json(self, mock_openai_cls):
        payload = '{"keywords": ["horror"], "vibe_keywords": ["dark"], "genre": "Horror", "free_only": false, "max_price": null}'
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("scary horror game")

        self.assertEqual(result["genre"], "Horror")
        self.assertIn("horror", result["keywords"])
        self.assertFalse(result["free_only"])
        self.assertIsNone(result["max_price"])

    @patch("home.views.OpenAI")
    def test_strips_markdown_code_fences(self, mock_openai_cls):
        payload = "```json\n{\"keywords\": [\"puzzle\"], \"vibe_keywords\": [], \"genre\": \"Puzzle\", \"free_only\": false, \"max_price\": null}\n```"
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("puzzle game")

        self.assertEqual(result["genre"], "Puzzle")
        self.assertIn("puzzle", result["keywords"])

    @patch("home.views.OpenAI")
    def test_strips_bare_code_fences_without_language_tag(self, mock_openai_cls):
        payload = "```\n{\"keywords\": [\"rpg\"], \"vibe_keywords\": [], \"genre\": \"RPG\", \"free_only\": false, \"max_price\": null}\n```"
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("rpg game")

        self.assertEqual(result["genre"], "RPG")

    @patch("home.views.OpenAI")
    def test_free_only_flag(self, mock_openai_cls):
        payload = '{"keywords": [], "vibe_keywords": [], "genre": null, "free_only": true, "max_price": null}'
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("free games")

        self.assertTrue(result["free_only"])

    @patch("home.views.OpenAI")
    def test_max_price_parsed(self, mock_openai_cls):
        payload = '{"keywords": [], "vibe_keywords": [], "genre": null, "free_only": false, "max_price": 5}'
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("games under $5")

        self.assertEqual(result["max_price"], 5)
        self.assertFalse(result["free_only"])

    @patch("home.views.OpenAI")
    def test_vibe_keywords_returned(self, mock_openai_cls):
        payload = '{"keywords": [], "vibe_keywords": ["relaxing", "peaceful", "cozy"], "genre": null, "free_only": false, "max_price": null}'
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response(payload)

        result = _ai_parse_query("something relaxing")

        self.assertIn("relaxing", result["vibe_keywords"])
        self.assertIn("cozy", result["vibe_keywords"])

    @patch("home.views.OpenAI")
    def test_raises_on_invalid_json(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = self._mock_response("not valid json at all")

        with self.assertRaises(Exception):
            _ai_parse_query("some query")

    @patch("home.views.OpenAI")
    def test_raises_on_api_error(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.side_effect = RuntimeError("API unavailable")

        with self.assertRaises(RuntimeError):
            _ai_parse_query("any query")


# ---------------------------------------------------------------------------
# Integration tests for the browse view with AI search
# ---------------------------------------------------------------------------

class BrowseAiSearchTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.browse_url = reverse("browse")

        self.horror_game = Game.objects.create(
            title="Shadow Depths",
            description="A terrifying horror adventure",
            genre="Horror",
            price="9.99",
            developer="Scary Dev",
        )
        self.rpg_game = Game.objects.create(
            title="Epic Quest",
            description="An epic role-playing adventure",
            genre="RPG",
            price="14.99",
            developer="RPG Studio",
        )
        self.free_game = Game.objects.create(
            title="Free Runner",
            description="A free platformer game",
            genre="Platformer",
            price="0.00",
            developer="Indie Dev",
        )
        self.cheap_game = Game.objects.create(
            title="Budget Blast",
            description="An affordable strategy game",
            genre="Strategy",
            price="2.99",
            developer="Small Studio",
        )

    def _patch_ai(self, return_value):
        """Patch _ai_parse_query and return the patcher (must be used as context manager)."""
        return patch("home.views._ai_parse_query", return_value=return_value)

    # --- Keyword filtering ---

    def test_keyword_filter_matches_title(self):
        ai_result = make_ai_response(keywords=["shadow"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "shadow"})

        games = list(response.context["games"])
        titles = [g.title for g in games]
        self.assertIn("Shadow Depths", titles)
        self.assertNotIn("Epic Quest", titles)

    def test_keyword_filter_matches_description(self):
        ai_result = make_ai_response(keywords=["terrifying"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "terrifying"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Shadow Depths", titles)

    def test_vibe_keyword_filter_matches_description(self):
        ai_result = make_ai_response(vibe_keywords=["epic"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "epic vibe"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Epic Quest", titles)

    def test_keywords_are_case_insensitive(self):
        ai_result = make_ai_response(keywords=["HORROR"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "HORROR"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Shadow Depths", titles)

    # --- Genre filtering ---

    def test_genre_filter_returns_matching_games(self):
        ai_result = make_ai_response(genre="RPG")
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "rpg"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Epic Quest", titles)
        self.assertNotIn("Shadow Depths", titles)

    def test_genre_and_keywords_combined_with_or(self):
        # keyword matches horror game; genre matches rpg — both should appear
        ai_result = make_ai_response(keywords=["terrifying"], genre="RPG")
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "terrifying rpg"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Shadow Depths", titles)
        self.assertIn("Epic Quest", titles)

    # --- Price filtering ---

    def test_free_only_filter_returns_only_free_games(self):
        ai_result = make_ai_response(free_only=True)
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "free games"})

        games = list(response.context["games"])
        for game in games:
            self.assertLessEqual(float(game.price), 0)
        titles = [g.title for g in games]
        self.assertIn("Free Runner", titles)
        self.assertNotIn("Epic Quest", titles)

    def test_max_price_filter_excludes_expensive_games(self):
        ai_result = make_ai_response(max_price=5)
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "games under $5"})

        games = list(response.context["games"])
        for game in games:
            self.assertLessEqual(float(game.price), 5)
        titles = [g.title for g in games]
        self.assertIn("Free Runner", titles)
        self.assertIn("Budget Blast", titles)
        self.assertNotIn("Epic Quest", titles)

    def test_free_only_takes_precedence_over_max_price(self):
        # When free_only is true, only $0 games returned regardless of max_price
        ai_result = make_ai_response(free_only=True, max_price=10)
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "free"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Free Runner", titles)
        self.assertNotIn("Budget Blast", titles)

    # --- No filters / empty results ---

    def test_no_filters_returns_all_games(self):
        # AI returns empty filters → all games returned (price filter already applied: none)
        ai_result = make_ai_response()
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "anything"})

        self.assertEqual(len(response.context["games"]), 4)

    def test_query_with_no_matching_games_returns_empty(self):
        ai_result = make_ai_response(keywords=["xyznonexistent"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "xyznonexistent"})

        self.assertEqual(len(response.context["games"]), 0)

    # --- Fallback to plain-text search on AI failure ---

    def test_fallback_search_on_ai_exception(self):
        with patch("home.views._ai_parse_query", side_effect=RuntimeError("AI down")):
            response = self.client.get(self.browse_url, {"q": "Horror"})

        self.assertEqual(response.status_code, 200)
        titles = [g.title for g in response.context["games"]]
        self.assertIn("Shadow Depths", titles)

    def test_fallback_search_does_not_return_unrelated_games(self):
        with patch("home.views._ai_parse_query", side_effect=RuntimeError("AI down")):
            response = self.client.get(self.browse_url, {"q": "Horror"})

        titles = [g.title for g in response.context["games"]]
        self.assertNotIn("Epic Quest", titles)

    def test_fallback_search_matches_developer_field(self):
        with patch("home.views._ai_parse_query", side_effect=RuntimeError("AI down")):
            response = self.client.get(self.browse_url, {"q": "Scary Dev"})

        titles = [g.title for g in response.context["games"]]
        self.assertIn("Shadow Depths", titles)

    # --- Context and response ---

    def test_query_is_passed_to_template_context(self):
        ai_result = make_ai_response(keywords=["horror"])
        with self._patch_ai(ai_result):
            response = self.client.get(self.browse_url, {"q": "horror"})

        self.assertEqual(response.context["query"], "horror")

    def test_no_query_returns_all_games_without_ai_call(self):
        with patch("home.views._ai_parse_query") as mock_ai:
            response = self.client.get(self.browse_url)

        mock_ai.assert_not_called()
        self.assertEqual(len(response.context["games"]), 4)

    def test_whitespace_only_query_treated_as_no_query(self):
        with patch("home.views._ai_parse_query") as mock_ai:
            response = self.client.get(self.browse_url, {"q": "   "})

        mock_ai.assert_not_called()
        self.assertEqual(len(response.context["games"]), 4)
