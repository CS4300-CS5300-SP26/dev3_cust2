from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse

from .models import Game


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("title", "publisher", "developer", "storefront", "game_id")
    search_fields = ("title", "publisher", "developer", "game_id")
    change_list_template = "admin/hiddengems/game/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "sync-update-all/",
                self.admin_site.admin_view(self.sync_update_all_view),
                name="hiddengems_game_sync_update_all",
            ),
            path(
                "sync-add-missing/",
                self.admin_site.admin_view(self.sync_add_missing_view),
                name="hiddengems_game_sync_add_missing",
            ),
            path(
                "sync-update-one/",
                self.admin_site.admin_view(self.sync_update_one_view),
                name="hiddengems_game_sync_update_one",
            ),
        ]
        return custom_urls + urls

    def sync_update_all_view(self, request):
        messages.info(request, "Update all Steam games button clicked. Logic not implemented yet.")
        return HttpResponseRedirect(reverse("admin:hiddengems_game_changelist"))

    def sync_add_missing_view(self, request):
        messages.info(request, "Add missing Steam games button clicked. Logic not implemented yet.")
        return HttpResponseRedirect(reverse("admin:hiddengems_game_changelist"))

    def sync_update_one_view(self, request):
        if request.method == "POST":
            steam_id = request.POST.get("steam_id", "").strip()
            messages.info(
                request,
                f"Update single Steam game requested for Steam ID: {steam_id or '(empty)'}. Logic not implemented yet."
            )
            return HttpResponseRedirect(reverse("admin:hiddengems_game_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Update one Steam game",
        }
        return render(request, "admin/hiddengems/game/update_one_form.html", context)