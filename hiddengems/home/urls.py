from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

# URL patterns for the home app
urlpatterns = [
    # Homepage
    path('', views.index, name='index'),

    # Browse/explore all games
    path('browse/', views.browse, name='browse'),

    # Page where developers upload their games
    # Accessible at: /upload/
    path('upload/', views.upload_game, name='upload_game'),

    # Game purchase page accessed by game ID (must come before slug pattern)
    path('game/<int:game_id>/', views.purchase_game, name='purchase_game'),

    # Game detail page accessed by slug
    path("game/<slug:slug>/", views.game_detail, name="game_detail"),

    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)