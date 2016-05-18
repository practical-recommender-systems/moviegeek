import json

from django.shortcuts import render
from moviegeeks.models import Movie


def index(request):

    #todo: add paginater
    api_key = get_api_key()

    movies = Movie.objects.all()[:16]
    context_dict = {'movies': movies,
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