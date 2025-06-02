from django.contrib import admin
from .models import Content, Rating, VideoSource

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'release_date', 'rating')
    list_filter = ('type', 'genres')
    search_fields = ('title', 'director', 'actors')
    date_hierarchy = 'release_date'
    
    # Customize how JSONField data is displayed
    def get_genres(self, obj):
        return ", ".join(obj.genres) if obj.genres else ""
    get_genres.short_description = "Genres"
    
    def get_actors(self, obj):
        return ", ".join(obj.actors) if obj.actors else ""
    get_actors.short_description = "Actors"

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'rating', 'timestamp')
    list_filter = ('rating', 'timestamp')
    search_fields = ('user__username', 'content__title')
    raw_id_fields = ('user', 'content')
    date_hierarchy = 'timestamp'

@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ('content', 'voice_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'voice_name')
    search_fields = ('content__title', 'source_url')
    raw_id_fields = ('content',)
    date_hierarchy = 'created_at'
    list_editable = ('is_active',)