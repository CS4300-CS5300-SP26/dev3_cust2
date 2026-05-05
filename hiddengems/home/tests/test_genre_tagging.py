import json
from io import StringIO
from unittest.mock import MagicMock, call, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from home.models import CANONICAL_GENRES, Game, GenreTag
from home.views import _ai_tag_game


def _make_game(**kwargs):
    defaults = dict(
        title="Test Game",
        description="A test game.",
        genre="",
        price="0.00",
        developer="Dev",
    )
    defaults.update(kwargs)
    return Game.objects.create(**defaults)


def _mock_openai_response(text):
    mock_resp = MagicMock()
    mock_resp.output_text = text
    return mock_resp


# ---------------------------------------------------------------------------
# Unit tests for _ai_tag_game
# ---------------------------------------------------------------------------


class AiTagGameTests(TestCase):

    @patch("home.views.OpenAI")
    def test_assigns_canonical_tags_to_game(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Action", "RPG"]')
        )
        game = _make_game(title="Hero Quest")

        _ai_tag_game(game)

        tag_names = list(game.genre_tags.values_list("name", flat=True))
        self.assertIn("Action", tag_names)
        self.assertIn("RPG", tag_names)

    @patch("home.views.OpenAI")
    def test_creates_genre_tag_objects(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Puzzle"]')
        )
        game = _make_game()

        _ai_tag_game(game)

        self.assertTrue(GenreTag.objects.filter(name="Puzzle").exists())

    @patch("home.views.OpenAI")
    def test_does_not_duplicate_existing_genre_tags(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Horror"]')
        )
        GenreTag.objects.create(name="Horror", slug="horror")
        game = _make_game()

        _ai_tag_game(game)

        self.assertEqual(GenreTag.objects.filter(name="Horror").count(), 1)

    @patch("home.views.OpenAI")
    def test_strips_non_canonical_genres(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Action", "NotAGenre", "FakeTag"]')
        )
        game = _make_game()

        _ai_tag_game(game)

        tag_names = list(game.genre_tags.values_list("name", flat=True))
        self.assertIn("Action", tag_names)
        self.assertNotIn("NotAGenre", tag_names)
        self.assertNotIn("FakeTag", tag_names)

    @patch("home.views.OpenAI")
    def test_all_non_canonical_results_in_no_tags(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Fake1", "Fake2"]')
        )
        game = _make_game()

        _ai_tag_game(game)

        self.assertEqual(game.genre_tags.count(), 0)

    @patch("home.views.OpenAI")
    def test_strips_markdown_code_fences(self, mock_openai_cls):
        payload = '```json\n["Strategy", "Simulation"]\n```'
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response(payload)
        )
        game = _make_game()

        _ai_tag_game(game)

        tag_names = list(game.genre_tags.values_list("name", flat=True))
        self.assertIn("Strategy", tag_names)
        self.assertIn("Simulation", tag_names)

    @patch("home.views.OpenAI")
    def test_strips_bare_code_fences(self, mock_openai_cls):
        payload = '```\n["Platformer"]\n```'
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response(payload)
        )
        game = _make_game()

        _ai_tag_game(game)

        tag_names = list(game.genre_tags.values_list("name", flat=True))
        self.assertIn("Platformer", tag_names)

    @patch("home.views.OpenAI")
    def test_invalidates_cache_for_each_tag(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Action", "RPG"]')
        )
        cache.set("genre_games_action", "stale")
        cache.set("genre_games_rpg", "stale")
        game = _make_game()

        _ai_tag_game(game)

        self.assertIsNone(cache.get("genre_games_action"))
        self.assertIsNone(cache.get("genre_games_rpg"))

    @patch("home.views.OpenAI")
    def test_raises_on_invalid_json(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response("not json")
        )
        game = _make_game()

        with self.assertRaises(Exception):
            _ai_tag_game(game)

    @patch("home.views.OpenAI")
    def test_raises_on_api_error(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.side_effect = RuntimeError(
            "API unavailable"
        )
        game = _make_game()

        with self.assertRaises(RuntimeError):
            _ai_tag_game(game)

    @patch("home.views.OpenAI")
    def test_truncates_description_to_600_chars(self, mock_openai_cls):
        mock_openai_cls.return_value.responses.create.return_value = (
            _mock_openai_response('["Action"]')
        )
        long_description = "x" * 1000
        game = _make_game(description=long_description)

        _ai_tag_game(game)

        _, kwargs = mock_openai_cls.return_value.responses.create.call_args
        user_content = kwargs["input"][1]["content"]
        self.assertIn("x" * 600, user_content)
        self.assertNotIn("x" * 601, user_content)


# ---------------------------------------------------------------------------
# Integration: upload_game view auto-tags and swallows errors
# ---------------------------------------------------------------------------


class UploadGameGenreTaggingTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="uploader", password="pass")
        self.client.login(username="uploader", password="pass")
        self.upload_url = reverse("upload_game")

    def _post_game(self, title="My Game"):
        return self.client.post(
            self.upload_url,
            {
                "title": title,
                "description": "An awesome indie game.",
                "price": "4.99",
            },
        )

    @patch("home.views._ai_tag_game")
    def test_upload_calls_ai_tag_game(self, mock_tag):
        self._post_game()
        mock_tag.assert_called_once()

    @patch("home.views._ai_tag_game", side_effect=RuntimeError("API down"))
    def test_upload_succeeds_even_when_tagging_fails(self, mock_tag):
        response = self._post_game(title="Resilient Game")
        self.assertRedirects(response, reverse("index"))
        self.assertTrue(Game.objects.filter(title="Resilient Game").exists())


# ---------------------------------------------------------------------------
# Management command: tag_genres
# ---------------------------------------------------------------------------


class TagGenresCommandTests(TestCase):

    @patch("home.management.commands.tag_genres._ai_tag_game")
    def test_tags_only_untagged_games_by_default(self, mock_tag):
        tagged_game = _make_game(title="Already Tagged")
        tag = GenreTag.objects.create(name="Action", slug="action")
        tagged_game.genre_tags.add(tag)

        untagged_game = _make_game(title="Needs Tags")

        call_command("tag_genres", "--delay=0", stdout=StringIO())

        calls = [c.args[0] for c in mock_tag.call_args_list]
        self.assertIn(untagged_game, calls)
        self.assertNotIn(tagged_game, calls)

    @patch("home.management.commands.tag_genres._ai_tag_game")
    def test_all_flag_retags_every_game(self, mock_tag):
        tagged_game = _make_game(title="Already Tagged")
        tag = GenreTag.objects.create(name="Action", slug="action")
        tagged_game.genre_tags.add(tag)

        untagged_game = _make_game(title="Needs Tags")

        call_command("tag_genres", "--all", "--delay=0", stdout=StringIO())

        self.assertEqual(mock_tag.call_count, 2)

    @patch("home.management.commands.tag_genres._ai_tag_game")
    def test_no_games_exits_early_with_message(self, mock_tag):
        out = StringIO()
        call_command("tag_genres", "--delay=0", stdout=out)

        mock_tag.assert_not_called()
        self.assertIn("already have genre tags", out.getvalue())

    @patch(
        "home.management.commands.tag_genres._ai_tag_game",
        side_effect=RuntimeError("fail"),
    )
    def test_failed_games_counted_in_output(self, mock_tag):
        _make_game(title="Game A")
        _make_game(title="Game B")
        out = StringIO()

        call_command("tag_genres", "--delay=0", stdout=out)

        output = out.getvalue()
        self.assertIn("0 tagged", output)
        self.assertIn("2 failed", output)
