import os
import time
import json
import numpy as np

from collections import defaultdict
from sklearn.model_selection import KFold
from decimal import Decimal
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from moviegeeks.models import Movie
from analytics.models import Rating


class DataSplitter(object):
    def __init__(self):
        self.folds = None

    def training_data(self):

        if self.folds is None:
            return Rating.objects().all()
        else:
            return Rating.objects().filter(user_id__in=self.folds)

    def split_data(self, num_folds=5):

        users = Rating.objects().values('user_id').distinct()
        kf = KFold(n_split=num_folds)
        self.folds = kf.split(users)


class MeanAverageError(object):
    def __init__(self, recommender):
        self.rec = recommender

    def calculate(self, train_ratings, test_ratings):

        user_ids = test_ratings['user_id'].unique()
        print('evaluating based on {} users (MAE)'.format(len(user_ids)))
        error = 0


        for user_id in user_ids:
            user_error = Decimal(0.0)

            ratings_for_rec = train_ratings[train_ratings.user_id == user_id]
            movies = {m['movie_id']: m['rating'] for m in
                      ratings_for_rec[['movie_id', 'rating']].to_dict(orient='records')}

            this_test_ratings = test_ratings[test_ratings['user_id'] == user_id]

            num_movies = 0
            if len(this_test_ratings) > 0:

                movie_ids = this_test_ratings['movie_id'].unique()
                for item_id in movie_ids:
                    actual_rating = this_test_ratings[this_test_ratings['movie_id'] == item_id].iloc[0]['rating']
                    predicted_rating = self.rec.predict_score_by_ratings(item_id, movies)
                    if actual_rating > 0 and predicted_rating > 0:
                        num_movies += 1
                        item_error = abs(actual_rating - predicted_rating)
                        user_error += item_error
                    else:
                        print("userid:{}, item:{} actual {} predicted = {}".format(user_id, item_id, actual_rating, predicted_rating))
                error += user_error / num_movies
        return error / len(user_ids)


class PrecissionAtK(object):
    def __init__(self, k, recommender):

        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.K = k
        self.rec = recommender

    def calculate(self, train_ratings, test_ratings):

        timestr = time.strftime("%Y%m%d-%H%M%S")
        file_name = '{}-evaluation_data.csv'.format(timestr)

        total_score = 0.0

        with open(file_name, 'a') as the_file:
            the_file.write("user_id, num_recs, num_test_data, test_data, recs\n")
            # use test users.
            user_ids = test_ratings['user_id'].unique()
            print('evaluating based on {} users'.format(len(user_ids)))
            apks = []
            for user_id in user_ids:

                ratings_for_rec = train_ratings[train_ratings.user_id == user_id][:20]
                dicts_for_rec = ratings_for_rec.to_dict(orient='records')

                relevant_ratings = list(test_ratings[(test_ratings['user_id'] == user_id)]['movie_id'])
                recs = list(self.rec.recommend_items_by_ratings(user_id,
                                                                dicts_for_rec,
                                                                self.K))

                score = self.average_precision_k(recs, relevant_ratings)

                apks.append(score)
                total_score += score
                the_file.write("{}, {}, {}, {}, {} \n".format(user_id,
                                                             len(recs),
                                                             len(relevant_ratings),
                                                             relevant_ratings, recs))

        mean_average_precision = np.mean(apks)
        print("MAP: ({}, {}) = {}".format(total_score,
                                              len(user_ids),
                                              mean_average_precision))
        return mean_average_precision

    def average_precision_k(self, recs, actual):
        score = 0.0
        num_hits = 0

        for i, p in enumerate(recs):
            if p[0] in actual and p not in recs[:i]:
                num_hits += 1.0
                score += num_hits / (i + 1.0)

        print("hits: {}  score {}".format(num_hits, score))
        score = score / min(len(actual), self.K)

        return score


class CFCoverage(object):
    def __init__(self):
        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.cf = NeighborhoodBasedRecs()
        self.items_in_rec = defaultdict(int)
        self.users_with_recs = []

    def calculate_coverage(self):

        print('calculating coverage for all users ({} in total)'.format(len(self.all_users)))
        for user in self.all_users:
            user_id = str(user['user_id'])
            recset = self.cf.recommend_items(user_id)
            if recset:
                self.users_with_recs.append(user)
                for rec in recset:
                    self.items_in_rec[rec[0]] += 1
                print('found recs for {}'.format(user_id))

        print('writing cf coverage to file.')
        json.dump(self.items_in_rec, open('cf_coverage.json', 'w'))

        no_movies = Movie.objects.all().count()
        no_movies_in_rec = len(self.items_in_rec.items())

        print("{} {} {}".format(no_movies, no_movies_in_rec, float(no_movies / no_movies_in_rec)))
        return no_movies_in_rec / no_movies


if __name__ == '__main__':
    # print("Calculating coverage...")
    # CFCoverage().calculate_coverage()

    print("Calculating Precision at K")
    pak = PrecissionAtK(5, NeighborhoodBasedRecs(),
                        ItemSimilarityMatrixBuilder())

    pak.calculate_old()
