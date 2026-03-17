from django.db import models
from django.utils.text import slugify

class Game(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    publisher = models.CharField(max_length=200)
    developer = models.CharField(max_length=200)

    #Steam Integration
    storefront = models.CharField(max_length=50, default="steam")
    price = models.DecimalField(decimal_places=2, max_digits=10)
    game_id = models.IntegerField()

    #Slugification for url
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
