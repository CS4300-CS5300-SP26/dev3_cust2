from django.urls import path
from .views import game_detail

urlpatterns = [
    path("game/<slug:slug>/", game_detail, name="game_detail"),
]
