from django.contrib import admin
from .models import Content

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