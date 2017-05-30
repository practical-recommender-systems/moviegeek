from recommender.models import Recs
from recs.base_recommender import base_recommender
import numpy as np
import pandas as pd
import pickle

class FunkSVDRecs(base_recommender):

    def predict_score(self, user_id, item_id):
        rec = Recs.objects.filter(user_id = user_id, item_id=item_id).first()
        if rec is None:
            return 0
        else:
            return rec.rating

    def recommend_items(self, user_id, num=6):
        recs = Recs.objects.filter(user_id=user_id, item_id=item_id).orderby('rating')[:6]
        if recs is None:
            return []
        else:
            return recs.values()
