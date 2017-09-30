from recs.base_recommender import base_recommender
from analytics.models import Rating
from recommender.models import Similarity
from django.db.models import Q
import time

from decimal import Decimal


class NeighborhoodBasedRecs(base_recommender):

    def __init__(self, neighborhood_size=15, min_sim=0.0):
        self.neighborhood_size = neighborhood_size
        self.min_sim = min_sim
        self.max_candidates = 100

    def recommend_items(self, user_id, num=6):

        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[:100]

        return self.recommend_items_by_ratings(user_id, active_user_items.values())

    def recommend_items_by_ratings(self, user_id, active_user_items, num=6):

        start = time.time()
        movie_ids = {movie['movie_id']: movie['rating'] for movie in active_user_items}
        user_mean = sum(movie_ids.values()) / len(movie_ids)

        candidate_items = Similarity.objects.filter(Q(source__in=movie_ids.keys())
                                                    & ~Q(target__in=movie_ids.keys())
                                                    & Q(similarity__gt=self.min_sim)
                                                    )
        candidate_items = candidate_items.order_by('-similarity')[:self.max_candidates]


        recs = dict()
        for candidate in candidate_items:
            target = candidate.target

            pre = 0
            sim_sum = 0

            rated_items = [i for i in candidate_items if i.target == target][:self.neighborhood_size]

            if len(rated_items) > 1:
                for sim_item in rated_items:
                    r = Decimal(movie_ids[sim_item.source] - user_mean)
                    pre += sim_item.similarity * r
                    sim_sum += sim_item.similarity
                if sim_sum > 0:
                    recs[target] = {'prediction': Decimal(user_mean) + pre / sim_sum,
                                    'sim_items': [r.source for r in rated_items]}

        sorted_items = sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]
        #print("Time spend on rec ", user_id, " time: ", time.time() - start, "items: ",len( sorted_items))
        return sorted_items

    def predict_score(self, user_id, item_id):

        active_user_items = Rating.objects.exclude(movie_id=item_id).filter(user_id=user_id).order_by('-rating')[:100]
        movie_ids = {movie.movie_id: movie.rating for movie in active_user_items}

        return self.predict_score_by_ratings(item_id, movie_ids)

    def predict_score_by_ratings(self, item_id, movie_ids):
        top = 0
        bottom = 0

        candidate_items = Similarity.objects.filter(source__in=movie_ids.keys()).filter(target=item_id)
        candidate_items = candidate_items.distinct().order_by('-similarity')[:self.max_candidates]

        if len(candidate_items) == 0:
            return 0

        for sim_item in candidate_items:
            r = movie_ids[sim_item.source]
            top += sim_item.similarity * r
            bottom += sim_item.similarity

        return top / bottom