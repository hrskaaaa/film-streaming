from django.db import models

class Content(models.Model):
    TYPE_CHOICES = [
        ('MOVIE', 'Movie'),
        ('TV_SHOW', 'TV Show'),
        ('ANIME', 'Anime'),
    ]

    title = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    is_animated = models.BooleanField(default=False)

    # IDs from different sources
    imdb_id = models.CharField(max_length=20, blank=True, null=True)
    mal_id = models.IntegerField(blank=True, null=True)

    # Common fields
    release_date = models.DateField(blank=True, null=True)
    poster_url = models.URLField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    genres = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True, null=True)  # ✅ NEW FIELD

    # Movie/TV Show specific fields
    runtime = models.IntegerField(blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    actors = models.JSONField(default=list, blank=True)

    # Anime specific fields
    episodes = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    studios = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.type})"
