import os
import urllib.request
from tqdm import tqdm

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

import django

django.setup()

from moviegeeks.models import Movie, Genre


def create_movie(movie_id, title, genres):
    movie = Movie.objects.get_or_create(movie_id=movie_id)[0]

    title_and_year = title.split(sep="(")

    movie.title = title_and_year[0]
    movie.year = title_and_year[1][:-1]

    if genres:
        for genre in genres.split(sep="|"):
            g = Genre.objects.get_or_create(name=genre)[0]
            movie.genres.add(g)
            g.save()

    movie.save()

    return movie


def download_movies():
    URL = 'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/movies.dat'
    response = urllib.request.urlopen(URL)
    data = response.read()
    return data.decode('utf-8')


def delete_db():
    print('truncate db')
    Movie.objects.all().delete()
    Genre.objects.all().delete()
    print('finished truncate db')


def populate():

    movies = download_movies()

    print('movie data downloaded')

    for movie in tqdm(movies.split(sep="\n")):
        m = movie.split(sep="::")
        if len(m) == 3:

            create_movie(m[0], m[1], m[2])


if __name__ == '__main__':
    print("Starting MovieGeeks Population script...")
    delete_db()
    populate()