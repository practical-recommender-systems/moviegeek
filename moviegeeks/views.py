import json

from django.shortcuts import render
from moviegeeks.models import Movie, Genre


def index(request):

    #todo: add paginater
    api_key = get_api_key()

    genres = Genre.objects.all().values('name').distinct()
    print(genres)
    movies = Movie.objects.all()[:16]
    context_dict = {'movies': movies,
                    'genres': genres,
                    'api_key': api_key}
    return render(request, 'moviegeek/index.html', context_dict)


def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]

def get_api_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']