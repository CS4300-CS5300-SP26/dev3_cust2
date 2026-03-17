from django.urls import path
from .views import index
from .views import game_detail
from .views import purchase_game

urlpatterns = [
    path('', index, name='index'),
    path("game/<slug:slug>/", game_detail, name="game_detail"),
    path('game/<int:game_id>/', purchase_game, name='purchase_game')
]
