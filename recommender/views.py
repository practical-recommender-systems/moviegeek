from decimal import Decimal
from math import sqrt

import numpy as np
import operator
from django.http import JsonResponse
from django.db.models import Avg, Count

from analytics.models import Rating
from collector.models import Log
from recommender.models import SeededRecs, Recs, MovieDescriptions, Similarity
from builder import data_helper

from gensim import models, corpora, similarities


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

    c = data_helper.get_query_cursor(sql)
    data = data_helper.dictfetchall(c)

    return JsonResponse(data, safe=False)


def pearson(users, this_user, that_user):
    if this_user in users and that_user in users:
        this_user_avg = sum(users[this_user].values()) / len(users[this_user].values())
        that_user_avg = sum(users[that_user].values()) / len(users[that_user].values())

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
            return dividend / Decimal(sqrt(divisor_a) * sqrt(divisor_b))

    return 0


def jaccard(users, this_user, that_user):
    if this_user in users and that_user in users:
        intersect = set(users[this_user].keys()) & set(users[that_user].keys())
        union = set(users[this_user].keys()) | set(users[that_user].keys())

        return len(intersect) / Decimal(len(union))
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

        if s > 0.5:
            similarity[user['user_id']] = round(s, 2)
    topn = sorted(similarity.items(), key=operator.itemgetter(1), reverse=True)[:10]

    data = {
        'user_id': user_id,
        'num_movies_rated': len(ratings),
        'type': type,
        'topn': topn,
        'similarity': topn,
    }

    return JsonResponse(data, safe=False)


def similar_content(request, content_id, num = 6):
    lda = models.ldamodel.LdaModel.load('./lda/model.lda')

    dictionary = corpora.Dictionary.load('./lda/dict.lda')

    corpus = corpora.MmCorpus('./lda/corpus.mm')
    content_sims = dict()

    md = MovieDescriptions.objects.filter(imdb_id=content_id).first()


    if md is not None:
        index = similarities.MatrixSimilarity.load('./lda/index.lda')

        lda_vector = lda[corpus[int(md.lda_vector)]]
        sims = index[lda_vector]

        sorted_sims = sorted(enumerate(sims), key=lambda item: -item[1])[:num]

        movies = get_movie_ids(sorted_sims, corpus, dictionary)

        for movie in movies:
            target = movie['target']
            if target in content_sims.keys():
                if movie['sim'] > content_sims[target]['sim']:
                    content_sims[target] = movie
            else:
                content_sims[target] = movie

        sorted_items = sorted(content_sims.values(), key=lambda item: -float(item['sim']))[:num]

        data = {
            'source_title': md.title,
            'source_id': md.imdb_id,
            'data': sorted_items
        }

        return JsonResponse(data, safe=False)


def recs_funksvd(request, user_id, num = 6):
    recs = Recs.objects.filter(user='u' + user_id)

    top_num = sorted(recs.values(), key=lambda rec: rec['rating'])

    data = {
        'user_id': user_id,
        'data': top_num[:num]
    }
    return JsonResponse(data, safe=False)


def recs_cb(request, user_id, num = 6):
    ratings = Rating.objects.filter(user_id=user_id)

    lda = models.ldamodel.LdaModel.load('./lda/model.lda')

    dictionary = corpora.Dictionary.load('./lda/dict.lda')

    corpus = corpora.MmCorpus('./lda/corpus.mm')

    content_sims = dict()
    for rating in ratings:
        md = MovieDescriptions.objects.filter(imdb_id=rating.movie_id).first()
        if md is not None:
            index = similarities.MatrixSimilarity.load('./lda/index.lda')

            lda_vector = lda[corpus[int(md.lda_vector)]]
            sims = index[lda_vector]
            sorted_sims = sorted(enumerate(sims), key=lambda item: -item[1])[:num]
            movies = get_movie_ids(sorted_sims, corpus, dictionary)

            for movie in movies:
                target = movie['target']
                if target in content_sims.keys():
                    if movie['sim'] > content_sims[target]['sim']:
                        content_sims[target] = movie
                else:
                    content_sims[target] = movie

    sorted_items = sorted(content_sims.values(), key=lambda item: -float(item['sim']))[:num]

    data = {
        'user_id': user_id,
        'data': sorted_items
    }

    return JsonResponse(data, safe=False)


def recs_cf(request, user_id, num = 6):
    active_user_items = Rating.objects.filter(user_id=user_id)

    movie_ids = {movie.movie_id: movie.rating for movie in active_user_items}
    #todo: get similar items
    candidate_items = Similarity.objects.filter(source__in=movie_ids.keys())
    candidate_items = candidate_items.distinct().order_by('-similarity')

    #todo: calculate predictions
    recs = dict()
    print(candidate_items)
    for candiate in candidate_items:
        target = candiate.target

        if target not in movie_ids:
            pre = 0

            rated_items = [i for i in candidate_items if i.target == target]

            for sim_item in [i for i in candidate_items if i.target == target]:
                r = movie_ids[sim_item.source]
                pre += sim_item.similarity * r

            recs[target] = {'prediction': pre/len(rated_items),
                            'sim_items': [r.source for r in rated_items]}

    sorted_items = sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]

    data = {'user_id': user_id,
            'data': sorted_items}

    return JsonResponse(data, safe=False)


def get_movie_ids(sorted_sims, corpus, dictionary):
    ids = [s[0] for s in sorted_sims]
    movies = MovieDescriptions.objects.filter(lda_vector__in=ids)

    return [{"target": movies[i].imdb_id,
             "title": movies[i].title,
             "sim": str(sorted_sims[i][1])} for i in range(len(movies))]


def lda2array(lda_vector, len):
    vec = np.zeros(len)
    for coor in lda_vector:
        if coor[0] > 1270:
            print("auc")
        vec[coor[0]] = coor[1]

    return vec
