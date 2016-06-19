from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from django.http import HttpResponse
from django.template.loader import get_template
from django.template.context import RequestContext
from django.db import connection

from datetime import datetime
import time

from collector.models import Log
from moviegeeks.models import Movie
from analytics.models import Rating


def index(request):
    context_dict = {}
    return render(request, 'analytics/index.html', context_dict)


def user(request, user_id):
    user_ratings = Rating.objects.filter(user_id=user_id).order_by('-rating')
    movies = Movie.objects.filter(movie_id__in=user_ratings.values('movie_id'))
    log = Log.objects.filter(user_id=user_id).values()[:20]
    movie_dtos = list()
    sum_rating = 0

    genres = dict()

    for movie in movies:
        id = movie.movie_id

        for genre in movie.genres.all():

            if genre.name in genres.keys():
                genres[genre.name] += 1
            else:
                genres[genre.name] = 1

        for rating in user_ratings:

            # todo: rating.movieid is an integer
            if rating.movie_id == id:
                r = rating.rating
                sum_rating += r
                movie_dtos.append(MovieDto(id, movie.title, r))

                for genre in movie.genres.all():

                    if genre.name in genres.keys():
                        genres[genre.name] += r
                    else:
                        genres[genre.name] = r

    context_dict = {
        'user_id': user_id,
        'avg_rating': 0 if len(movie_dtos) == 0 else float(sum_rating) / float(len(movie_dtos)),
        'movies': movie_dtos,
        'genres': genres,
        'logs': list(log),

    }
    return render(request, 'analytics/user.html', context_dict)


def content(request, content_id):

    context_dict = {
        'content_id': content_id,
    }

    return render(request, 'analytics/content.html', context_dict)

def user_taste(request, user_id):
    genres = dict()

    context_dict = {
        'user_id': user_id,
        'genres': genres,
    }

    return JsonResponse()


def statistics(request):
    user_by_moviecount = Rating.objects.values('user_id').annotate(movie_count=Count('movie_id')).order_by(
        '-movie_count')


class MovieDto(object):
    def __init__(self, movie_id, title, rating):
        self.movie_id = movie_id
        self.title = title
        self.rating = rating


###### -------------- old code ------------------


def user2(request, userid):
    context = RequestContext(request, {
        'user': userid,
    })

    return render(request, '/analytics/user.html', context)


def top_content(request):
    cursor = connection.cursor()
    cursor.execute('SELECT \
                        content_id,\
                        mov.title,\
                        count(*) as sold\
                    FROM    collector_log log\
                    JOIN    moviegeeks_movie mov ON CAST(log.content_id AS INTEGER) = CAST(mov.movie_id AS INTEGER)\
                    WHERE 	event like \'buy\' \
                    GROUP BY content_id, mov.title \
                    ORDER BY sold desc \
                    LIMIT 10 \
        ')

    data = dictfetchall(cursor)
    return JsonResponse(data, safe=False)


def get_user_statistics(request, userid):
    date_timestamp = time.strptime(request.GET["date"], "%Y-%m-%d")

    end_date = datetime.fromtimestamp(time.mktime(date_timestamp))
    start_date = monthdelta(end_date, -1)

    sessions_with_conversions = Log.objects.filter(created__range=(start_date, end_date), event='buy', user_id=userid) \
        .values('sessionId').distinct()
    buy_data = Log.objects.filter(created__range=(start_date, end_date), event='buy', user_id=userid) \
        .values('event', 'user_id', 'content_id', 'sessionId')
    sessions = Log.objects.filter(created__range=(start_date, end_date), user_id=userid) \
        .values('sessionId').distinct()

    if len(sessions) == 0:
        conversions = 0
    else:
        conversions = (len(sessions_with_conversions) / len(sessions)) * 100
        conversions = round(conversions)

    return JsonResponse(
        {"items_bought": len(buy_data),
         "conversions": conversions,
         "sessions": len(sessions)})


def get_statistics(request):
    date_timestamp = time.strptime(request.GET["date"], "%Y-%m-%d")

    end_date = datetime.fromtimestamp(time.mktime(date_timestamp))

    start_date = monthdelta(end_date, -1)

    print("getting statics for ", start_date, " and ", end_date)

    sessions_with_conversions = Log.objects.filter(created__range=(start_date, end_date), event='buy') \
        .values('session_id').distinct()
    buy_data = Log.objects.filter(created__range=(start_date, end_date), event='buy') \
        .values('event', 'user_id', 'content_id', 'session_id')
    visitors = Log.objects.filter(created__range=(start_date, end_date)) \
        .values('user_id').distinct()
    sessions = Log.objects.filter(created__range=(start_date, end_date)) \
        .values('session_id').distinct()

    if len(sessions) == 0:
        conversions = 0
    else:
        conversions = (len(sessions_with_conversions) / len(sessions)) * 100
        conversions = round(conversions)

    return JsonResponse(
        {"items_sold": len(buy_data),
         "conversions": conversions,
         "visitors": len(visitors),
         "sessions": len(sessions)})


def events_on_conversions(request):
    cursor = connection.cursor()
    cursor.execute('''select
                            (case when c.conversion = 1 then \'buy\' else \'no buy\' end) as conversion,
                            event,
                                count(*) as count_items
                              FROM
                                    collector_log log
                              LEFT JOIN
                                (SELECT session_id, 1 as conversion
                                 FROM   collector_log
                                 WHERE  event=\'buy\') c
                                 ON     log.session_id = c.session_id
                               GROUP BY conversion, event''')
    data = dictfetchall(cursor)
    print(data)
    return JsonResponse(data, safe=False)


def dictfetchall(cursor):
    " Returns all rows from a cursor as a dict "
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]


def user_evidence(request, userid):
    cursor = connection.cursor()
    cursor.execute('SELECT \
                        user_id, \
                        content_id,\
                        mov.title,\
                        count(case when event = \'buy\' then 1 end) as buys,\
                        count(case when event = \'details\' then 1 end) as details,\
                        count(case when event = \'moredetails\' then 1 end) as moredetails\
                    FROM \
                      public."collector_log" log\
                    JOIN    public.movies mov \
                    ON CAST(log.content_id AS VARCHAR(50)) = CAST(mov.id AS VARCHAR(50))\
                    WHERE\
                        user_id = \'%s\'\
                    group by log.user_id, log.content_id, mov.title\
                    order by log.user_id, log.content_id' % userid)
    data = dictfetchall(cursor)
    movie_ratings = Builder.generate_implicit_ratings(data)
    Builder.save_ratings(userid, movie_ratings)

    return JsonResponse(movie_ratings, safe=False)


class movie_rating():
    title = ""
    rating = 0

    def __init__(self, title, rating):
        self.title = title
        self.rating = rating


def top_content_by_eventtype(request):
    event_type = request.GET.get_template('eventtype', 'buy')

    data = Event.objects.filter(event=event_type) \
               .values('content_id') \
               .annotate(count_items=Count('user_id')) \
               .order_by('-count_items')[:10]
    return JsonResponse(list(data), safe=False)


def monthdelta(date, delta):
    m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
    if not m: m = 12
    d = min(date.day, [31,
                       29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date.replace(day=d, month=m, year=y)

