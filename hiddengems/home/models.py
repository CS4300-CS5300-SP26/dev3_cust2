from django.db import models

class Game(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    publisher = models.CharField(max_length=200)
    developer = models.CharField(max_length=200)

    def __str__(self):
        return self.title