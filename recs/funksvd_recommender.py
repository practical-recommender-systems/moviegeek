import json

from django.db.models import Avg

from recommender.models import Recs
from analytics.models import Rating
from recs.base_recommender import base_recommender

import numpy as np
import pandas as pd
import pickle

class FunkSVDRecs(base_recommender):


    def __init__(self, save_path='/Users/u0157492/Projects/moviegeek/models/hyperparameter/model/40factors/'):
        self.save_path = save_path
        self.load_model(save_path)

        self.avg = list(Rating.objects.all().aggregate(Avg('rating')).values())[0]

    def load_model(self, save_path):
        with open(save_path + 'user_bias.data', 'rb') as ub_file:
            self.user_bias = pickle.load(ub_file)
        with open(save_path + 'item_bias.data', 'rb') as ub_file:
            self.item_bias = pickle.load(ub_file)
        with open(save_path + 'user_factors.json', 'r') as infile:
            self.user_factors = pd.DataFrame(json.load(infile)).T
        with open(save_path + 'item_factors.json', 'r') as infile:
            self.item_factors = pd.DataFrame(json.load(infile)).T

    def set_save_path(self, save_path):
        self.save_path = save_path

        self.load_model(save_path)

    def predict_score(self, user_id, item_id):
        rec = Recs.objects.filter(user_id = user_id, item_id=item_id).first()
        if rec is None:
            return 0
        else:
            return rec.rating

    def recommend_items(self, user_id, num=6):
        active_user_items = Rating.objects.filter(user_id=user_id).order_by('-rating')[:100]

        return self.recommend_items_by_ratings(user_id, active_user_items.values())

    def recommend_items_by_ratings(self, user_id, active_user_items, num=6):

        rated_movies = {movie['movie_id']: movie['rating'] for movie in active_user_items}

        user = self.user_factors[str(user_id)]
        scores = self.item_factors.T.dot(user)

        scores.sort_values(inplace=True, ascending=False)
        result = scores[:num + len(rated_movies)]
        user_bias = 0

        if user_id in self.user_bias.keys():
            user_bias = self.user_bias[user_id]
        elif int(user_id) in self.user_bias.keys():
            user_bias = self.user_bias[int(user_id)]

        recs = {r[0]: {'prediction': r[1] + user_bias + self.item_bias[r[0]] + self.avg}
                for r in zip(result.index, result) if r[0] not in rated_movies}

        sorted_items = sorted(recs.items(), key=lambda item: -float(item[1]['prediction']))[:num]
        if user_id == 14620:
            print(user_id, rated_movies)
            print(user_id, sorted_items)
        return sorted_items
