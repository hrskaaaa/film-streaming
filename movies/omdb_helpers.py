# omdb_helpers.py
import datetime
import requests

def fetch_omdb_details(imdb_id, api_key):
    detail_url = f"http://www.omdbapi.com/?apikey={api_key}&i={imdb_id}"
    detail_response = requests.get(detail_url)
    detail_data = detail_response.json()

    if detail_data.get('Response') != 'True':
        return None

    rating = None
    if 'imdbRating' in detail_data and detail_data['imdbRating'] != 'N/A':
        try:
            rating = float(detail_data['imdbRating'])
        except:
            pass

    release_date = None
    if 'Released' in detail_data and detail_data['Released'] != 'N/A':
        try:
            release_date = datetime.datetime.strptime(detail_data['Released'], '%d %b %Y').date()
        except:
            pass

    runtime = None
    if 'Runtime' in detail_data and detail_data['Runtime'] != 'N/A':
        try:
            runtime = int(detail_data['Runtime'].split()[0])
        except:
            pass

    genres = [genre.strip() for genre in detail_data.get('Genre', '').split(',') if genre.strip()]
    actors = [actor.strip() for actor in detail_data.get('Actors', '').split(',') if actor.strip()]
    is_animated = 'Animation' in genres

    return {
        'rating': rating,
        'release_date': release_date,
        'runtime': runtime,
        'genres': genres,
        'actors': actors,
        'director': detail_data.get('Director') if detail_data.get('Director', 'N/A') != 'N/A' else None,
        'is_animated': is_animated
    }
