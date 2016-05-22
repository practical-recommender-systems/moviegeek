import uuid, random
import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from moviegeeks.models import Movie, Genre

@ensure_csrf_cookie
def index(request):
    genre_selected = request.GET.get('genre')

    # todo: add paginater

    api_key = get_api_key()

    if genre_selected:
        selected = Genre.objects.filter(name=genre_selected)[0]
        movies = selected.movies.all()[:16]
    else:
        movies = Movie.objects.all()[:16]

    genres = get_genres()

    print(genres)
    context_dict = {'movies': movies,
                    'genres': genres,
                    'api_key': api_key,
                    'session_id': session_id(request),
                    'user_id': user_id(request)}

    return render(request, 'moviegeek/index.html', context_dict)


def detail(request, movie_id):
    api_key = get_api_key()
    genres = get_genres()
    context_dict = {'movie_id': movie_id,
                    'genres': genres,
                    'api_key': api_key,
                    'session_id': session_id(request),
                    'user_id': user_id(request)}

    return render(request, 'moviegeek/detail.html', context_dict)


def dictfetchall(cursor):
    """Returns all rows from a cursor as a dict"""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]


def get_api_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']


def get_genres():
    return Genre.objects.all().values('name').distinct()


def session_id(request):
    if not "session_id" in request.session:
        request.session["session_id"] = str(uuid.uuid1())

    return request.session["session_id"]


def user_id(request):
    if not "user_id" in request.session:
        request.session['user_id'] = random.randint(1000000000000, 9000000000000)

    print("ensured id: ", request.session['user_id'] )
    return request.session['user_id']
