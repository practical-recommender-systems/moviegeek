import uuid, random
import json

from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from moviegeeks.models import Movie, Genre

@ensure_csrf_cookie
def index(request):

    genre_selected = request.GET.get('genre')

    api_key = get_api_key()

    if genre_selected:
        selected = Genre.objects.filter(name=genre_selected)[0]
        movies = selected.movies.order_by('-year', 'movie_id')
    else:
        movies = Movie.objects.order_by('-year', 'movie_id')

    genres = get_genres()

    page_number = request.GET.get("page", 1)
    page, page_end, page_start = handle_pagination(movies,
                                                   page_number)

    context_dict = {'movies': page,
                    'genres': genres,
                    'api_key': api_key,
                    'session_id': session_id(request),
                    'user_id': user_id(request),
                    'pages': range(page_start, page_end),
                    }

    return render(request, 'moviegeek/index.html', context_dict)


def handle_pagination(movies, page_number):

    paginate_by = 18

    paginator = Paginator(movies, paginate_by)

    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page_number = 1
        page = paginator.page(page_number)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page_number = int(page_number)
    page_start = 1 if page_number < 5 else page_number - 3
    page_end = 6 if page_number < 5 else page_number + 2
    return page, page_end, page_start


@ensure_csrf_cookie
def genre(request, genre_id):

    if genre_id:
        selected = Genre.objects.filter(name=genre_id)[0]
        movies = selected.movies.all().order_by('-year')
    else:
        movies = Movie.objects.all().order_by('-year')

    genres = get_genres()

    page_number = request.GET.get("page", 1)
    page, page_end, page_start = handle_pagination(movies,
                                                   page_number)

    print(genres)
    context_dict = {'movies': page,
                    'genres': genres,
                    'api_key': get_api_key(),
                    'session_id': session_id(request),
                    'user_id': user_id(request),
                    'pages': range(page_start, page_end),
                    }

    return render(request, 'moviegeek/index.html', context_dict)


def detail(request, movie_id):
    api_key = get_api_key()
    genres = get_genres()
    movie = Movie.objects.filter(movie_id=movie_id).first()
    genre_names = []

    if movie is not None :
        movie_genres = movie.genres.all() if movie is not None else []
        genre_names = list(movie_genres.values('name'))

    context_dict = {'movie_id': movie_id,
                    'genres': genres,
                    'movie_genres': genre_names,
                    'api_key': api_key,
                    'session_id': session_id(request),
                    'user_id': user_id(request)}

    return render(request, 'moviegeek/detail.html', context_dict)


def search_for_movie(request):

    search_term = request.GET.get('q', None)

    if search_term is None:
        return redirect('/movies/')

    mov = Movie.objects.filter(title__startswith=search_term)

    genres = get_genres()

    api_key = get_api_key()

    context_dict = {
        'genres': genres,
        'movies': mov.values(),
        'api_key': api_key,
    }
    print(list(mov))

    return render(request, 'moviegeek/search_result.html', context_dict)


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
    user_id = request.GET.get("user_id")

    if user_id:
        request.session['user_id'] = user_id

    if not "user_id" in request.session:
        request.session['user_id'] = random.randint(10000000000, 90000000000)

    print("ensured id: ", request.session['user_id'] )
    return request.session['user_id']

