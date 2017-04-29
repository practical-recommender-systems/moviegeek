import os
import time
import json
import pandas as pd

from collections import defaultdict
from sklearn.model_selection import KFold

from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from moviegeeks.models import Movie
from analytics.models import Rating
from builder import data_helper


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


class PrecissionAtK(object):
    # todo:
    # * split the data.
    # * calculate similarities with training data.


    def __init__(self, k, recommender):

        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.K = k
        self.rec = recommender

    def calculate(self, ratings):

        timestr = time.strftime("%Y%m%d-%H%M%S")
        file_name = '{}-evaluation_data.csv'.format(timestr)

        print('start evaluation with {} ratings'.format(ratings.shape[0]))
        total_score = 0
        num_user = 0

        with open(file_name, 'a') as the_file:

            # use test users.
            user_ids = ratings['user_id'].unique()
            print('evaluating based on {} users'.format(len(user_ids)))

            for user_id in user_ids:
                num_user += 1

                relevant_ratings = list(ratings[(ratings['user_id'] == user_id) &
                                                (ratings['rating'] > 5.0)]['movie_id'])
                recs = list(self.rec.recommend_items(user_id, self.K))
                num_hits = 0
                score = 0

                for i, p in enumerate(recs):
                    if p[0] in relevant_ratings and p not in recs[:i]:
                        num_hits += 1.0
                        score += num_hits / (i + 1.0)

                total_score += score
                the_file.write("{}, {}, {}, {}, {}\n".format(user_id,
                                                             len(recs),
                                                             len(relevant_ratings),
                                                             num_hits,
                                                             score))
        mean_average_precision = total_score / len(self.all_users)
        print("MAP: ({}, {}) = {}".format(total_score,
                                          len(self.all_users),
                                          mean_average_precision))
        return mean_average_precision

    def calculate_old(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        file_name = '{}-evaluation_data.csv'.format(timestr)
        # rating_data = self.split_ratings_django()
        print('build similarity matrix')
        # build(rating_data)
        print('start evaluation with {} users'.format(len(self.all_users)))
        total_score = 0
        num_user = 0

        with open(file_name, 'a') as the_file:

            # use test users.
            for user in self.all_users:
                num_user += 1
                user_id = str(user['user_id'])
                actual = list(Rating.objects.filter(user_id=user_id))
                relevant_ratings = [r.movie_id for r in actual if self.relevant(r)]
                recset = list(self.rec.recommend_items(user_id, self.K))

                num_hits = 0
                score = 0

                for i, p in enumerate(recset):
                    if p[0] in relevant_ratings and p not in recset[:i]:
                        num_hits += 1.0
                        score += num_hits / (i + 1.0)
                        the_file.write("{}, {}, {}, {}, {}\n".format(user_id,
                                                                     len(recset),
                                                                     len(relevant_ratings),
                                                                     num_hits,
                                                                     score))
                total_score += score
                if num_user % 1000 == 0:
                    print(num_user)
            print("")
            print("MAP: ({}, {}) = {}".format(total_score,
                                              len(self.all_users),
                                              total_score / len(self.all_users)))


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
