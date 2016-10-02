from django.shortcuts import render
from django.db.models import Count
from django.http import JsonResponse
from django.db import connection

from datetime import datetime
import time

from collector.models import Log
from moviegeeks.models import Movie, Genre
from analytics.models import Rating, Cluster
from recommender.models import SeededRecs, Similarity
from gensim import corpora, models

def index(request):
    context_dict = {}
    return render(request, 'analytics/index.html', context_dict)


def user(request, user_id):
    user_ratings = Rating.objects.filter(user_id=user_id).order_by('-rating')
    print(user_ratings.values('movie_id'))
    movies = Movie.objects.filter(movie_id__in=user_ratings.values('movie_id'))
    log = Log.objects.filter(user_id=user_id).order_by('-created').values()[:20]

    cluster = Cluster.objects.filter(user_id=user_id).first()
    ratings = {r.movie_id: r for r in user_ratings}
    print(ratings)
    print(movies)
    movie_dtos = list()
    sum_rating = 0


    genres = {g['name']: 0 for g in Genre.objects.all().values('name').distinct()}
    for movie in movies:
        id = movie.movie_id

        rating = ratings[id]

        r = rating.rating
        sum_rating += r
        movie_dtos.append(MovieDto(id, movie.title, r))

        for genre in movie.genres.all():

            if genre.name in genres.keys():
                genres[genre.name] += r

    max_value = max(genres.values())
    max_value = max(max_value,1)

    genres = {key: value / max_value for key, value in genres.items()}
    cluster_id = cluster.cluster_id if cluster else 'Not in cluster'
    context_dict = {
        'user_id': user_id,
        'avg_rating': 0 if len(movie_dtos) == 0 else float(sum_rating) / float(len(movie_dtos)),
        'movies': movie_dtos,
        'genres': genres,
        'logs': list(log),
        'cluster': cluster_id,

    }
    return render(request, 'analytics/user.html', context_dict)


def content(request, content_id):
    movie = Movie.objects.filter(movie_id=content_id).first()
    ratings = Rating.objects.filter(movie_id=content_id).values('rating')
    logs = Log.objects.filter(content_id=content_id).order_by('-created').values()[:20]
    association_rules = SeededRecs.objects.filter(source=content_id).values('target', 'type')

    genres = movie.genres.values()

    ratings = list(r['rating'] for r in ratings)
    agv_rating = sum(ratings)/len(ratings)
    context_dict = {
        'title': movie.title,
        'avg_rating': "{:10.2f}".format(agv_rating),
        'genres': [g['name'] for g in genres],
        'association_rules': association_rules,
        'content_id': content_id,
        'logs': logs,
    }

    return render(request, 'analytics/content_item.html', context_dict)

def lda(request):
    lda = models.ldamodel.LdaModel.load('./../pickled_model.lda')

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
        'members':  [m.user_id for m in members],
        'cluster_id': cluster_id,
        'members_count': len(members),
    }

    return render(request, 'analytics/cluster.html', context_dict)

class MovieDto(object):
    def __init__(self, movie_id, title, rating):
        self.movie_id = movie_id
        self.title = title
        self.rating = rating


def top_content(request):

    #todo: use django ORM instead of raw sql.

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

    clusters_w_membercount = Cluster.objects.values('cluster_id').annotate(member_count=Count('user_id'))

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
    # context_dict = {
    #     "nodes": [
    #         {"id": 2, "label": 'Node 2'},
    #         {"id": 3, "label": 'Node 3'},
    #         {"id": 4, "label": 'Node 4'},
    #         {"id": 5, "label": 'Node 5'},
    #         {"id": 1, "label": 'Node 1'},
    #     ],
    #     "edges": [
    #         {"from": 1, "to": 3},
    #         {"from": 1, "to": 2},
    #         {"from": 2, "to": 4},
    #         {"from": 2, "to": 5},
    #         {"from": 1, "to": 5}
    #     ]
    #
    # }
    return render(request, 'analytics/similarity_graph.html', context_dict)


###### -------------- old code ------------------




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
