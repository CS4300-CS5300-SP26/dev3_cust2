from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from home.forms import GameUploadForm
from home.models import Game


class GameUploadFormTest(TestCase):

    def base_data(self):
        """Valid form data to build on top of in each test."""
        return {
            "title": "Test Game",
            "description": "A test game.",
            "price": "9.99",
            "genre": "Action",
            "playable_in_browser": False,
            "other_platforms": "",
            "on_steam": False,
            "steam_id": "",
        }

    # --- Price ---

    def test_negative_price_invalid(self):
        data = self.base_data()
        data["price"] = "-1.00"
        form = GameUploadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_zero_price_valid(self):
        data = self.base_data()
        data["price"] = "0.00"
        form = GameUploadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_price_too_large_invalid(self):
        data = self.base_data()
        data["price"] = "99999999.00"
        form = GameUploadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    # --- Steam ---

    def test_on_steam_without_id_invalid(self):
        data = self.base_data()
        data["on_steam"] = True
        data["steam_id"] = ""
        form = GameUploadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("steam_id", form.errors)

    def test_on_steam_with_id_valid(self):
        data = self.base_data()
        data["on_steam"] = True
        data["steam_id"] = "400"
        form = GameUploadForm(data=data)
        self.assertTrue(form.is_valid())

    def test_duplicate_steam_id_invalid(self):
        Game.objects.create(
            storefront="steam", 
            game_id=400, 
            title="Existing",
            price="9.99"
        )
        data = self.base_data()
        data["on_steam"] = True
        data["steam_id"] = "400"
        form = GameUploadForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("steam_id", form.errors)

    # --- Thumbnail ---

    def test_invalid_thumbnail_extension(self):
        data = self.base_data()
        bad_file = SimpleUploadedFile("image.svg", b"<svg/>", content_type="image/svg+xml")
        form = GameUploadForm(data=data, files={"thumbnail": bad_file})
        self.assertFalse(form.is_valid())
        self.assertIn("thumbnail", form.errors)

    def test_valid_thumbnail_extension(self):
        data = self.base_data()
        good_file = SimpleUploadedFile("image.png", b"fakepng", content_type="image/png")
        form = GameUploadForm(data=data, files={"thumbnail": good_file})
        self.assertTrue(form.is_valid())

    # --- Build file ---

    def test_invalid_build_file_extension(self):
        data = self.base_data()
        bad_file = SimpleUploadedFile("game.exe", b"fakeexe", content_type="application/octet-stream")
        form = GameUploadForm(data=data, files={"build_file": bad_file})
        self.assertFalse(form.is_valid())
        self.assertIn("build_file", form.errors)

    def test_valid_build_file_zip(self):
        data = self.base_data()
        good_file = SimpleUploadedFile("game.zip", b"fakezip", content_type="application/zip")
        form = GameUploadForm(data=data, files={"build_file": good_file})
        self.assertTrue(form.is_valid())