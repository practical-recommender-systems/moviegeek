from django.http import JsonResponse
from django.db.models import Avg

from collector.models import Log
from recommender.models import SeededRecs
from builder import DataHelper


def get_association_rules_for(request, content_id, take=6):
    data = SeededRecs.objects.filter(source=content_id)\
        .order_by('confidence')\
        .values('target', 'confidence', 'support')[:take]

    return JsonResponse(dict(data=list(data)), safe=False)


def recs_using_association_rules(request, user_id, take=6):
    events = Log.objects.filter(user_id=user_id)\
                        .order_by('created')\
                        .values('content_id')[:20]

    seeds = set([event['content_id'] for event in events])

    print(seeds)

    rules = SeededRecs.objects.filter(source__in=seeds)\
                              .values('target')\
                              .annotate(confidence=Avg('confidence'))\
                              .order_by('-confidence')

    recs = [{'id':'{0:07d}'.format(int(rule['target'])),
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

