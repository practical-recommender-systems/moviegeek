import os

import django
import json
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

django.setup()

from recommender.models import MovieDescriptions
NUMBER_OF_PAGES = 15760
start_date = "1970-01-01"


def get_descriptions():

    url = """https://api.themoviedb.org/3/discover/movie?primary_release_date.gte={}&api_key={}&page={}"""
    api_key = get_api_key()

    #MovieDescriptions.objects.all().delete()

    for page in range(1, NUMBER_OF_PAGES):
        formated_url = url.format(start_date, api_key, page)
        print(formated_url)
        r = requests.get(formated_url)
        for film in r.json()['results']:
            id = film['id']
            md = MovieDescriptions.objects.get_or_create(movie_id=id)[0]

            md.imdb_id = get_imdb_id(id)
            md.title = film['title']
            md.description = film['overview']
            md.genres = film['genre_ids']
            if None != md.imdb_id:
                md.save()

        time.sleep(1)

        print("{}: {}".format(page, r.json()))


def save_as_csv():
    url = """https://api.themoviedb.org/3/discover/movie?primary_release_date.gte=2016-01-01
    &primary_release_date.lte=2016-10-22&api_key={}&page={}"""
    api_key = get_api_key()

    file = open('data.json','w')

    films = []
    for page in range(1, NUMBER_OF_PAGES):
        r = requests.get(url.format(api_key, page))
        for film in r.json()['results']:
            f = dict()

            f['id'] = film['id']
            f['imdb_id'] = get_imdb_id(f['id'])
            f['title'] = film['title']
            f['description'] = film['overview']
            f['genres'] = film['genre_ids']
            films.append(f)
        print("{}: {}".format(page, r.json()))

    json.dump(films, file, sort_keys=True, indent=4)

    file.close()


def get_imdb_id(moviedb_id):
    url = """https://api.themoviedb.org/3/movie/{}?api_key={}"""

    r = requests.get(url.format(moviedb_id, get_api_key()))

    json = r.json()
    print(json)
    if 'imdb_id' not in json:
        return ''
    imdb_id = json['imdb_id']
    if imdb_id is not None:
        print(imdb_id)
        return imdb_id[2:]
    else:
        return ''


def get_api_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']


def get_popular_films_for_genre(genre_str):
    film_genres = {'drama': 18, 'action': 28, 'comedy': 35}
    genre = film_genres[genre_str]

    url = """https://api.themoviedb.org/3/discover/movie?sort_by=popularity.desc&with_genres={}&api_key={}"""
    api_key = get_api_key()
    r = requests.get(url.format(genre, api_key))
    print(r.json())
    films = []
    for film in r.json()['results']:
        id = film['id']
        imdb = get_imdb_id(id)
        print("{} {}".format(imdb, film['title']))
        films.append(imdb[2:])
    print(films)


if __name__ == '__main__':
    print("Starting MovieGeeks Population script...")
    get_descriptions()
    # get_popular_films_for_genre('comedy')
    # save_as_csv()
