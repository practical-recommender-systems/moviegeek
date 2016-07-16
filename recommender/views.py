from decimal import Decimal
from math import sqrt

from django.http import JsonResponse
from django.db.models import Avg, Count

from analytics.models import Rating
from collector.models import Log
from recommender.models import SeededRecs
from builder import DataHelper


def get_association_rules_for(request, content_id, take=6):
    data = SeededRecs.objects.filter(source=content_id) \
               .order_by('confidence') \
               .values('target', 'confidence', 'support')[:take]

    return JsonResponse(dict(data=list(data)), safe=False)


def recs_using_association_rules(request, user_id, take=6):
    events = Log.objects.filter(user_id=user_id) \
                 .order_by('created') \
                 .values('content_id')[:20]

    seeds = set([event['content_id'] for event in events])

    print(seeds)

    rules = SeededRecs.objects.filter(source__in=seeds) \
        .exclude(target__in=seeds) \
        .values('target') \
        .annotate(confidence=Avg('confidence')) \
        .order_by('-confidence')

    recs = [{'id': '{0:07d}'.format(int(rule['target'])),
             'confidence': rule['confidence']} for rule in rules]

    return JsonResponse(dict(data=list(recs[:take])))


def chart(request, take=10):
    sql = """SELECT content_id,
                mov.title,
                count(*) as sold
            FROM    collector_log log
            JOIN    moviegeeks_movie mov
            ON      log.content_id = mov.movie_id
            WHERE 	event like 'buy'
            GROUP BY content_id, mov.title
            ORDER BY sold desc
            LIMIT {}
            """.format(take)

    c = DataHelper.get_query_cursor(sql)
    data = DataHelper.dictfetchall(c)

    return JsonResponse(data, safe=False)


def pearson(users, this_user, that_user):
    if this_user in users and that_user in users:
        this_user_avg = sum(users[this_user].values())/len(users[this_user].values())
        that_user_avg = sum(users[that_user].values())/len(users[that_user].values())

        all_movies = set(users[this_user].keys()) & set(users[that_user].keys())

        dividend = 0
        divisor_a = 0
        divisor_b = 0
        for movie in all_movies:

            if movie in users[this_user].keys() and movie in users[that_user].keys():
                nr_a = users[this_user][movie] - this_user_avg
                nr_b = users[that_user][movie] - that_user_avg
                dividend += (nr_a) * (nr_b)
                divisor_a += pow(nr_a, 2)
                divisor_b += pow(nr_b, 2)

        divisor = Decimal(sqrt(divisor_a) * sqrt(divisor_b))
        if divisor != 0:
            return dividend/Decimal(sqrt(divisor_a) * sqrt(divisor_b))

    return 0


def jaccard(users, this_user, that_user):
    if this_user in users and that_user in users:
        intersect = set(users[this_user].keys()) & set(users[that_user].keys())
        union = set(users[this_user].keys()) | set(users[that_user].keys())

        return len(intersect)/Decimal(len(union))
    else:
        return 0

def similar_users(request, user_id, type):

    min = request.GET.get('min', 1)

    ratings = Rating.objects.filter(user_id=user_id)
    sim_users = Rating.objects.filter(movie_id__in=ratings.values('movie_id')) \
        .values('user_id') \
        .annotate(intersect=Count('user_id')).filter(intersect__gt=min)

    dataset = Rating.objects.filter(user_id__in=sim_users.values('user_id'))

    users = {u['user_id']: {} for u in sim_users}

    for row in dataset:
        if row.user_id in users.keys():
            users[row.user_id][row.movie_id] = row.rating

    similarity = dict()

    switcher = {
        'jaccard': jaccard,
        'pearson': pearson,

    }

    for user in sim_users:

        func = switcher.get(type, lambda: "nothing")
        s = func(users, int(user_id), int(user['user_id']))

        if s > 0.2:
            similarity[user['user_id']] = s

    data = {
        'user_id': user_id,
        'num_movies_rated': len(ratings),
        'type': type,
        'similarity': similarity,
    }
    return JsonResponse(data, safe=False)
