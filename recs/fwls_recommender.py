from recs.base_recommender import base_recommender


class FeatureWeightedLinearStacking(base_recommender):

    def fun1(self):
        return 1.0

    def fun2(self, user_id):
        if self.rating_count[self.rating_count['user_id'] == user_id]['movie_id'].values[0] > 3.0:
            return 1.0
        return 0.0

    def recommend_items(self, user_id, num=6):
        pass

    def predict_score(self, user_id, item_id):
        pass