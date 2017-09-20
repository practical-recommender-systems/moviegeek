from decimal import Decimal
import os

import datetime
import math
import pandas as pd
import numpy as np
import timeit

from sklearn.model_selection import KFold

from builder.algorithm_evaluator import PrecisionAtK, MeanAverageError
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from django.db.models import Count

from recs.popularity_recommender import PopularityBasedRecs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
from datetime import datetime
import time
from sklearn.model_selection import train_test_split

django.setup()

from analytics.models import Rating


class EvaluationRunner(object):

    def __init__(self, folds, builder, recommender, K = 10):
        self.folds = folds
        self.builder = builder
        self.recommender = recommender
        self.K = K

    def clean_data(self, ratings, min_ratings=5):
        print("cleaning data only to contain users with at least {} ratings".format(min_ratings))

        original_size = ratings.shape[0]

        user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
        user_count = user_count.reset_index()
        user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']

        ratings = ratings[ratings['user_id'].isin(user_ids)]
        new_size = ratings.shape[0]
        print('reduced dataset from {} to {}'.format(original_size, new_size))
        return ratings

    def calculate(self, min_number_of_ratings=5, min_rank=10, number_test_users=-1):

        ratings_count = Rating.objects.all().count()
        print('{} ratings available'.format(ratings_count))

        if number_test_users == -1:
            ratings_rows = Rating.objects.all().values()

        else:
            user_ids = Rating.objects.values('user_id')\
                .annotate(movie_count=Count('movie_id'))\
                .filter(movie_count__gt=min_number_of_ratings)\
                .order_by('-movie_count')

            user_ids = user_ids.values('user_id')[:number_test_users]

            ratings_rows = Rating.objects.filter(user_id__in=user_ids).values()

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

        train_data_len = int((len(users)*70/100))
        np.random.shuffle(users)
        train_users, test_users = users[:train_data_len], users[train_data_len:]

        test_data, train_data = self.split_data(min_rank,
                                                ratings,
                                                test_users,
                                                train_users)

        print("Test run having {} training rows, and {} test rows".format(len(train_data),
                                                                          len(test_data)))

        if self.builder:
            self.builder.build(train_data)

        print("Build is finished")

        pak, rak = PrecisionAtK(self.K, self.recommender).calculate(train_data, test_data)
        mae=0
        #mae = MeanAverageError(self.recommender).calculate(train_data, test_data)
        results = {'pak': pak, 'rak': rak, 'mae': mae}
        return results

    def calculate_using_ratings(self, all_ratings, min_number_of_ratings=5, min_rank=5):

        ratings = self.clean_data(all_ratings, min_number_of_ratings)

        users = ratings.user_id.unique()
        kf = self.split_users()

        validation_no = 0
        paks = Decimal(0.0)
        raks = Decimal(0.0)
        maes = Decimal(0.0)

        for train, test in kf.split(users):
            print('starting validation no {}'.format(validation_no))
            validation_no += 1

            test_data, train_data = self.split_data(min_rank,
                                                    ratings,
                                                    users[test],
                                                    users[train])

            print("Test run having {} training rows, and {} test rows".format(len(train_data),
                                                                              len(test_data)))
            if self.builder:
                self.builder.build(train_data)

            print("Build is finished")

            pak, rak = PrecisionAtK(self.K, self.recommender).calculate(train_data, test_data)

            paks += pak
            raks += rak
            maes += MeanAverageError(self.recommender).calculate(train_data, test_data)
            results = {'pak': paks/self.folds, 'rak': raks/self.folds, 'mae': maes/self.folds}

        print(results)
        return results

    def split_users(self):
        kf = KFold(n_splits=self.folds)
        return kf

    def split_data(self, min_rank, ratings, test_users, train_users):

        train = ratings[ratings['user_id'].isin(train_users)]

        test_temp = ratings[ratings['user_id'].isin(test_users)].sort_values('rating_timestamp', ascending=False)

        test = test_temp.groupby('user_id').head(min_rank)

        additional_training_data = test_temp[~test_temp.index.isin(test.index)]

        train = train.append(additional_training_data)

        return test, train

if __name__ == '__main__':
    min_number_of_ratings = 20
    min_overlap = 5
    min_sim = 0.3
    K = 20
    min_rank = 5

    timestr = time.strftime("%Y%m%d-%H%M%S")
    file_name = '{}-min_overlap_item_similarity.csv'.format(timestr)

    with open(file_name, 'a', 1) as logfile:
        logfile.write("rak, pak, mae, min_overlap, min_sim, K, min_num_of_ratings, min_rank\n")

        builder = ItemSimilarityMatrixBuilder(min_overlap, min_sim=min_sim)

        for min_overlap in np.arange(0, 20, 1):
            min_rank = min_number_of_ratings/2
            er = EvaluationRunner(0,
                                   builder,
                                   NeighborhoodBasedRecs(),
                                   K)
            # Run the baseline recommender:
            # er = EvaluationRunner(3, None, PopularityBasedRecs(), K)

            result = er.calculate(min_number_of_ratings, min_rank, number_test_users=-1)
            pak = result['pak']
            mae = result['mae']
            rak = result['rak']
            logfile.write("{}, {}, {}, {}, {}, {}, {}, {} \n".format(rak, pak, mae, min_overlap,
                                                                 min_sim, K,
                                                                 min_number_of_ratings,
                                                                 min_rank, datetime.now()))
            logfile.flush()
            #builder = None


