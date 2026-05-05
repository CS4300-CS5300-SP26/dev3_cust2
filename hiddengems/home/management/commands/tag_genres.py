import time

from django.core.management.base import BaseCommand

from home.models import Game
from home.views import _ai_tag_game


class Command(BaseCommand):
    help = "Auto-assign AI genre tags to games that don't have any yet."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-tag all games, including those that already have tags.",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between API calls (default: 0.5).",
        )

    def handle(self, *args, **options):
        retag_all = options["all"]
        delay = options["delay"]

        if retag_all:
            games = Game.objects.all()
        else:
            games = Game.objects.filter(genre_tags__isnull=True)

        total = games.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("All games already have genre tags."))
            return

        self.stdout.write(f"Tagging {total} game(s)...\n")
        success, failed = 0, 0

        for i, game in enumerate(games, 1):
            try:
                _ai_tag_game(game)
                tags = ", ".join(game.genre_tags.values_list("name", flat=True))
                self.stdout.write(f"  [{i}/{total}] {game.title}  →  {tags}")
                success += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  [{i}/{total}] {game.title}  →  FAILED: {e}")
                )
                failed += 1

            if i < total:
                time.sleep(delay)

        self.stdout.write(
            self.style.SUCCESS(f"\nDone. {success} tagged, {failed} failed.")
        )
