import os
import time
import datetime
import json
import pandas as pd

from collections import defaultdict
from sklearn.model_selection import KFold

from builder import data_helper
from builder.algorithm_evaluator import PrecissionAtK
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django

from django.db.models import Count

django.setup()
import numpy as np
from analytics.models import Rating

class EvaluationRunner(object):
    def __init__(self, folds, builder, recommender):
        self.folds = folds
        self.builder = builder
        self.recommender = recommender

    def clean_data(self, ratings, min_ratings=5):
        original_size = ratings.shape[0]
        user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
        user_count = user_count.reset_index()
        user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
        ratings = ratings[ratings['user_id'].isin(user_ids)]
        new_size = ratings.shape[0]
        print('reduced dataset from {} to {}'.format(original_size, new_size))
        return ratings

    def calculate(self, min_rank=10):

        ratings_rows = Rating.objects.all().values()
        all_ratings = pd.DataFrame.from_records(ratings_rows)

        return self.calculate_using_ratings(all_ratings, min_rank)

    def calculate_using_ratings(self, all_ratings, min_rank=5):


        ratings = self.clean_data(all_ratings, min_rank)

        users = ratings.user_id.unique()
        kf = self.split_users()

        validation_no = 0
        results = []
        for train, test in kf.split(users):
            print('starting validation no {}'.format(validation_no))
            validation_no += 1

            test_data, train_data = self.split_data(min_rank,
                                                    ratings,
                                                    users[test],
                                                    users[train])

            print("Test run having {} training rows, and {} test rows".format(len(train_data), len(test_data)))
            self.builder.build(train_data)
            print("Build is finished")

            result = PrecissionAtK(10, self.recommender).calculate(train_data, test_data)
            results.append(result)

        print(results)

    def split_users(self):
        kf = KFold(n_splits=self.folds)
        return kf

    def split_data(self, min_rank, ratings, test_users, train_users):
        train = ratings[ratings['user_id'].isin(train_users)]
        test_temp = ratings[ratings['user_id'].isin(test_users)]

        test_temp['rank'] = test_temp.groupby('user_id')['rating_timestamp'].rank(ascending=False)
        test = test_temp[test_temp['rank'] < min_rank]

        additional_training_data = test_temp[test_temp['rank'] >= min_rank]
        train = train.append(additional_training_data)

        return test, train

    def split_ratings_sql(self):

        sql = """select  *,
           ( select  count(*)
             from    analytics_rating as rating2
             where   rating2.rating_timestamp < rating1.rating_timestamp
             and     rating1.user_id = rating2.user_id
            ) as rank
        from    analytics_rating as rating1
        where    rank < 3"""

        columns = ['user_id', 'movie_id', 'rating', 'type']
        rating_data = data_helper.get_data_frame(sql, columns)

        print('found {} ratings'.format(rating_data.count()))
        return rating_data

if __name__ == '__main__':
    TEST = False

    if TEST:
        er = EvaluationRunner(5, ItemSimilarityMatrixBuilder(2), NeighborhoodBasedRecs())
        ratings = pd.DataFrame(
            [[1, '11', 5, '2013-10-12 23:20:27+00:00'],
             [1, '12', 3, '2014-10-12 23:20:27+00:00'],
             [1, '14', 2, '2015-10-12 23:20:27+00:00'],
             [2, '11', 4, '2013-10-12 23:20:27+00:00'],
             [2, '12', 3, '2014-10-12 23:20:27+00:00'],
             [2, '13', 4, '2015-10-12 23:20:27+00:00'],
             [3, '11', 5, '2013-10-12 23:20:27+00:00'],
             [3, '12', 2, '2014-10-12 23:20:27+00:00'],
             [3, '13', 5, '2015-10-12 23:20:27+00:00'],
             [3, '14', 2, '2016-10-12 23:20:27+00:00'],
             [4, '11', 3, '2013-10-12 23:20:27+00:00'],
             [4, '12', 5, '2014-10-12 23:20:27+00:00'],
             [4, '13', 3, '2015-10-12 23:20:27+00:00'],
             [5, '11', 3, '2013-10-12 23:20:27+00:00'],
             [5, '12', 3, '2014-10-12 23:20:27+00:00'],
             [5, '13', 3, '2015-10-12 23:20:27+00:00'],
             [5, '14', 2, '2016-10-12 23:20:27+00:00'],
             [6, '11', 2, '2013-10-12 23:20:27+00:00'],
             [6, '12', 3, '2014-10-12 23:20:27+00:00'],
             [6, '13', 2, '2015-10-12 23:20:27+00:00'],
             [6, '14', 3, '2016-10-12 23:20:27+00:00'],
             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

        er.calculate_using_ratings(ratings, 2)
    else:
        er = EvaluationRunner(5, ItemSimilarityMatrixBuilder(), NeighborhoodBasedRecs())
        er.calculate()