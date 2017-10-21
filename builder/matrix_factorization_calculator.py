import os
import sys
import random

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Avg, Count

from scipy.sparse import coo_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import pickle

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json
import decimal

from collections import defaultdict
import math
from datetime import datetime

from builder import data_helper

django.setup()

from analytics.models import Rating, Cluster
from moviegeeks.models import Movie
from recommender.models import Recs


class MatrixFactorization(object):
    Regularization = 0.015
    NumFactors = 3
    BiasLearnRate = 0.7
    BiasReg = 0.33
    FrequencyRegularization = 1
    LearnRate = 0.01
    k = 25
    all_movies_mean = 0
    number_of_ratings = 0

    item_bias = None
    user_bias = None
    beta = 0.02

    iterations = 0
    MINIMUM_IMPROVEMENT = 0.01

    def __init__(self, save_path):
        self.save_path = save_path

        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.movie_ids = None

        self.all_movies_mean = 0.0
        self.number_of_ratings = 0
        self.MAX_ITERATIONS = 25

    def initialize_factors(self, ratings, k=25):
        self.k = k
        self.user_ids = set(ratings['user_id'].values)
        self.movie_ids = set(ratings['movie_id'].values)

        num_users = len(self.user_ids)
        num_items = len(self.movie_ids)

        self.all_movies_mean = self.calculate_all_movies_mean()

        self.item_factors = pd.DataFrame(np.random.normal(scale=1. / self.k,
                                                          size=(num_items, self.k)),
                                         index=self.movie_ids)
        self.user_factors = pd.DataFrame(np.random.normal(scale=1. / self.k,
                                                          size=(num_users, self.k)),
                                         index=self.user_ids)
        self.user_bias = defaultdict(lambda: 0)
        self.item_bias = defaultdict(lambda: 0)
        print('initialized factors, items: {}, users: {}'.format(num_items, num_users))


    def predict(self, user, item):
        pq = self.item_factors.loc[item].dot(self.user_factors.loc[user])
        b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
        rating = b_ui + pq
        if rating > 10:
            rating = 10
        elif rating < 1:
            rating = 1
        return rating

    def build(self, ratings, params):
        if params:
            k = params['k']
        self.train(ratings, k)

    def train(self, ratings, k=25):

        self.initialize_factors(ratings, k)
        print("training matrix factorization")

        lr = self.LearnRate
        r = self.Regularization

        iterations = 0
        last_err = 0
        iteration_err = sys.maxsize

        while not self.finished(iterations, last_err, iteration_err):
            start_time = datetime.now()
            last_err = iteration_err
            current_err = 0
            index_randomized = random.sample(ratings.index.tolist(), len(ratings.index))

            for inx in index_randomized:
                user_rating = ratings.ix[inx]
                u = user_rating['user_id']
                i = user_rating['movie_id']
                rating = user_rating['rating']

                current_err, err = self.loss(current_err, i, rating, u)

                self.user_bias[u] += lr * (err - r * self.user_bias[u])
                self.item_bias[i] += lr * (err - r * self.item_bias[i])

                user_fac = self.user_factors.loc[u].copy()
                item_fac = self.item_factors.loc[i].copy()

                self.user_factors.loc[u] += lr * (err * item_fac
                                                  - r * user_fac)
                self.item_factors.loc[i] += lr * (err * user_fac
                                                  - r * item_fac)

            iteration_err = math.sqrt(current_err / ratings.shape[0])
            iterations += 1

            self.save()
            print("finished iteration {} in {}, iteration error was {}".format(iterations - 1,
                                                                               datetime.now() - start_time,
                                                                               iteration_err))

    def loss(self, current_err, i, rating, u):

        r = self.Regularization
        p = self.item_factors.loc[str(i)]
        q = self.user_factors.loc[u]
        p_two = p.T.dot(p).sum()
        q_two = q.T.dot(q).sum()

        prediction_error = float(rating) - self.predict(u, i)
        regularization_error = r * (q_two + p_two)

        current_err += math.pow(prediction_error + regularization_error, 2)

        return current_err, prediction_error

    def finished(self, iterations, last_err, current_err):

        if iterations >= self.MAX_ITERATIONS or abs(last_err - current_err) < self.MINIMUM_IMPROVEMENT:
            print('Finish w iterations: {}, last_err: {}, current_err {}'
                  .format(iterations, last_err, current_err))
            return True
        else:
            self.iterations += 1
            return False

    def calculate_all_movies_mean(self):
        #todo: mean of the actual ratings, not the ones in the database
        avg = Rating.objects.all().aggregate(Avg('rating')).values()
        return list(avg)[0]


    def save(self):

        print("global mean: {}".format(self.all_movies_mean))

        print("saving factors")

        with open(self.save_path +'user_factors.json', 'w') as outfile:
            outfile.write(self.user_factors.to_json())
        with open(self.save_path +'item_factors.json', 'w') as outfile:
            outfile.write(self.item_factors.to_json())

        with open(self.save_path +'user_bias.data', 'wb') as ub_file:
            pickle.dump(dict(self.user_bias), ub_file)

        with open(self.save_path +'item_bias.data', 'wb') as ub_file:
            pickle.dump(dict(self.item_bias), ub_file)

def load_all_ratings():
    columns = ['user_id', 'movie_id', 'rating', 'type']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    ratings['rating'] = ratings['rating'].astype(float)
    return ratings

if __name__ == '__main__':
    print("Calculating matrix factorization...")

    MF = MatrixFactorization(save_path='./models/funk_svd/')
    MF.train(load_all_ratings())
