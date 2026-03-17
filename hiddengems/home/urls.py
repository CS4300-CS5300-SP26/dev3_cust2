from django.urls import path
from .views import index, purchase_game

urlpatterns = [
    path('', index, name='index'),
    path('game/<int:game_id>/', purchase_game, name='purchase_game')
]