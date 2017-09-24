import os
import time
import json
import numpy as np

from collections import defaultdict
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from moviegeeks.models import Movie
from analytics.models import Rating


class MeanAverageError(object):
    def __init__(self, recommender):
        self.rec = recommender

    def calculate(self, train_ratings, test_ratings):

        user_ids = test_ratings['user_id'].unique()
        print('evaluating based on {} users (MAE)'.format(len(user_ids)))
        error = Decimal(0.0)

        if len(user_ids) == 0:
            return Decimal(0.0)

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

                if num_movies > 0:
                    error += user_error / num_movies

                    print(
                        "AE userid:{}, test_ratings:{} predicted {} error {}".format(user_id,
                                                                                     len(this_test_ratings),
                                                                                     num_movies,
                                                                                     user_error / num_movies))

        return error / len(user_ids)


class PrecisionAtK(object):
    def __init__(self, k, recommender):

        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.K = k
        self.rec = recommender

    def calculate(self, train_ratings, test_ratings):

        timestr = time.strftime("%Y%m%d-%H%M%S")
        file_name = '{}-evaluation_data.csv'.format(timestr)

        total_precision_score = Decimal(0.0)
        total_recall_score = Decimal(0.0)

        #with open(file_name, 'a') as the_file:
        #    the_file.write("user_id, num_recs, num_test_data, test_data, recs\n")
            # use test users.

        apks = []
        arks = []
        user_id_count = 0
        #timestr = time.strftime("%Y%m%d-%H%M%S")

        for user_id, users_test_data in test_ratings.groupby('user_id'):
            user_id_count += 1
            training_data_for_user = train_ratings[train_ratings['user_id'] == user_id][:20]
            #print("training_data_for_user ",training_data_for_user)
            dict_for_rec = training_data_for_user.to_dict(orient='records')
            #print("dict_for_rec ",dict_for_rec )
            relevant_ratings = list(users_test_data['movie_id'])

            recs = list(self.rec.recommend_items_by_ratings(user_id,
                                                            dict_for_rec,
                                                            self.K))

            if len(recs) > 0:
                AP = self.average_precision_k(recs, relevant_ratings)
                AR = self.average_recall_k(recs, relevant_ratings)
                print("recs: {} actual: {} p@k {} r@k {} ".format(len(recs), len(relevant_ratings), AP, AR))
                arks.append(AP)
                apks.append(AR)
                total_precision_score += AP
                total_recall_score += AR

        mean_average_recall = np.mean(arks)
        mean_average_precision = np.mean(apks)
        print("MAP: ( ap@k: {}, ar@k{}, {}) = {}".format(total_precision_score,
                                                         total_recall_score,
                                                         user_id_count,
                                                         mean_average_precision))
        return mean_average_precision, mean_average_recall

    def average_recall_k(self, recs, actual):
        score = Decimal(0.0)
        num_hits = 0

        for i, p in enumerate(recs):
            TP = p[0] in actual
            if TP:
                num_hits += 1.0
            score += Decimal(num_hits / min(len(actual), len(recs)))
        score /= len(recs)


        return score

    def average_precision_k(self, recs, actual):
        score = Decimal(0.0)
        num_hits = 0

        for i, p in enumerate(recs):
            TP = p[0] in actual
            if TP:
                num_hits += 1.0
            score += Decimal(num_hits / (i + 1.0))

        score /= len(recs)

        return score


class RecommenderCoverage(object):
    def __init__(self, recommender):
        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.recommender = recommender
        self.items_in_rec = defaultdict(int)
        self.users_with_recs = []

    def calculate_coverage(self):

        print('calculating coverage for all users ({} in total)'.format(len(self.all_users)))
        for user in self.all_users:
            user_id = str(user['user_id'])
            recset = self.recommender.recommend_items(user_id)
            if recset:
                self.users_with_recs.append(user)
                for rec in recset:
                    self.items_in_rec[rec[0]] += 1
                print('found recs for {}'.format(user_id))

        print('writing cf coverage to file.')
        json.dump(self.items_in_rec, open('cf_coverage.json', 'w'))

        no_movies = Movie.objects.all().count()
        no_movies_in_rec = len(self.items_in_rec.items())
        no_users = self.all_users.count()
        no_users_in_rec = len(self.users_with_recs)
        user_coverage = float(no_users_in_rec/ no_users)
        movie_coverage = float(no_movies_in_rec/ no_movies)
        print("{} {} {}".format(no_users, no_users_in_rec), user_coverage)
        print("{} {} {}".format(no_movies, no_movies_in_rec, movie_coverage))
        return user_coverage, movie_coverage
