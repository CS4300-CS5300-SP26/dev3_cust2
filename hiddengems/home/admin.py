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
        api_key = os.environ.get("STEAM_WEB_API_KEY")

        if not api_key:
            messages.error(request, "STEAM_WEB_API_KEY is missing from settings.py")
            return HttpResponseRedirect(reverse("admin:home_game_changelist"))

        try:
            app_list = self.fetch_store_app_list(api_key=api_key, max_results=25)
        except Exception as e:
            messages.error(request, f"Could not fetch Steam app list: {e}")
            return HttpResponseRedirect(reverse("admin:home_game_changelist"))

        created_count = 0
        updated_count = 0
        failed_count = 0
        skipped_count = 0

        for app in app_list:
            try:
                steam_id = app.get("appid")
                name = (app.get("name") or "").strip()

                if not steam_id or not str(steam_id).isdigit():
                    skipped_count += 1
                    continue

                if not name:
                    skipped_count += 1
                    continue

                steam_data = self.fetch_steam_game_data(str(steam_id))
                game, created = self.upsert_steam_game(str(steam_id), steam_data)

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception:
                failed_count += 1

        if created_count:
            messages.success(request, f"Created {created_count} Steam game(s).")
        if updated_count:
            messages.success(request, f"Updated {updated_count} Steam game(s).")
        if skipped_count:
            messages.info(request, f"Skipped {skipped_count} app(s).")
        if failed_count:
            messages.warning(request, f"{failed_count} app(s) failed during import.")

        if not any([created_count, updated_count, skipped_count, failed_count]):
            messages.info(request, "No Steam apps were processed.")

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

    def fetch_store_app_list(self, api_key, last_appid=None, max_results=25):
        params = {
            "key": api_key,
            "max_results": max_results,
            "include_games": "true",
            "include_dlc": "false",
            "include_software": "false",
            "include_videos": "false",
            "include_hardware": "false",
            "input_json": "1",
        }

        if last_appid is not None:
            params["last_appid"] = last_appid

        url = "https://api.steampowered.com/ISteamApps/GetAppList/v2" + urlencode(params)

        try:
            with urlopen(url) as response:
                payload = json.load(response)
        except HTTPError as exc:
            raise ValueError(f"Steam app list HTTP error: {exc.code}")
        except URLError as exc:
            raise ValueError(f"Could not reach Steam app list endpoint: {exc}")
        except json.JSONDecodeError:
            raise ValueError("Steam app list returned invalid JSON.")

        response_data = payload.get("response", {})
        apps = response_data.get("apps", [])

        if not isinstance(apps, list):
            raise ValueError("Steam app list response format was unexpected.")

        return apps