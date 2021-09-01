import os
import requests
from tqdm import tqdm


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'prs_project.settings')

import django

django.setup()

from moviegeeks.models import Movie, Genre

def delete_db()->None:
    movie_count = Movie.objects.all().count()

    if movie_count > 1:
        Movie.objects.all().delete()
        Genre.objects.all().delete()


def download_movies()->list:

    '''
    Gets latest movie metadata in format movieid::title::genre|genre\n
    :return: response object with data formatted as a list of strings
    '''

    URL = 'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/latest/movies.dat'
    response = requests.get(URL)

    if response:
        data = response.text
        movie_metadata = data.split('\n')
    else:
        print('The latest dataset seems to be empty. Older movie list downloaded.')
        print('Please have a look at https://github.com/sidooms/MovieTweetings/issues and see if there is an issue')
        alternate_url = download_movies(
            'https://raw.githubusercontent.com/sidooms/MovieTweetings/master/snapshots/100K/movies.dat')
        response = requests.get(alternate_url)
        data = response.text
        movie_metadata = data.split('\n')

    return movie_metadata

def populate(movie_metadata)->None:
    '''
    Create movie metadata tables and associate ratings (many-to-many relationship
    :param movie_metadata:
    :return: None
    '''

    for row in tqdm(movie_metadata,mininterval=1, maxinterval=10):
        print(row) # output to Docker logs
        m = row.split(sep="::")
        if len(m) == 3:
            movie_id = m[0]
            movie = Movie.objects.get_or_create(movie_id=movie_id)[0]
            title_and_year = m[1].split(sep="(")
            movie.title = title_and_year[0]
            movie.year = title_and_year[1][:-1]
            genres = m[2]

            if genres:
                for genre in genres.split(sep="|"):
                    g = Genre.objects.get_or_create(name=genre)[0]
                    movie.genres.add(g)
                    g.save()

            movie.save()

if __name__ == '__main__':
    print("Starting metadata script...")

    print("Downloading movie metadata data...")
    movies = download_movies()
    print("Downloaded movie metadata data...")

    print("Truncate movie metdata database...")
    delete_db()

    print("populate movie metadata...")
    populate(movies)

    print("movie metadata populated...")
