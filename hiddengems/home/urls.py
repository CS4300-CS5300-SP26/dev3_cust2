from django.urls import path
from .views import index
from .views import game_detail

urlpatterns = [
    path('', index, name='index'),
    path("game/<int:game_id>/", game_detail, name="game_detail"),
]
