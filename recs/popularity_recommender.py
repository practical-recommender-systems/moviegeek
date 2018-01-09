from decimal import Decimal

from analytics.models import Rating
from collector.models import Log
from recs.base_recommender import base_recommender
from django.db.models import Count
from django.db.models import Q
from django.db.models import Avg

class PopularityBasedRecs(base_recommender):

    def predict_score(self, user_id, item_id):
        avg_rating = Rating.objects.filter(~Q(user_id=user_id) &
                                           Q(movie_id=item_id)).values('movie_id').aggregate(Avg('rating'))
        return avg_rating['rating__avg']

    @staticmethod
    def recommend_items_from_log(num=6):
        items = Log.objects.values('content_id')
        items = items.filter(event='buy').annotate(Count('user_id'))

        sorted_items = sorted(items, key=lambda item: -float(item['user_id__count']))

        return sorted_items[:num]

    def recommend_items(self, user_id, num=6):
        pop_items = Rating.objects.filter(~Q(user_id=user_id)).values('movie_id').annotate(Count('user_id'),
                                                                                           Avg('rating'))
        sorted_items = sorted(pop_items, key=lambda item: -float(item['user_id__count']))[:num]
        return sorted_items

    @staticmethod
    def recommend_items_by_ratings(user_id, active_user_items, num=6):
        item_ids = [i['id'] for i in active_user_items]
        pop_items = Rating.objects.filter(~Q(movie_id__in=item_ids)).values('movie_id').annotate(Count('user_id'),
                                                                                           Avg('rating'))
        recs = {i['movie_id']: {'prediction': i['rating__avg'], 'pop': i['user_id__count']} for i in pop_items}
        sorted_items = sorted(recs.items(), key=lambda item: -float(item[1]['pop']))[:num]
        return sorted_items

    @staticmethod
    def predict_score_by_ratings(item_id, movies):
        item = Rating.objects.filter(movie_id=item_id).values('movie_id').annotate(Avg('rating')).first()
        if not item:
            return 0

        return Decimal(item['rating__avg'])

