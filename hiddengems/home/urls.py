from django.urls import path
from . import views

# URL patterns for the home app
urlpatterns = [
    # Homepage
    path('', views.index, name='index'),

    # Page where developers upload their games
    # Accessible at: /upload/
    path('upload/', views.upload_game, name='upload_game'),
]