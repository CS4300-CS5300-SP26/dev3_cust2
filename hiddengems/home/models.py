from django.db import models

# Create your models here.from django.db import models
from django.contrib.auth.models import User

# Game model stores all information about a developer's uploaded game
class Game(models.Model):

    # Title of the game
    title = models.CharField(max_length=200)

    # Full description of the game (story, mechanics, etc.)
    description = models.TextField()

    # The developer who uploaded the game
    # Linked to Django's built-in User model
    developer = models.ForeignKey(User, on_delete=models.CASCADE)

    # Price of the game
    price = models.DecimalField(max_digits=6, decimal_places=2)

    # Genre of the game (RPG, puzzle, platformer, etc.)
    genre = models.CharField(max_length=100)

    # Indicates if the game can run directly in the browser
    playable_in_browser = models.BooleanField(default=False)

    # Other platforms the game is available on (Steam, itch.io, etc.)
    other_platforms = models.CharField(max_length=200, blank=True)

    # Thumbnail image displayed on the game page
    # Using FileField instead of ImageField due to container dependency issues
    thumbnail = models.FileField(upload_to='game_thumbnails/')

    # Optional uploaded build (zip or web build)
    build_file = models.FileField(upload_to='game_builds/', blank=True)

    # Automatically records when the game was uploaded
    created_at = models.DateTimeField(auto_now_add=True)

    # String representation of the object in admin panel
    def __str__(self):
        return self.title