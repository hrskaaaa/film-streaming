from django.core.management.base import BaseCommand
from django.conf import settings
import requests
from datetime import datetime, timedelta
from movies.models import Content
from movies.omdb_helpers import fetch_omdb_details
import time

class Command(BaseCommand):
    help = 'Fetches the newest movies, TV shows and anime'

    def handle(self, *args, **options):
        self.stdout.write("Fetching newest content...")
        
        # Fetch newest movies (released in last 3 months)
        self.fetch_new_omdb_content('movie', days=90)
        
        # Fetch newest TV shows (released in last 3 months)
        self.fetch_new_omdb_content('series', days=90)
        
        # Fetch currently airing anime
        self.fetch_current_anime()
        
        self.stdout.write(self.style.SUCCESS('Successfully fetched newest content'))

    def fetch_new_omdb_content(self, content_type, days=30, count=20):
        """Fetch new movies or TV shows from OMDB"""
        self.stdout.write(f"Fetching new {content_type}s from OMDB...")
        
        api_key = settings.OMDB_API_KEY
        current_year = datetime.now().year
        fetched_ids = set()
        current_count = 0
        
        # Search recent years
        for year in range(current_year, current_year - 2, -1):
            if current_count >= count:
                break
                
            url = f"http://www.omdbapi.com/?apikey={api_key}&y={year}&type={content_type}"
            response = requests.get(url).json()
            
            if response.get('Response') == 'True':
                for item in response.get('Search', []):
                    if current_count >= count:
                        break
                        
                    if item['imdbID'] in fetched_ids or Content.objects.filter(imdb_id=item['imdbID']).exists():
                        continue

                        
                    details = fetch_omdb_details(item['imdbID'], api_key)
                    if not details or not details['release_date']:
                        continue
                    
                    # Check if release date is within specified days
                    if (datetime.now().date() - details['release_date']).days > days:
                        continue
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                    Content.objects.update_or_create(
                        imdb_id=item['imdbID'],
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
                    
                    fetched_ids.add(item['imdbID'])
                    current_count += 1
                    self.stdout.write(f"Added {item['Title']} ({content_type})")
        
        self.stdout.write(f"Finished fetching {current_count} new {content_type}s")

    def fetch_current_anime(self, count=20):
        """Fetch currently airing anime from Jikan API"""
        self.stdout.write("Fetching currently airing anime from Jikan API...")
        
        current_count = 0
        page = 1
        
        while current_count < count:
            url = f"https://api.jikan.moe/v4/anime?status=airing&page={page}"
            response = requests.get(url).json()
            
            if 'data' not in response:
                break
                
            for item in response['data']:
                if current_count >= count:
                    break
                

                if Content.objects.filter(mal_id=item['mal_id']).exists():
                    continue

                # Skip non-TV anime
                if item.get('type') != 'TV':
                    continue
                
                # Convert ratings
                rating = None
                if 'score' in item and item['score']:
                    rating = float(item['score'])
                
                # Get studios
                studios = []
                for studio in item.get('studios', []):
                    studios.append(studio.get('name', ''))
                
                # Get genres
                genres = []
                for genre in item.get('genres', []):
                    genres.append(genre.get('name', ''))
                
                # Get release date
                release_date = None
                if item['aired'].get('from'):
                    try:
                        release_date = datetime.strptime(
                            item['aired']['from'].split('T')[0], 
                            '%Y-%m-%d'
                        ).date()
                    except:
                        pass
                
                Content.objects.update_or_create(
                    mal_id=item['mal_id'],
                    defaults={
                        'title': item['title'],
                        'type': 'ANIME',
                        'release_date': release_date,
                        'poster_url': item['images']['jpg'].get('image_url'),
                        'rating': rating,
                        'genres': genres,
                        'episodes': item.get('episodes', None),
                        'status': item.get('status', None),
                        'studios': studios,
                        'description': item.get('synopsis'),
                        'is_animated': True
                    }
                )
                
                current_count += 1
                self.stdout.write(f"Added {item['title']} (anime)")
            
            page += 1
            time.sleep(1)  # Respect Jikan API rate limits
        
        self.stdout.write(f"Finished fetching {current_count} currently airing anime")