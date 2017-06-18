from analytics.models import Rating
from recs.base_recommender import base_recommender
from django.db.models import Count
from django.db.models import Q
from django.db.models import Avg

class PopularityBasedRecs(base_recommender):

    def predict_score(self, user_id, item_id):
        avg_rating = Rating.objects.filter(~Q(user_id=user_id) & Q(movie_id=item_id)).values('movie_id').aggregate(Avg('rating'))
        return avg_rating['rating__avg']

    def recommend_items(self, user_id, num=6):
        pop_items = Rating.objects.filter(~Q(user_id=user_id)).values('movie_id').annotate(Count('user_id'), Avg('rating'))
        sorted_items = sorted(pop_items, key=lambda item: -float(item['user_id__count']))[:num]
        return sorted_items