from django.urls import path
from . import views

# URL patterns for the home app
urlpatterns = [
    # Homepage
    path('', views.index, name='index'),

    # Browse/explore all games
    path('browse/', views.browse, name='browse'),

    # Page where developers upload their games
    # Accessible at: /upload/
    path('upload/', views.upload_game, name='upload_game'),

    # Game detail page accessed by slug
    path("game/<slug:slug>/", views.game_detail, name="game_detail"),

    # Game purchase page accessed by game ID
    path('game/<int:game_id>/', views.purchase_game, name='purchase_game'),
]