from decimal import Decimal

from analytics.models import Rating
from recs.base_recommender import base_recommender
from recs.content_based_recommender import ContentBasedRecs
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
import pickle

class FeatureWeightedLinearStacking(base_recommender):
    def __init__(self):
        self.cb = ContentBasedRecs()
        self.cf = NeighborhoodBasedRecs()

        self.wcb1 = Decimal(0.65221204)
        self.wcb2 = Decimal(-0.14638855)
        self.wcf1 = Decimal(-0.0062952)
        self.wcf2 = Decimal(0.09139193)
        self.intercept = Decimal(0)

    @staticmethod
    def fun1():
        return Decimal(1.0)

    @staticmethod
    def fun2(user_id):
        count = Rating.objects.filter(user_id=user_id).count()
        if count > 3.0:
            return Decimal(1.0)
        return Decimal(0.0)

    def set_save_path(self, save_path):
        with open(save_path + 'fwls_parameters.data', 'rb') as ub_file:
            parameters = pickle.load(ub_file)
            self.wcb1 = Decimal(parameters['cb1'])
            self.wcb2 = Decimal(parameters['cb2'])
            self.wcf1 = Decimal(parameters['cb1'])
            self.wcf2 = Decimal(parameters['cf2'])
            self.intercept = Decimal(parameters['intercept'])

    def recommend_items_by_ratings(self,
                                   user_id,
                                   active_user_items,
                                   num=6):

        cb_recs = self.cb.recommend_items_by_ratings(user_id, active_user_items, num * 5)
        cf_recs = self.cf.recommend_items_by_ratings(user_id, active_user_items, num * 5)

        return self.merge_predictions(user_id, cb_recs, cf_recs, num)

    def recommend_items(self, user_id, num=6):
        cb_recs = self.cb.recommend_items(user_id, num * 5)
        cf_recs = self.cf.recommend_items(user_id, num * 5)

        return self.merge_predictions(user_id, cb_recs, cf_recs, num)

    def merge_predictions(self, user_id, cb_recs, cf_recs, num):

        combined_recs = dict()
        for rec in cb_recs:
            movie_id = rec[0]
            pred = rec[1]['prediction']
            combined_recs[movie_id] = {'cb': pred}

        for rec in cf_recs:
            movie_id = rec[0]
            pred = rec[1]['prediction']
            if movie_id in combined_recs.keys():
                combined_recs[movie_id]['cf'] = pred
            else:
                combined_recs[movie_id] = {'cf': pred}
        fwls_preds = dict()
        for key, recs in combined_recs.items():
            if 'cb' not in recs.keys():
                recs['cb'] = self.cb.predict_score(user_id, key)
            if 'cf' not in recs.keys():
                recs['cf'] = self.cf.predict_score(user_id, key)
            pred = self.prediction(recs['cb'], recs['cf'], user_id)
            fwls_preds[key] = {'prediction': pred}
        sorted_items = sorted(fwls_preds.items(),
                              key=lambda item: -float(item[1]['prediction']))[:num]
        return sorted_items

    def predict_score(self, user_id, item_id):
        p_cb = self.cb.predict_score(user_id, item_id)
        p_cf = self.cf.predict_score(user_id, item_id)

        self.prediction(p_cb, p_cf, user_id)

    def prediction(self, p_cb, p_cf, user_id):
        p = (self.wcb1 * self.fun1() * p_cb +
             self.wcb2 * self.fun2(user_id) * p_cb +
             self.wcf1 * self.fun1() * p_cf +
             self.wcf2 * self.fun2(user_id) * p_cf)
        return p + self.intercept
