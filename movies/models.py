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
    description = models.TextField(blank=True, null=True)  

    # source_stream_url = models.URLField(blank=True, null=True, help_text="Base m3u8 URL to parse")

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


from django.contrib.auth.models import User

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name="user_ratings")
    rating = models.PositiveIntegerField(default=1)  
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} rated {self.content.title} ({self.rating})"


class VideoSource(models.Model):
    content = models.ForeignKey('Content', on_delete=models.CASCADE, related_name='video_sources')
    source_url = models.URLField(max_length=500)
    quality = models.CharField(max_length=20, blank=True, default='Unknown')
    voice_name = models.CharField(max_length=100, default='Невідоме озвучення')
    data_id = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=False)
    streaming_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content', 'source_url']
    
    def __str__(self):
        return f"{self.content.title} - {self.voice_name}"