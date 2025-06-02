from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Local imports
from .models import Content, Rating, VideoSource
from .omdb_helpers import fetch_omdb_details
from movies.utils.kino_ua_parser import KinoUAParser
from movies.gnn.recommend import get_recommendations

# Standard library imports
import requests
import json
import logging
from datetime import datetime

# Third-party imports
from asgiref.sync import async_to_sync
import asyncio


def home(request):
    # Популярні фільми 
    popular_items = Content.objects.filter(
        release_date__year__gte=2020,
        release_date__year__lte=2025
    ).order_by('-rating')[:12]

    # Новинки 
    recent_items = Content.objects.order_by('-release_date')[:12]

    # Розбиваємо популярні по 4 для каруселі
    def chunked(iterable, n):
        return [iterable[i:i + n] for i in range(0, len(iterable), n)]

    popular_chunks = chunked(list(popular_items), 4)

    recommended_items = []
    if request.user.is_authenticated:
        try:
            recommended_movie_ids = get_recommendations(request.user.id, top_k=8)
            recommended_items = Content.objects.filter(id__in=recommended_movie_ids)
        except Exception:
            recommended_items = []

    return render(request, 'home_content.html', {
        'popular_chunks': popular_chunks,
        'recent_items': recent_items
        # 'recommended_items': recommended_items
    })

def api_recommendations(request):
    user_id = request.user.id if request.user.is_authenticated else None
    if not user_id:
        return JsonResponse({'results': []})

    try:
        recommended_movie_ids = get_recommendations(user_id, top_k=10)
        contents = Content.objects.filter(id__in=recommended_movie_ids)
        data = [{
            'id': c.id,
            'title': c.title,
            'poster_url': c.poster_url,
            'release_date': c.release_date,
            'type': c.get_type_display()
        } for c in contents]
        return JsonResponse({'results': data})
    except Exception as e:
        return JsonResponse({'results': [], 'error': str(e)}, status=500)
    

def movies_page(request):
    genres = get_unique_genres('MOVIE')
    ratings = get_unique_ratings('MOVIE')
    context = {
        'active_page': 'movies',
        'genres': genres,
        'ratings': ratings
    }
    return render(request, 'movies/movies.html', context)

def tvshows_page(request):
    genres = get_unique_genres('TV_SHOW')
    context = {
        'active_page': 'tvshows',
        'genres': genres
    }
    return render(request, 'movies/tvshows.html', context)

def anime_page(request):
    genres = get_unique_genres('ANIME')
    statuses = get_unique_statuses('ANIME')
    contex = {
        'active_page': 'anime',
        'genres': genres,
        'statuses': statuses
    }
    return render(request, 'movies/anime.html', contex)

def content_detail(request, pk):
    content = get_object_or_404(Content, pk=pk)
    
    # Handle user rating
    user_rating = None
    if request.user.is_authenticated:
        user_rating_obj = Rating.objects.filter(user=request.user, content=content).first()
        if user_rating_obj:
            user_rating = user_rating_obj.rating

        if request.method == 'POST':
            new_rating = request.POST.get('rating')
            if new_rating and new_rating.isdigit():
                new_rating = int(new_rating)
                if 1 <= new_rating <= 5:
                    if user_rating_obj:
                        user_rating_obj.rating = new_rating
                        user_rating_obj.save()
                    else:
                        Rating.objects.create(
                            user=request.user, 
                            content=content, 
                            rating=new_rating
                        )
                    return redirect('content_detail', pk=pk)

    # If no video sources exist, try to find them
    if not content.video_sources.exists():
        parser = KinoUAParser()
        search_results = async_to_sync(parser.search_content)(content.title)
        
        if search_results:
            # Take the first result (best match)
            best_match = search_results[0]
            video_data = async_to_sync(parser.get_video_links)(best_match['url'])
            
            if video_data['success']:
                for source in video_data['video_sources']:
                    VideoSource.objects.create(
                        content=content,
                        source_url=source['url'],
                        voice_name=source.get('voice_name', 'Original'),
                        data_id=source.get('data_id', ''),
                        is_active=True
                    )
    
    context = {
        'content': content,
        'user_rating': user_rating,
        'video_sources': content.video_sources.all()
    }
    
    return render(request, 'movies/content_detail.html', context)

logger = logging.getLogger(__name__)

@csrf_exempt
def get_streaming_url(request, source_id):
    logger = logging.getLogger(__name__)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        video_source = get_object_or_404(VideoSource, id=source_id)

        # Використовуємо кешовану URL якщо є
        if video_source.streaming_url:
            return JsonResponse({
                'success': True,
                'streaming_url': video_source.streaming_url,
                'voice_name': video_source.voice_name
            })

        parser = KinoUAParser()

        # 🟡 Виклик асинхронної функції в синхронному view
        result = async_to_sync(parser.get_video_links)(video_source.source_url)

        if result['success'] and result['video_sources']:
            video_url = result['video_sources'][0]['url']
            video_source.streaming_url = video_url
            video_source.save()
            return JsonResponse({
                'success': True,
                'streaming_url': video_url,
                'voice_name': video_source.voice_name
            })

        return JsonResponse({
            'success': False,
            'error': result.get('error', 'Не знайдено стрім')
        }, status=500)

    except Exception as e:
        logger.error(f"Error getting streaming URL: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def refresh_video_sources(request, content_id):
    logger = logging.getLogger(__name__)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        content = get_object_or_404(Content, id=content_id)
        parser = KinoUAParser()

        # Очистка старих джерел
        content.video_sources.all().delete()

        # 🟡 Виклик асинхронного пошуку
        search_results = async_to_sync(parser.search_content)(content.title)
        sources_added = 0

        if search_results:
            video_data = async_to_sync(parser.get_video_links)(search_results[0]['url'])
            if video_data['success']:
                for source in video_data['video_sources']:
                    VideoSource.objects.create(
                        content=content,
                        source_url=source['url'],
                        voice_name=source.get('voice_name', 'Original'),
                        data_id=source.get('data_id', ''),
                        is_active=True,
                        quality=source.get('quality', 'Unknown'),
            )
                    
                    sources_added += 1

        return JsonResponse({
            'success': True,
            'sources_added': sources_added,
            'message': f'Added {sources_added} video sources'
        })

    except Exception as e:
        logger.error(f"Error refreshing video sources: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

    return asyncio.run(async_handler())

def get_unique_genres(content_type=None):
    if content_type:
        queryset = Content.objects.filter(type=content_type)
    else:
        queryset = Content.objects.all()
    
    # Збираємо всі унікальні жанри
    unique_genres = set()
    
    for content in queryset:
        if content.genres:
            if isinstance(content.genres, list):
                # Якщо жанри збережені як список
                unique_genres.update(content.genres)
            elif isinstance(content.genres, str):
                # Якщо жанри збережені як рядок, розділений комами
                genres_list = [genre.strip() for genre in content.genres.split(',') if genre.strip()]
                unique_genres.update(genres_list)
    
    # Повертаємо відсортований список унікальних жанрів
    return sorted(list(unique_genres))

def get_unique_statuses(content_type='ANIME'):

    queryset = Content.objects.filter(type=content_type, status__isnull=False).exclude(status='')
    
    # Збираємо всі унікальні статуси
    unique_statuses = set()
    
    for content in queryset:
        if content.status:
            # Очищуємо статус від зайвих пробілів
            clean_status = content.status.strip()
            if clean_status:
                unique_statuses.add(clean_status)
    
    # Повертаємо відсортований список унікальних статусів
    return sorted(list(unique_statuses))

def get_unique_ratings(content_type=None):
    if content_type:
        queryset = Content.objects.filter(type=content_type)
    else:
        queryset = Content.objects.all()

    unique_ratings = set()

    for content in queryset:
        if content.rating is not None:
            try:
                # Округлюємо рейтинг до найближчого цілого
                rating_int = int(float(content.rating))
                unique_ratings.add(rating_int)
            except (ValueError, TypeError):
                continue

    return sorted(list(unique_ratings), reverse=True)  # Від найвищого до найнижчого


@csrf_exempt
def fetch_movies(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        genre_filter = request.GET.get('genre')
        year_range = request.GET.get('year')
        rating_order = request.GET.get('min_rating')  # 'top' or 'least'
        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 20))

        queryset = Content.objects.filter(type='MOVIE')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if genre_filter:
            queryset = queryset.filter(genres__icontains=genre_filter)

        if year_range:
            try:
                year_from, year_to = map(int, year_range.split('-'))
                queryset = queryset.filter(release_date__year__gte=year_from, release_date__year__lte=year_to)
            except ValueError:
                pass

        if rating_order == 'top':
            queryset = queryset.order_by('-rating')
        elif rating_order == 'least':
            queryset = queryset.order_by('rating')
        else:
            queryset = queryset.order_by('-release_date')

        paginator = Paginator(queryset, page_size)
        total_pages = paginator.num_pages
        total_count = paginator.count

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        movies_data = []
        for movie in page_obj:
            movie_dict = {
                'id': movie.id,
                'title': movie.title,
                'type': movie.type,
                'release_date': movie.release_date.isoformat() if movie.release_date else None,
                'poster_url': movie.poster_url,
                'rating': float(movie.rating) if movie.rating else None,
                'genres': movie.genres,
                'runtime': movie.runtime,
                'director': movie.director,
                'actors': movie.actors,
                'description': movie.description,
                'imdb_id': movie.imdb_id,
            }
            movies_data.append(movie_dict)

        return JsonResponse({
            'movies': movies_data,
            'total_pages': total_pages,
            'count': total_count
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_tvshows(request):
    if request.method == 'GET':
        search_query = request.GET.get('search', '')
        genre_filter = request.GET.get('genre')
        min_rating = request.GET.get('min_rating')
        year_range = request.GET.get('year')  # Expecting values like "2010-2020"
        sort_by = request.GET.get('min_rating')  # 'top', 'least', or None
        page = request.GET.get('page', 1)
        page_size = int(request.GET.get('page_size', 20))

        queryset = Content.objects.filter(type='TV_SHOW')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if genre_filter:
            queryset = queryset.filter(genres__icontains=genre_filter)

        if min_rating:
            try:
                queryset = queryset.filter(rating__gte=float(min_rating))
            except ValueError:
                pass

        if year_range:
            try:
                year_from, year_to = map(int, year_range.split('-'))
                queryset = queryset.filter(release_date__year__gte=year_from, release_date__year__lte=year_to)
            except ValueError:
                pass

        if sort_by == 'top':
            queryset = queryset.order_by('-rating')
        elif sort_by == 'least':
            queryset = queryset.order_by('rating')
        else:
            queryset = queryset.order_by('-release_date')

        paginator = Paginator(queryset, page_size)
        total_pages = paginator.num_pages
        total_count = paginator.count

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        tvshows_data = []
        for tvshow in page_obj:
            tvshow_data = {
                'id': tvshow.id,
                'title': tvshow.title,
                'type': tvshow.type,
                'release_date': tvshow.release_date.isoformat() if tvshow.release_date else None,
                'poster_url': tvshow.poster_url,
                'rating': float(tvshow.rating) if tvshow.rating else None,
                'genres': tvshow.genres,
                'runtime': tvshow.runtime,
                'director': tvshow.director,
                'actors': tvshow.actors,
                'imdb_id': tvshow.imdb_id,
                'description': tvshow.description,
                'is_animated': tvshow.is_animated
            }
            tvshows_data.append(tvshow_data)

        return JsonResponse({
            'tvshows': tvshows_data,
            'total_pages': total_pages,
            'count': total_count
        })

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def fetch_anime(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    rating_order = request.GET.get('min_rating')  # 'top' or 'least'
    search_query = request.GET.get('search', '').strip()
    genre_filter = request.GET.get('genre', '')
    status_filter = request.GET.get('status', '')
    min_rating = request.GET.get('min_rating', '')
    page = int(request.GET.get('page', 1))
    page_size = 20

    try:
        queryset = Content.objects.filter(type='ANIME')

        if search_query:
            queryset = queryset.filter(title__icontains=search_query)

        if genre_filter:
            queryset = queryset.filter(genres__icontains=genre_filter)

        if status_filter:
            queryset = queryset.filter(status__iexact=status_filter)

        # Фільтр за роками
        year_range = request.GET.get('year')
        if year_range:
            try:
                year_from, year_to = map(int, year_range.split('-'))
                queryset = queryset.filter(release_date__year__gte=year_from, release_date__year__lte=year_to)
            except ValueError:
                pass
        if rating_order == 'top':
                    queryset = queryset.order_by('-rating')
        elif rating_order == 'least':
            queryset = queryset.order_by('rating')
        else:
            queryset = queryset.order_by('-release_date')

        paginator = Paginator(queryset, page_size)
        total_pages = paginator.num_pages
        total_results = paginator.count

        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        anime_data = []
        for anime in page_obj:
            # Виправлення для жанрів та студій
            genres = anime.genres if isinstance(anime.genres, list) else anime.genres.split(',') if anime.genres else []
            studios = anime.studios if isinstance(anime.studios, list) else anime.studios.split(',') if anime.studios else []
            
            anime_data.append({
                'id': anime.id,
                'title': anime.title,
                'poster_url': anime.poster_url,
                'release_date': anime.release_date.strftime('%Y-%m-%d') if anime.release_date else None,
                'rating': float(anime.rating) if anime.rating else None,
                'episodes': anime.episodes,
                'status': anime.status,
                'genres': genres,
                'studios': studios,
                'description': anime.description,
                'mal_id': anime.mal_id
            })

        return JsonResponse({
            'results': anime_data,
            'total_results': total_results,
            'total_pages': total_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next()
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def search_autocomplete(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})

    # Пошук у локальній базі даних
    local_results = Content.objects.filter(
        Q(title__icontains=query)
    ).values('id', 'title', 'type', 'poster_url')[:10]

    formatted_results = []
    for item in local_results:
        formatted_results.append({
            'title': item['title'],
            'type': dict(Content.TYPE_CHOICES).get(item['type'], item['type']),
            'url': f"/{item['type'].lower().replace('_', '')}/{item['id']}/",
            'poster_url': item['poster_url'],
            'source': 'local'
        })

    # Якщо результатів мало, шукаємо у зовнішніх API
    if len(formatted_results) < 5:
        try:
            # Пошук у OMDB API
            omdb_results = search_external_apis(query)
            formatted_results.extend(omdb_results[:5])  # Обмежуємо кількість зовнішніх результатів
        except Exception as e:
            print(f"Error searching external APIs: {e}")

    return JsonResponse({'results': formatted_results})


def fetch_omdb_details(imdb_id, api_key):
    details_url = f"http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}"
    try:
        response = requests.get(details_url)
        data = response.json()
        if data.get('Response') == 'True':
            return {
                'Plot': data.get('Plot'),  
                'Year': data.get('Year'),
                'Genre': data.get('Genre'),
                'Director': data.get('Director'),
                'Actors': data.get('Actors'),
                'imdbRating': data.get('imdbRating'),
                'Runtime': data.get('Runtime'),
                'totalSeasons': data.get('totalSeasons')
            }
    except Exception as e:
        print(f"Error fetching OMDB details: {e}")
    return None

def search_external_apis(query):
    results = []
    api_key = settings.OMDB_API_KEY
    
    # Спочатку шукаємо в Jikan API (MyAnimeList) для аніме
    try:
        jikan_url = "https://api.jikan.moe/v4/anime"
        jikan_params = {'q': query, 'limit': 5}
        jikan_response = requests.get(jikan_url, params=jikan_params)
        jikan_data = jikan_response.json()
        
        if 'data' in jikan_data:
            for item in jikan_data['data'][:5]:
                results.append({
                    'title': item['title'],
                    'type': 'Anime',
                    'url': item['url'],
                    'poster_url': item['images']['jpg']['image_url'] if item.get('images', {}).get('jpg', {}).get('image_url') else None,
                    'source': 'jikan',
                    'mal_id': item['mal_id'],
                    'year': item['aired']['prop']['from']['year'] if item.get('aired', {}).get('prop', {}).get('from', {}).get('year') else None,
                    'details': {
                        'score': item.get('score'),
                        'episodes': item.get('episodes'),
                        'status': item.get('status'),
                        'genres': [g['name'] for g in item.get('genres', [])],
                        'studios': [s['name'] for s in item.get('studios', [])]
                    },
                    'description': item.get('synopsis', None),
                    'external_id': f"mal_{item['mal_id']}",
                    'is_anime': True
                })
    except Exception as e:
        print(f"Error fetching anime data: {e}")
    
    # Потім шукаємо в OMDB API, але виключаємо результати, які вже є в Jikan
    seen_titles = {r['title'].lower() for r in results}
    
    # Search movies from OMDB
    movie_url = f"http://www.omdbapi.com/?apikey={api_key}&s={query}&type=movie"
    movie_response = requests.get(movie_url)
    movie_data = movie_response.json()
    
    if movie_data.get('Response') == 'True':
        for item in movie_data.get('Search', [])[:5]:
            if item['Title'].lower() in seen_titles:
                continue
                
            details = fetch_omdb_details(item['imdbID'], api_key)
            is_anime = False
            if details:
                genre = details.get('Genre', '').lower()
                country = details.get('Country', '').lower()
                is_anime = 'animation' in genre and ('japan' in country or 'japanese' in genre)

            if not is_anime:  # Додаємо тільки якщо це не аніме
                results.append({
                    'title': item['Title'],
                    'type': 'Movie',
                    'url': f"https://www.imdb.com/title/{item['imdbID']}/",
                    'poster_url': item['Poster'] if item['Poster'] != 'N/A' else None,
                    'source': 'omdb',
                    'imdb_id': item['imdbID'],
                    'year': item.get('Year', ''),
                    'details': details,
                    'description': details.get('Plot') if details else None,
                    'is_anime': False,
                    'external_id': f"imdb_{item['imdbID']}"
                })
    
    # Search TV shows from OMDB
    tv_url = f"http://www.omdbapi.com/?apikey={api_key}&s={query}&type=series"
    tv_response = requests.get(tv_url)
    tv_data = tv_response.json()
    
    if tv_data.get('Response') == 'True':
        for item in tv_data.get('Search', [])[:5]:
            if item['Title'].lower() in seen_titles:
                continue
                
            details = fetch_omdb_details(item['imdbID'], api_key)
            is_anime = False
            if details:
                genre = details.get('Genre', '').lower()
                country = details.get('Country', '').lower()
                is_anime = 'animation' in genre and ('japan' in country or 'japanese' in genre)

            if not is_anime:  # Додаємо тільки якщо це не аніме
                results.append({
                    'title': item['Title'],
                    'type': 'TV Show',
                    'url': f"https://www.imdb.com/title/{item['imdbID']}/",
                    'poster_url': item['Poster'] if item['Poster'] != 'N/A' else None,
                    'source': 'omdb',
                    'imdb_id': item['imdbID'],
                    'year': item.get('Year', ''),
                    'details': details,
                    'description': details.get('Plot') if details else None,
                    'is_anime': False,
                    'external_id': f"imdb_{item['imdbID']}"
                })
    
    return results


def search_results(request):
    import re

    def safe_int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    def safe_float(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    query = request.GET.get('q', '').strip()

    # Get all local results
    local_results = Content.objects.filter(Q(title__icontains=query))

    # Get external results
    external_results = search_external_apis(query)

    # Combine and deduplicate results
    combined_results = []
    seen_ids = set()
    seen_titles = set()

    # Спочатку додаємо локальні результати
    for item in local_results:
        title_lower = item.title.lower()
        if title_lower not in seen_titles:
            combined_results.append({
                'id': item.id,
                'title': item.title,
                'type': item.get_type_display(),
                'type_icon': 'film' if item.type == 'MOVIE' else 'tv' if item.type == 'TV_SHOW' else 'dragon',
                'poster_url': item.poster_url,
                'release_date': item.release_date,
                'year': item.release_date.year if item.release_date else None,
                'rating': item.rating,
                'episodes': item.episodes,
                'description': item.description,
                'source': 'local'
            })
            seen_ids.add(item.imdb_id if item.imdb_id else item.mal_id if item.mal_id else f"local_{item.id}")
            seen_titles.add(title_lower)

    # Потім обробляємо зовнішні результати
    for item in external_results:
        external_id = item.get('external_id')
        title_lower = item['title'].lower()
        
        if external_id not in seen_ids and title_lower not in seen_titles:
            try:
                # Визначаємо тип контенту
                if item.get('is_anime') or item['type'] == 'Anime':
                    content_type = 'ANIME'
                elif item['type'] == 'Movie':
                    content_type = 'MOVIE'
                elif item['type'] == 'TV Show':
                    content_type = 'TV_SHOW'
                else:
                    content_type = 'MOVIE'
                    
                episodes_raw = item['details'].get('totalSeasons') if item['type'] == 'TV Show' else item['details'].get('episodes')

                content_data = {
                    'type': content_type,
                    'title': item['title'],
                    'poster_url': item['poster_url'],
                    'rating': safe_float(item['details'].get('imdbRating') or item['details'].get('score')) if item['details'] else None,
                    'genres': item['details'].get('Genre', '').split(', ') if item.get('details', {}).get('Genre') else item['details'].get('genres', []),
                    'episodes': safe_int(episodes_raw),
                    'status': item['details'].get('status'),
                    'is_animated': item.get('is_anime', False)
                }

                raw_year = item.get('year', '')
                year_match = re.search(r'\d{4}', str(raw_year))
                release_date = datetime.strptime(year_match.group(), '%Y').date() if year_match else None

                if content_type == 'MOVIE':
                    content_data.update({
                        'imdb_id': item['imdb_id'],
                        'release_date': release_date,
                        'director': item['details'].get('Director'),
                        'description': item.get('description'),
                        'actors': item['details'].get('Actors', '').split(', ') if item.get('details', {}).get('Actors') != 'N/A' else [],
                        'runtime': safe_int(item['details'].get('Runtime', '').split()[0])
                    })
                elif content_type == 'TV_SHOW':
                    content_data.update({
                        'imdb_id': item['imdb_id'],
                        'release_date': release_date,
                        'director': item['details'].get('Director'),
                        'description': item.get('description'),
                        'actors': item['details'].get('Actors', '').split(', ') if item.get('details', {}).get('Actors') != 'N/A' else [],
                        'runtime': safe_int(item['details'].get('Runtime', '').split()[0])
                    })
                elif content_type == 'ANIME':
                    aired_info = item['details'].get('aired', {})
                    aired_from = aired_info.get('from')
                    anime_release = None
                    if aired_from:
                        try:
                            anime_release = datetime.strptime(aired_from.split('T')[0], '%Y-%m-%d').date()
                        except Exception as e:
                            print(f"Error parsing anime release date: {e}")

                    content_data.update({
                        'mal_id': item.get('mal_id'),
                        'imdb_id': item.get('imdb_id'),
                        'release_date': anime_release,
                        'description': item.get('description'),
                        'studios': item['details'].get('studios', [])
                    })

                # Створюємо або оновлюємо контент
                if content_type == 'ANIME':
                    if item.get('mal_id'):
                        content, created = Content.objects.update_or_create(
                            mal_id=item['mal_id'],
                            defaults=content_data
                        )
                    elif item.get('imdb_id'):
                        content, created = Content.objects.update_or_create(
                            imdb_id=item['imdb_id'],
                            defaults=content_data
                        )
                    else:
                        continue  # немає ідентифікаторів
                else:
                    content, created = Content.objects.update_or_create(
                        imdb_id=item['imdb_id'],
                        defaults=content_data
                    )


                combined_results.append({
                    'id': content.id,
                    'title': content.title,
                    'type': content.get_type_display(),
                    'type_icon': 'film' if content.type == 'MOVIE' else 'tv' if content.type == 'TV_SHOW' else 'dragon',
                    'poster_url': content.poster_url,
                    'release_date': content.release_date,
                    'year': content.release_date.year if content.release_date else item.get('year'),
                    'rating': content.rating,
                    'episodes': content.episodes,
                    'source': 'local' if not created else 'external'
                })
                seen_ids.add(external_id)
                seen_titles.add(title_lower)

            except Exception as e:
                print(f"Error saving external content to database: {e}")
                continue

    context = {
        'query': query,
        'combined_results': combined_results,
        'active_page': 'search'
    }

    return render(request, 'search-results.html', context)


# views.py - додати нові функції
