from django.shortcuts import render

from moviegeeks.models import Movie
from analytics.models import Rating

def index(request):

    context_dict = {}
    return render(request, 'analytics/index.html', context_dict)


def user(request, user_id):

    user_ratings = Rating.objects.filter(user_id=user_id).order_by('-rating')
    movies = Movie.objects.filter(movie_id__in=user_ratings.values('movie_id'))

    movie_dtos = list()
    sum_rating = 0
    for movie in movies.values():
        id = movie['movie_id']
        for rating in user_ratings.values():

            #todo: rating.movieid is an integer
            if rating['movie_id'] == int(id):
                r = rating['rating']
                sum_rating += r
                movie_dtos.append(Movie_dto(id, movie['title'], r))

    context_dict = {
        'user_id': user_id,
        'avg_rating': sum_rating/float(len(movie_dtos)),
        'movies': movie_dtos,

    }
    return render(request, 'analytics/user.html', context_dict)

def statistics(request):

    user_by_moviecount = Rating.objects.values('user_id').annotate(movie_count=count('movie_id')).order_by('-movie_count')


class Movie_dto(object):

    def __init__(self, movie_id, title, rating):
        self.movie_id = movie_id
        self.title = title
        self.rating = rating

