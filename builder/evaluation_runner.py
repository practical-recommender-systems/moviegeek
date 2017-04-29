import os
import time
import datetime
import json
import pandas as pd

from collections import defaultdict
from sklearn.model_selection import KFold

from builder.algorithm_evaluator import PrecissionAtK
from builder.item_similarity_calculator import build
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
from django.db.models import Count

django.setup()
import numpy as np
from analytics.models import Rating

class EvaluationRunner(object):
    def __init__(self):
        self.folds = None

    def remove_new_users(self, ratings, min_ratings=20):
        # original_size = ratings.shape[0]
        # s = '01/01/2013'
        # min_date = datetime.datetime.strptime(s, "%d/%m/%Y")
        # print(ratings.head())
        # ratings = ratings[ratings['rating_timestamp'] > str(min_date)]

        user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
        user_count = user_count.reset_index()
        user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
        ratings = ratings[ratings['user_id'].isin(user_ids)]
        new_size = ratings.shape[0]
        print('reduced dataset from {} to {}'.format(original_size, new_size))
        return ratings

    def calculate(self, num_folds=5, min_rank=5):

        ratings_rows = Rating.objects.all().values()
        all_ratings = pd.DataFrame.from_records(ratings_rows)

        ratings = self.remove_new_users(all_ratings)

        users = ratings.user_id.unique()
        kf = KFold(n_splits=num_folds)
        validation_no = 0
        for train, test in kf.split(users):
            print('starting validation no {}'.format(validation_no))
            validation_no += 1

            train_data = ratings[ratings['user_id'].isin(train)]
            test_data = ratings[ratings['user_id'].isin(test)]

            test_data['rank'] = test_data.groupby('user_id')['rating_timestamp'].rank(ascending=False)

            additional_training_data = test_data[test_data['rank'] <= min_rank]
            test_data = test_data[test_data['rank'] > min_rank]

            train_data = train_data.append(additional_training_data)

            print("Test run with fold, having {} training rows, and {} test rows".format(len(train_data), len(test_data)))
            build(train_data)
            print("Build is finished")
            PrecissionAtK(5, NeighborhoodBasedRecs()).calculate(test_data)


if __name__ == '__main__':
    er = EvaluationRunner()
    er.calculate(5)