import json
import os
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlencode

from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .models import Game

from django.conf import settings



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
                "sync-update-one/",
                self.admin_site.admin_view(self.sync_update_one_view),
                name="home_game_sync_update_one",
            ),
        ]
        return custom_urls + urls


    def sync_update_all_view(self, request):
        if request.method == "POST":
            start_id = request.POST.get("start_id", "").strip()
            end_id = request.POST.get("end_id", "").strip()

            if not start_id.isdigit() or not end_id.isdigit():
                messages.error(request, "Start ID and End ID must both be numeric.")
                return HttpResponseRedirect(reverse("admin:home_game_sync_update_all"))

            start_id = int(start_id)
            end_id = int(end_id)

            if start_id > end_id:
                messages.error(request, "Start ID must be less than or equal to End ID.")
                return HttpResponseRedirect(reverse("admin:home_game_sync_update_all"))

            created_count = 0
            updated_count = 0
            failed_ids = []

            for steam_id in range(start_id, end_id + 1):
                try:
                    steam_data = self.fetch_steam_game_data(str(steam_id))
                    game, created = self.upsert_steam_game(str(steam_id), steam_data)

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

                except Exception:
                    failed_ids.append(steam_id)

            if created_count:
                messages.success(request, f"Created {created_count} Steam game(s).")
            if updated_count:
                messages.success(request, f"Updated {updated_count} Steam game(s).")
            if failed_ids:
                messages.warning(request, f"Failed IDs: {failed_ids}")

            if not any([created_count, updated_count, failed_ids]):
                messages.info(request, "No Steam IDs were processed.")

            return HttpResponseRedirect(reverse("admin:home_game_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Update Steam games by range",
        }
        return render(request, "admin/home/game/update_range_form.html", context)

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
        title = (steam_data.get("name") or "").strip()
        if not title:
            raise ValueError("Steam data did not include a title.")

        description = (steam_data.get("short_description") or "").strip()

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
        else:
            game.save()

        return game, created