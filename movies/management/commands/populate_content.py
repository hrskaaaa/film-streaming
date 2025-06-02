from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from datetime import datetime
from movies.models import Content
from movies.omdb_helpers import fetch_omdb_details
import time

class Command(BaseCommand):
    help = 'Populates database with popular movies, TV shows and anime'

    def handle(self, *args, **options):
        self.stdout.write("Starting to populate database with popular content...")
        
        # Fetch popular movies
        self.fetch_popular_omdb_content('movie', 50)
        
        # Fetch popular TV shows
        self.fetch_popular_omdb_content('series', 50)
        
        # Fetch popular anime
        self.fetch_popular_anime(50)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated database with popular content'))

    def fetch_popular_omdb_content(self, content_type, count=100):
        
        self.stdout.write(f"Fetching {count} popular {content_type}s from OMDB (2023–2025)...")

        api_key = settings.OMDB_API_KEY
        search_terms = ['the', 'of', 'a', 'love', 'war', 'star', 'life', 'day', 'man', 'woman']
        fetched_ids = set()
        current_count = 0
        current_year = datetime.now().year

        for year in range(2025, 2022, -1):  # 2025 to 2023
            for term in search_terms:
                if current_count >= count:
                    break

                url = f"http://www.omdbapi.com/?apikey={api_key}&s={term}&type={content_type}&y={year}"
                response = requests.get(url).json()

                if response.get('Response') != 'True':
                    continue

                for item in response.get('Search', []):
                    if current_count >= count:
                        break

                    imdb_id = item.get('imdbID')
                    if not imdb_id or imdb_id in fetched_ids or Content.objects.filter(imdb_id=imdb_id).exists():
                        continue

                    details = fetch_omdb_details(imdb_id, api_key)
                    if not details or not details.get('release_date'):
                        continue

                    release_year = details['release_date'].year
                    if release_year < 2023 or release_year > 2025:
                        continue

                    Content.objects.update_or_create(
                        imdb_id=imdb_id,
                        defaults={
                            'title': item['Title'],
                            'type': 'MOVIE' if content_type == 'movie' else 'TV_SHOW',
                            'release_date': details['release_date'],
                            'poster_url': item['Poster'] if item['Poster'] != 'N/A' else None,
                            'rating': details['rating'],
                            'genres': details['genres'],
                            'runtime': details['runtime'],
                            'director': details['director'],
                            'actors': details['actors'],
                            'description': details.get('Plot'),
                            'is_animated': details['is_animated']
                        }
                    )

                    fetched_ids.add(imdb_id)
                    current_count += 1
                    self.stdout.write(f"✔ Added {item['Title']} ({release_year})")

                    time.sleep(0.5)  # Respect OMDB rate limit

        self.stdout.write(f"🎯 Fetched total: {current_count} {content_type}s")



    # def fetch_popular_anime(self, count=50):
    #     """Fetch popular anime from Jikan API"""
    #     self.stdout.write("Fetching popular anime from Jikan API...")
        
    #     current_count = 0
    #     page = 1
        
    #     while current_count < count:
    #         url = f"https://api.jikan.moe/v4/top/anime?page={page}"
    #         response = requests.get(url).json()
            
    #         if 'data' not in response:
    #             break
                
    #         for item in response['data']:
    #             if current_count >= count:
    #                 break
                
    #             # Skip non-TV anime (movies, OVAs, etc.)
    #             if item.get('type') != 'TV':
    #                 continue
                
    #             # Convert ratings
    #             rating = None
    #             if 'score' in item and item['score']:
    #                 rating = float(item['score'])
                
    #             # Get studios
    #             studios = []
    #             for studio in item.get('studios', []):
    #                 studios.append(studio.get('name', ''))
                
    #             # Get genres
    #             genres = []
    #             for genre in item.get('genres', []):
    #                 genres.append(genre.get('name', ''))
                
    #             # Get release date
    #             release_date = None
    #             if item['aired'].get('from'):
    #                 try:
    #                     release_date = datetime.strptime(
    #                         item['aired']['from'].split('T')[0], 
    #                         '%Y-%m-%d'
    #                     ).date()
    #                 except:
    #                     pass
                
    #             Content.objects.update_or_create(
    #                 mal_id=item['mal_id'],
    #                 defaults={
    #                     'title': item['title'],
    #                     'type': 'ANIME',
    #                     'release_date': release_date,
    #                     'poster_url': item['images']['jpg'].get('image_url'),
    #                     'rating': rating,
    #                     'genres': genres,
    #                     'episodes': item.get('episodes', None),
    #                     'status': item.get('status', None),
    #                     'studios': studios,
    #                     'is_animated': True
    #                 }
    #             )
                
    #             current_count += 1
    #             self.stdout.write(f"Added {item['title']} (anime)")
            
    #         page += 1
    #         time.sleep(1)  # Respect Jikan API rate limits
        
    #     self.stdout.write(f"Finished fetching {current_count} anime")

