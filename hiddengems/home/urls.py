from django.urls import path
from . import views

# URL patterns for the home app
urlpatterns = [
    # Homepage
    path('', views.index, name='index'),

    # Page where developers upload their games
    # Accessible at: /upload/
    path('upload/', views.upload_game, name='upload_game'),

    # Game detail page accessed by slug
    path("game/<slug:slug>/", views.game_detail, name="game_detail"),

    # Game purchase page accessed by game ID
    path('game/<int:game_id>/', views.purchase_game, name='purchase_game'),
]
```

Run:
```
nano /home/student/dev3_cust2/hiddengems/home/urls.py
```

Paste it in, save with `Ctrl+X`, `Y`, `Enter`. Then check for any remaining conflicts:
```
grep -r "<<<<<<" ~/dev3_cust2 --include="*.py" -l
