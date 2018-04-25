import decimal
import json
import time
from datetime import datetime

from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from gensim import models

from analytics.models import Rating, Cluster
from collector.models import Log
from moviegeeks.models import Movie, Genre
from recommender.models import SeededRecs, Similarity

def index(request):
    context_dict = {}
    return render(request, 'analytics/index.html', context_dict)


def user(request, user_id):
    user_ratings = Rating.objects.filter(user_id=user_id).order_by('-rating')

    movies = Movie.objects.filter(movie_id__in=user_ratings.values('movie_id'))
    log = Log.objects.filter(user_id=user_id).order_by('-created').values()[:20]

    cluster = Cluster.objects.filter(user_id=user_id).first()
    ratings = {r.movie_id: r for r in user_ratings}

    movie_dtos = list()
    sum_rating = 0
    if len(ratings) > 0:
        sum_of_ratings = sum([r.rating for r in ratings.values()])
        user_avg = sum_of_ratings/decimal.Decimal(len(ratings))
    else:
        user_avg = 0

    genres_ratings = {g['name']: 0 for g in Genre.objects.all().values('name').distinct()}
    genres_count = {g['name']: 0 for g in Genre.objects.all().values('name').distinct()}

    for movie in movies:
        id = movie.movie_id

        rating = ratings[id]

        r = rating.rating
        sum_rating += r
        movie_dtos.append(MovieDto(id, movie.title, r))
        for genre in movie.genres.all():

            if genre.name in genres_ratings.keys():
                genres_ratings[genre.name] += r - user_avg
                genres_count[genre.name] += 1

    max_value = max(genres_ratings.values())
    max_value = max(max_value, 1)
    max_count = max(genres_count.values())
    max_count = max(max_count, 1)

    genres = []
    for key, value in genres_ratings.items():
        genres.append((key, 'rating', value/max_value))
        genres.append((key, 'count', genres_count[key]/max_count))

    cluster_id = cluster.cluster_id if cluster else 'Not in cluster'

    context_dict = {
        'user_id': user_id,
        'avg_rating': user_avg,
        'film_count': len(ratings),
        'movies': sorted(movie_dtos, key=lambda item: -float(item.rating))[:15],
        'genres': genres,
        'logs': list(log),
        'cluster': cluster_id,
        'api_key': get_api_key(),

    }

    print(genres)
    return render(request, 'analytics/user.html', context_dict)


def content(request, content_id):
    print(content_id)
    movie = Movie.objects.filter(movie_id=content_id).first()
    user_ratings = Rating.objects.filter(movie_id=content_id)
    ratings = user_ratings.values('rating')
    logs = Log.objects.filter(content_id=content_id).order_by('-created').values()[:20]
    association_rules = SeededRecs.objects.filter(source=content_id).values('target', 'type')

    print(content_id, " rat:", ratings)

    movie_title = 'No Title'
    agv_rating = 0
    genre_names = []
    if movie is not None:
        movie_genres = movie.genres.all() if movie is not None else []
        genre_names = list(movie_genres.values('name'))

        ratings = list(r['rating'] for r in ratings)
        agv_rating = sum(ratings)/len(ratings)
        movie_title = movie.title

    context_dict = {
        'title': movie_title,
        'avg_rating': "{:10.2f}".format(agv_rating),
        'genres': genre_names,
        'api_key': get_api_key(),
        'association_rules': association_rules,
        'content_id': str(content_id),
        'rated_by': user_ratings,
        'logs': logs,
        'number_users': len(ratings)}

    return render(request, 'analytics/content_item.html', context_dict)

def lda(request):
    lda = models.ldamodel.LdaModel.load('./lda/model.lda')

    for topic in lda.print_topics():
        print("topic {}: {}".format(topic[0], topic[1]))

    context_dict = {
        "topics": lda.print_topics(),
        "number_of_topics": lda.num_topics

    }
    return render(request, 'analytics/lda_model.html', context_dict)


def cluster(request, cluster_id):

    members = Cluster.objects.filter(cluster_id=cluster_id)
    member_ratings = Rating.objects.filter(user_id__in=members.values('user_id'))
    movies = Movie.objects.filter(movie_id__in=member_ratings.values('movie_id'))

    ratings = {r.movie_id: r for r in member_ratings}

    sum_rating = 0

    genres = {g['name']: 0 for g in Genre.objects.all().values('name').distinct()}
    for movie in movies:
        id = movie.movie_id
        rating = ratings[id]

        r = rating.rating
        sum_rating += r

        for genre in movie.genres.all():

            if genre.name in genres.keys():
                genres[genre.name] += r

    max_value = max(genres.values())
    genres = {key: value / max_value for key, value in genres.items()}

    context_dict = {
        'genres': genres,
        'members':  sorted([m.user_id for m in members]),
        'cluster_id': cluster_id,
        'members_count': len(members),
    }

    return render(request, 'analytics/cluster.html', context_dict)

def get_genres():
    return Genre.objects.all().values('name').distinct()

class MovieDto(object):
    def __init__(self, movie_id, title, rating):
        self.movie_id = movie_id
        self.title = title
        self.rating = rating


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

def clusters(request):

    clusters_w_membercount = (Cluster.objects.values('cluster_id')
                              .annotate(member_count=Count('user_id'))
                              .order_by('cluster_id'))

    context_dict = {
        'cluster': list(clusters_w_membercount)
    }
    return JsonResponse(context_dict, safe=False)


def similarity_graph(request):

    sim = Similarity.objects.all()[:10000]
    source_set = [s.source for s in sim]
    nodes = [{"id":s, "label": s} for s in set(source_set)]
    edges = [{"from": s.source, "to": s.target} for s in sim]

    print(nodes)
    print(edges)
    context_dict = {
        "nodes": nodes,
        "edges": edges
    }
    return render(request, 'analytics/similarity_graph.html', context_dict)

def get_api_key():
    # Load credentials
    cred = json.loads(open(".prs").read())
    return cred['themoviedb_apikey']


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
                            (case when c.conversion = 1 then \'Buy\' else \'No Buy\' end) as conversion,
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


def ratings_distribution(request):
    cursor = connection.cursor()
    cursor.execute("""
    select rating, count(1) as count_items
    from analytics_rating
    group by rating
    order by rating
    """)
    data = dictfetchall(cursor)
    for d in data:
        d['rating'] = round(d['rating'])

    return JsonResponse(data, safe=False)


def dictfetchall(cursor):
    " Returns all rows from a cursor as a dict "
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
        ]

class movie_rating():
    title = ""
    rating = 0

    def __init__(self, title, rating):
        self.title = title
        self.rating = rating

def monthdelta(date, delta):
    m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
    if not m: m = 12
    d = min(date.day, [31,
                       29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date.replace(day=d, month=m, year=y)
