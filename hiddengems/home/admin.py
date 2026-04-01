import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "publisher", "developer", "storefront", "game_id", "price")
    search_fields = ("title", "publisher", "developer", "game_id")
    change_list_template = "admin/home/game/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-update-all/",
                self.admin_site.admin_view(self.sync_update_all_view),
                name="home_game_sync_update_all",
            ),
            path(
                "sync-add-missing/",
                self.admin_site.admin_view(self.sync_add_missing_view),
                name="home_game_sync_add_missing",
            ),
            path(
                "sync-update-one/",
                self.admin_site.admin_view(self.sync_update_one_view),
                name="home_game_sync_update_one",
            ),
        ]
        return custom_urls + urls

    def sync_update_all_view(self, request):
        messages.info(request, "Not implemented yet.")
        return HttpResponseRedirect(reverse("admin:home_game_changelist"))

    def sync_add_missing_view(self, request):
        messages.info(request, "Not implemented yet.")
        return HttpResponseRedirect(reverse("admin:home_game_changelist"))

    def sync_update_one_view(self, request):
        if request.method == "POST":
            steam_id = request.POST.get("steam_id", "").strip()

            if not steam_id.isdigit():
                messages.error(request, "Steam ID must be numeric.")
                return HttpResponseRedirect(reverse("admin:home_game_sync_update_one"))

            try:
                steam_data = self.fetch_steam_game_data(steam_id)
                game, created = self.upsert_steam_game(steam_id, steam_data)

                if created:
                    messages.success(request, f"Created {game.title}.")
                else:
                    messages.success(request, f"Updated {game.title}.")

                return HttpResponseRedirect(reverse("admin:home_game_changelist"))

            except Exception as e:
                messages.error(request, f"Error: {e}")
                return HttpResponseRedirect(reverse("admin:home_game_sync_update_one"))

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Update one Steam game",
        }
        return render(request, "admin/home/game/update_one_form.html", context)

    def fetch_steam_game_data(self, steam_id):
        url = f"https://store.steampowered.com/api/appdetails?appids={steam_id}"

        try:
            with urlopen(url) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ValueError(f"Steam API HTTP error: {exc.code}")
        except URLError:
            raise ValueError("Could not reach Steam API.")

        app_block = payload.get(str(steam_id))
        if not app_block or not app_block.get("success"):
            raise ValueError("Steam game not found.")

        data = app_block.get("data", {})
        if not data:
            raise ValueError("Steam returned empty data.")

        return data

    def upsert_steam_game(self, steam_id, steam_data):
        title = steam_data.get("name", "").strip()
        description = steam_data.get("short_description", "").strip()

        developers = steam_data.get("developers") or []
        publishers = steam_data.get("publishers") or []

        developer = ", ".join(developers) if developers else "Unknown"
        publisher = ", ".join(publishers) if publishers else "Unknown"

        price_overview = steam_data.get("price_overview")
        is_free = steam_data.get("is_free", False)

        if is_free:
            price = Decimal("0.00")
        elif price_overview and "final" in price_overview:
            price = Decimal(price_overview["final"]) / Decimal("100")
        else:
            price = Decimal("0.00")

        game, created = Game.objects.get_or_create(
            storefront="steam",
            game_id=int(steam_id),
            defaults={
                "title": title,
                "description": description,
                "publisher": publisher,
                "developer": developer,
                "price": price,
            },
        )

        if not created:
            game.title = title
            game.description = description
            game.publisher = publisher
            game.developer = developer
            game.price = price
            game.save()

        return game, created