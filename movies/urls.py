from django.urls import path
from . import views
from . import api_views 

urlpatterns = [
    path('', views.home, name='home'),
    path('movies/', views.movies_page, name='movies'),
    path('tvshows/', views.tvshows_page, name='tv_shows'),
    path('anime/', views.anime_page, name='anime'),
    path('content/<int:pk>/', views.content_detail, name='content_detail'),
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    
    # API endpoints
    path('api/movies/', views.fetch_movies, name='fetch_movies'),
    path('api/tvshows/', views.fetch_tvshows, name='fetch_tvshows'),
    path('api/anime/', views.fetch_anime, name='fetch_anime'),
    
    # Search endpoints
    path('api/search/autocomplete/', views.search_autocomplete, name='search_autocomplete'),
    path('search/', views.search_results, name='search_results'),

    path('api/recent/', api_views.RecentContentAPIView.as_view(), name='api-recent'),
    path('api/popular/', api_views.PopularContentAPIView.as_view(), name='api-popular'),

    path('api/get_streaming_url/<int:source_id>/', views.get_streaming_url, name='get_streaming_url'),
    path('api/refresh_video_sources/<int:content_id>/', views.refresh_video_sources, name='refresh_video_sources'),

    path('api/recommendations/', views.api_recommendations, name='api_recommendations'),

]
