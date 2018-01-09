import os
import argparse
from decimal import Decimal

import logging
import numpy as np
from numpy import random
import pandas as pd
from django.db.models import Count

from sklearn.model_selection import KFold

from builder.bpr_calculator import BayesianPersonalizationRanking
from builder.fwls_calculator import FWLSCalculator
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder
from builder.matrix_factorization_calculator import MatrixFactorization
from evaluator.algorithm_evaluator import PrecisionAtK, MeanAverageError
from recs.bpr_recommender import BPRRecs
from recs.content_based_recommender import ContentBasedRecs
from recs.funksvd_recommender import FunkSVDRecs
from recs.fwls_recommender import FeatureWeightedLinearStacking
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from recs.popularity_recommender import PopularityBasedRecs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
import time

django.setup()

from analytics.models import Rating


class EvaluationRunner(object):
    def __init__(self, folds, builder,
                 recommender,
                 k=10,
                 params=None,
                 logger=logging.getLogger('Evaluation runner')):
        self.folds = folds
        self.builder = builder
        self.recommender = recommender
        self.K = k
        self.params = params
        self.logger = logger

    def clean_data(self, ratings, min_ratings=5):
        self.logger.debug("cleaning data only to contain users with at least {} ratings".format(min_ratings))

        original_size = ratings.shape[0]

        user_count = ratings[['user_id', 'movie_id']]
        user_count = user_count.groupby('user_id').count()
        user_count = user_count.reset_index()
        user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']

        ratings = ratings[ratings['user_id'].isin(user_ids)]
        new_size = ratings.shape[0]
        self.logger.debug('reduced dataset from {} to {}'.format(original_size, new_size))
        return ratings

    def calculate(self, min_number_of_ratings=5, min_rank=10, number_test_users=-1):

        ratings_count = Rating.objects.all().count()
        self.logger.debug('{} ratings available'.format(ratings_count))

        if number_test_users == -1:
            ratings_rows = Rating.objects.all().values()

        else:
            user_ids = Rating.objects.values('user_id') \
                .annotate(movie_count=Count('movie_id')) \
                .filter(movie_count__gt=min_number_of_ratings) \
                .order_by('-movie_count')

            test_user_ids = set(user_ids.values_list('user_id', flat=True)[:number_test_users])

            ratings_rows = Rating.objects.filter(user_id__in=test_user_ids).values()

        all_ratings = pd.DataFrame.from_records(ratings_rows)
        if self.folds == 0:
            return self.calculate_using_ratings_no_crossvalidation(all_ratings,
                                                                   min_number_of_ratings,
                                                                   min_rank)
        else:
            return self.calculate_using_ratings(all_ratings,
                                                min_number_of_ratings,
                                                min_rank)

    def calculate_using_ratings_no_crossvalidation(self, all_ratings, min_number_of_ratings=5, min_rank=5):
        ratings = self.clean_data(all_ratings, min_number_of_ratings)

        users = ratings.user_id.unique()

        train_data_len = int((len(users) * 70 / 100))
        np.random.seed(42)
        np.random.shuffle(users)
        train_users, test_users = users[:train_data_len], users[train_data_len:]

        test_data, train_data = self.split_data(min_rank,
                                                ratings,
                                                test_users,
                                                train_users)

        self.logger.debug("Test run having {} training rows, and {} test rows".format(len(train_data),
                                                                          len(test_data)))

        if self.builder:
            if self.params:
                self.builder.build(train_data, self.params)
                self.logger.debug('setting save_path {}'.format(self.params['save_path']))
                self.recommender.set_save_path(self.params['save_path'])
            else:
                self.builder.build(train_data)

        self.logger.info("Build is finished")

        map, ar = PrecisionAtK(self.K, self.recommender).calculate_mean_average_precision(train_data, test_data)
        mae = 0
        results = {'map': map, 'ar': ar, 'mae': mae, 'users': len(users)}
        return results

    def calculate_using_ratings(self, all_ratings, min_number_of_ratings=5, min_rank=5):

        ratings = self.clean_data(all_ratings, min_number_of_ratings)

        users = ratings.user_id.unique()
        kf = self.split_users()

        validation_no = 0
        maps = Decimal(0.0)
        ars = Decimal(0.0)
        maes = Decimal(0.0)

        for train, test in kf.split(users):
            self.logger.info('starting validation no {}'.format(validation_no))
            validation_no += 1

            test_data, train_data = self.split_data(min_rank,
                                                    ratings,
                                                    users[test],
                                                    users[train])

            self.logger.info("Test run having {} training rows, and {} test rows".format(len(train_data),
                                                                              len(test_data)))
            if self.builder:
                self.builder.build(train_data)

            self.logger.info("Build is finished")

            map, ar = PrecisionAtK(self.K, self.recommender).calculate_mean_average_precision(train_data, test_data)

            maps += map
            ars += ar
            maes += MeanAverageError(self.recommender).calculate(train_data, test_data)
            results = {'map': maps / self.folds,
                       'ar': ars / self.folds,
                       'mae': maes / self.folds}

        self.logger.info(results)
        return results

    def split_users(self):
        kf = KFold(n_splits=self.folds)
        return kf

    @staticmethod
    def split_data(min_rank, ratings, test_users, train_users):

        train = ratings[ratings['user_id'].isin(train_users)]

        test_temp = ratings[ratings['user_id'].isin(test_users)].sort_values('rating_timestamp',
                                                                             ascending=False)

        test = test_temp.groupby('user_id').head(min_rank)

        additional_training_data = test_temp[~test_temp.index.isin(test.index)]

        train = train.append(additional_training_data)

        return test, train

def evaluate_pop_recommender():

    min_number_of_ratings = 20
    min_overlap = 5
    min_sim = 0.1
    min_rank = 5

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-pop.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("ar, map, mae, min_overlap, min_sim, K, min_num_of_ratings, min_rank\n")

        builder = None

        for k in np.arange(0, 20, 2):
            recommender = PopularityBasedRecs()
            er = EvaluationRunner(0,
                                  builder,
                                  recommender,
                                  k)

            result = er.calculate(min_number_of_ratings, min_rank, number_test_users=-1)

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            logfile.write("{}, {}, {}, {}, {}, {}, {}, {}\n".format(ar, map, mae,
                                                                    min_overlap,
                                                                    min_sim, k,
                                                                    min_number_of_ratings,
                                                                    min_rank))
            logfile.flush()


def evaluate_cf_recommender():
    min_number_of_ratings = 5
    min_overlap = 5
    min_sim = 0.1
    k = 10
    min_rank = 5

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-cf.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("ar, map, mae, min_overlap, min_sim, K, min_num_of_ratings, min_rank\n")

        for k in np.arange(0, 20, 2):
            min_rank = min_number_of_ratings / 2
            recommender = NeighborhoodBasedRecs()
            er = EvaluationRunner(0,
                                  ItemSimilarityMatrixBuilder(min_overlap, min_sim=min_sim),
                                  recommender,
                                  k)

            result = er.calculate(min_number_of_ratings, min_rank, number_test_users=-1)

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            logfile.write("{}, {}, {}, {}, {}, {}, {}, {}\n".format(ar, map, mae, min_overlap,
                                                                            min_sim, k,
                                                                            min_number_of_ratings,
                                                                            min_rank))
            logfile.flush()


def evaluate_cb_recommender():
    min_sim = 0
    min_num_of_ratings = 0
    min_rank = 0

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-cb-k.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("ar, map, mae, k, min_sim, min_num_of_ratings, min_rank\n")

        for k in np.arange(5, 20, 3):
            recommender = ContentBasedRecs()

            er = EvaluationRunner(0,
                                  None,
                                  recommender,
                                  k)

            result = er.calculate(10, 5, number_test_users=-1)

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            logfile.write("{}, {}, {}, {}, {}, {}\n".format(ar, map, mae,
                                                            k, min_sim,
                                                            min_num_of_ratings,
                                                            min_rank ))
            logfile.flush()


def evaluate_fwls_recommender():
    save_path = './models/fwls/'
    min_number_of_ratings = 10
    min_overlap = 3
    min_sim = 0.1
    K = 5
    min_rank = 5
    number_test_users = 1000
    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-fwls.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("ar, map, mae, min_overlap, min_sim, K, min_num_of_ratings, min_rank, data_sample\n")

        builder = FWLSCalculator(min_overlap, save_path)

        for data_sample in np.arange(500, 5000, 200):

            min_rank = min_number_of_ratings / 2
            recommender = FeatureWeightedLinearStacking()
            er = EvaluationRunner(0,
                                  builder,
                                  recommender,
                                  K,
                                  params={'save_path': save_path,
                                          'data_sample': data_sample}
                                  )

            result = er.calculate(min_number_of_ratings, min_rank, number_test_users)

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            logfile.write("{}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(ar, map, mae, min_overlap,
                                                                            min_sim, K,
                                                                            min_number_of_ratings,
                                                                            min_rank,
                                                                        data_sample))
            logfile.flush()


def evaluate_funksvd_recommender():
    save_path = './models/funkSVD/'
    K = 20
    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-funksvd-k.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("rak,pak,mae,k\n")

        builder = MatrixFactorization(save_path)

        for k in np.arange(0, 20, 2):

            recommender = FunkSVDRecs(save_path + 'model/')

            er = EvaluationRunner(0,
                                  builder,
                                  recommender,
                                  k,
                                  params={'k': 20,
                                          'save_path': save_path + 'model/'})

            result = er.calculate(20, 10)
            builder = None

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            logfile.write("{}, {}, {}, {}\n".format(ar, map, mae, k))

            logfile.flush()


def evaluate_bpr_recommender():
    number_of_factors = 30
    number_of_iterations = 5
    N = 10
    save_path = './models/bpr/'

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-bpr-k.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("ar, map, mae, N, error, factors, number_of_iterations\n")

        builder = BayesianPersonalizationRanking(save_path)

        for number_of_factors in np.arange(5, 50, 5):

            recommender = BPRRecs(save_path + 'model/')

            er = EvaluationRunner(0,
                                  builder,
                                  recommender,
                                  N,
                                  params={'k': number_of_factors,
                                          'num_iterations': number_of_iterations,
                                          'save_path': save_path + 'model/'})

            result = er.calculate(10, 5)

            map = result['map']
            mae = result['mae']
            ar = result['ar']
            error = builder.error if builder else 0
            logfile.write("{}, {}, {}, {}, {}, {}, {}\n".format(ar,
                                                                map,
                                                                mae,
                                                                N,
                                                                error,
                                                                number_of_factors,
                                                                number_of_iterations))
            logfile.flush()

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('Evaluation runner')

    parser = argparse.ArgumentParser(description='Evaluate recommender algorithms.')
    parser.add_argument('-fwls', help="run evaluation on fwls rec", action="store_true")
    parser.add_argument('-funk', help="run evaluation on funk rec", action="store_true")
    parser.add_argument('-cf', help="run evaluation on cf rec", action="store_true")
    parser.add_argument('-cb', help="run evaluation on cb rec", action="store_true")
    parser.add_argument('-ltr', help="run evaluation on rank rec", action="store_true")
    parser.add_argument('-pop', help="run evaluation on popularity rec", action="store_true")

    args = parser.parse_args()

    if args.fwls:
        logger.debug("evaluating fwls")
        evaluate_fwls_recommender()

    if args.cf:
        logger.debug("evaluating cf")
        evaluate_cf_recommender()

    if args.cb:
        logger.debug("evaluating cb")
        evaluate_cb_recommender()

    if args.ltr:
        logger.debug("evaluating ltr")
        evaluate_bpr_recommender()

    if args.funk:
        logger.debug("evaluating funk")
        evaluate_funksvd_recommender()

    if args.pop:
        logger.debug("evaluating popularity")
        evaluate_pop_recommender()