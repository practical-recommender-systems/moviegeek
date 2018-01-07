import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import pickle
import logging

import pandas as pd
from sklearn import linear_model
from sklearn.model_selection import train_test_split

from analytics.models import Rating
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder
from builder.lda_model_calculator import LdaModel
from recs.content_based_recommender import ContentBasedRecs
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from recs.fwls_recommender import FeatureWeightedLinearStacking


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class FWLSCalculator(object):
    def __init__(self, save_path, data_size=1000):
        self.save_path = save_path
        self.logger = logging.getLogger('FWLS')
        self.train_data = None
        self.test_data = None
        self.rating_count = None
        self.cb = ContentBasedRecs()
        self.cf = NeighborhoodBasedRecs()
        self.fwls = FeatureWeightedLinearStacking()
        self.data_size = data_size

    def get_real_training_data(self):
        columns = ['user_id', 'movie_id', 'rating', 'type']
        ratings_data = Rating.objects.all().values(*columns)[:self.data_size]
        df = pd.DataFrame.from_records(ratings_data, columns=columns)
        self.train_data, self.test_data = train_test_split(df, test_size=0.2)
        self.logger.debug("training data loaded {}".format(len(ratings_data)))

    def calculate_predictions_for_training_data(self):
        self.logger.debug("[BEGIN] getting predictions")

        self.train_data['cb'] = self.train_data.apply(lambda data:
                                                      self.cb.predict_score(data['user_id'],
                                                                            data['movie_id']), axis=1)

        self.train_data['cf'] = self.train_data.apply(lambda data:
                                                      self.cf.predict_score(data['user_id'],
                                                                            data['movie_id']), axis=1)

        self.logger.debug("[END] getting predictions")
        return None

    def calculate_feature_functions_for_training_data(self):
        self.logger.debug("[BEGIN] calculating functions")
        self.train_data['cb1'] = self.train_data.apply(lambda data:
                                                       data['cb'] * self.fwls.fun1(), axis=1)
        self.train_data['cb2'] = self.train_data.apply(lambda data:
                                                       data['cb'] * self.fwls.fun2(data['user_id']), axis=1)

        self.train_data['cf1'] = self.train_data.apply(lambda data:
                                                       data['cf'] * self.fwls.fun1(), axis=1)
        self.train_data['cf2'] = self.train_data.apply(lambda data:
                                                       data['cf'] * self.fwls.fun2(data['user_id']), axis=1)

        self.logger.debug("[END] calculating functions")
        return None

    def build(self, train_data=None, params=None):

        if params:
            self.save_path = params['save_path']
            self.data_size = params['data_sample']

        if train_data is not None:
            self.train_data = train_data
            if self.data_size > 0:
                self.train_data = self.train_data.sample(self.data_size)
                self.logger.debug("training sample of size {}".format(self.train_data.shape[0]))
        else:
            self.get_real_training_data()

        self.calculate_predictions_for_training_data()
        self.calculate_feature_functions_for_training_data()

        return self.train()

    def train(self, ratings=None, train_feature_recs=False):

        if train_feature_recs:
            ItemSimilarityMatrixBuilder().build(ratings)
            LdaModel.build()

        regr = linear_model.LinearRegression(fit_intercept=True,
                                             n_jobs=-1,
                                             normalize=True)

        regr.fit(self.train_data[['cb1', 'cb2', 'cf1', 'cf2']], self.train_data['rating'])
        self.logger.info(regr.coef_)

        result = {'cb1': regr.coef_[0],
                  'cb2': regr.coef_[1],
                  'cf1': regr.coef_[2],
                  'cf2': regr.coef_[3],
                  'intercept': regr.intercept_}
        self.logger.debug(result)
        self.logger.debug(self.train_data.iloc[100])
        ensure_dir(self.save_path)
        with open(self.save_path + 'fwls_parameters.data', 'wb') as ub_file:
            pickle.dump(result, ub_file)
        return result


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('funkSVD')
    logger.info("[BEGIN] Calculating Feature Weighted Linear Stacking...")

    if not os.path.exists("./models/lda/model.lda"):
        logger.error("lda model should be done first. please run the lda_model_calculator.py script")
        exit()

    fwls = FWLSCalculator(data_size=1000)
    fwls.get_real_training_data()
    logger.info(fwls.train_data)

    fwls.calculate_predictions_for_training_data()
    fwls.calculate_feature_functions_for_training_data()
    logger.info("Freatures trained")
    logger.info("[BEGIN] training of FWLS")
    fwls.train()
    logger.info("[END] training of FWLS")
    logger.info("[END] Calculating Feature Weighted Linear Stacking...")
