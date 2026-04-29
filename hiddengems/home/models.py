from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.cache import cache

CANONICAL_GENRES = [
    "Action", "Adventure", "RPG", "Strategy", "Puzzle", "Platformer",
    "Horror", "Simulation", "Sports", "Racing", "Visual Novel", "Roguelike",
    "Shoot-em-up", "Fighting", "Rhythm", "Card Game", "Metroidvania", "Idle",
]


class GenreTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


# Game model stores all information about a developer's uploaded game
class Game(models.Model):

    # Title of the game
    title = models.CharField(max_length=200)

    # URL-friendly slug generated from title
    slug = models.SlugField(unique=True, blank=True, max_length=255)

    # Full description of the game (story, mechanics, etc.)
    description = models.TextField()

    # Developer name as a string (e.g. "Indie Studio X")
    developer = models.CharField(max_length=200, blank=True)

    # The user who uploaded the game
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_games', null=True, blank=True)

    # Users authorized to edit this game
    authorized_users = models.ManyToManyField(User, related_name='authorized_games', blank=True)

    # Publisher of the game
    publisher = models.CharField(max_length=200, blank=True)

    # Price of the game
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Genre of the game (RPG, puzzle, platformer, etc.)
    genre = models.CharField(max_length=100, blank=True)

    # AI-assigned genre tags (M2M, populated automatically on upload)
    genre_tags = models.ManyToManyField(GenreTag, blank=True, related_name='games')

    # Indicates if the game can run directly in the browser
    playable_in_browser = models.BooleanField(default=False)

    # Other platforms the game is available on (Steam, itch.io, etc.)
    other_platforms = models.CharField(max_length=200, blank=True)

    # Thumbnail image displayed on the game page
    thumbnail = models.FileField(upload_to='game_thumbnails/', blank=True)

    # Optional uploaded build (zip or web build)
    build_file = models.FileField(upload_to='game_builds/', blank=True)

    # Steam Integration
    storefront = models.CharField(max_length=50, default="steam")
    game_id = models.IntegerField(null=True, blank=True)

    # Automatically records when the game was uploaded
    created_at = models.DateTimeField(auto_now_add=True)

    # Auto-generate slug from title if not provided
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "game"
            slug = base_slug
            counter = 1

            while Game.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    # String representation of the object in admin panel
    def __str__(self):
        return self.title

@receiver(models.signals.post_save, sender=Game)
def invalidate_similar_games_cache(sender, instance, **kwargs):
    cache.delete(f"similar_games_{instance.pk}")
    SimilarGame.objects.filter(game=instance).delete()

@receiver(models.signals.m2m_changed, sender=Game.genre_tags.through)
def invalidate_genre_cache(sender, instance, action, pk_set, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        for tag in instance.genre_tags.all():
            cache.delete(f"genre_games_{tag.slug}")

class SimilarGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='similar_games')
    similar = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='similar_to')
    score = models.FloatField()
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-score']
        unique_together = [['game', 'similar']]

    def __str__(self):
        return f"{self.game.title} -> {self.similar.title} ({self.score:.2f})"