from django.http import JsonResponse
from recommender.models import SeededRecs
from builder import DataHelper


def get_association_rules_for(request, content_id, take=5):
    data = SeededRecs.objects.filter(source=content_id)\
        .order_by('confidence')\
        .values('target', 'confidence', 'support')[:take]

    dto = {'result': data}
    return JsonResponse(dict(data=list(data)), safe=False)


def chart(request):
    sql = """SELECT content_id,
                mov.title,
                count(*) as sold
            FROM    collector_log log
            JOIN    moviegeeks_movie mov
            ON      log.content_id = mov.movie_id
            WHERE 	event like 'buy'
            GROUP BY content_id, mov.title
            ORDER BY sold desc
            LIMIT 10
            """

    c = DataHelper.get_query_cursor(sql)
    data = DataHelper.dictfetchall(c)

    return JsonResponse(data, safe=False)
