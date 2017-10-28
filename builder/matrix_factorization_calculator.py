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


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class MatrixFactorization(object):
    Regularization = 0.02
    NumFactors = 3
    BiasLearnRate = 0.7
    BiasReg = 0.02
    FrequencyRegularization = 1
    LearnRate = 0.001
    k = 25
    all_movies_mean = 0
    number_of_ratings = 0

    item_bias = None
    user_bias = None
    beta = 0.02

    iterations = 0
    MINIMUM_IMPROVEMENT = 0.00001

    def __init__(self, save_path):
        self.save_path = save_path
        self.saved_predictions = None
        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.movie_ids = None

        self.all_movies_mean = 0.0
        self.number_of_ratings = 0
        self.MAX_ITERATIONS = 20

        ensure_dir(save_path)

    def initialize_factors(self, ratings, k=25):
        self.user_ids = set(ratings['user_id'].values)
        self.movie_ids = set(ratings['movie_id'].values)

        self.u_inx = {r: i for i, r in enumerate(self.user_ids)}
        self.i_inx = {r: i for i, r in enumerate(self.movie_ids)}

        self.saved_predictions = np.zeros((len(self.user_ids), len(self.user_ids)))
        # self.item_factors = 1 / k * np.random.randn(len(self.i_inx), k)
        self.item_factors = np.full((len(self.i_inx), k), 0.1)
        # self.user_factors = 1 / k * np.random.randn(len(self.u_inx), k)
        self.user_factors = np.full((len(self.u_inx), k), 0.1)

        self.all_movies_mean = self.calculate_all_movies_mean(ratings)
        print("user_factors are {}".format(self.user_factors.shape))
        self.user_bias = defaultdict(lambda: 0)
        self.item_bias = defaultdict(lambda: 0)

    def predict(self, user, item):

        pq = np.dot(self.item_factors[item],self.user_factors[user].T)
        b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
        prediction = b_ui + pq

        if prediction > 10:
            prediction = 10
        elif prediction < 1:
            prediction = 1
        return prediction

    def build(self, ratings, params):
        if params:
            k = params['k']
        self.train(ratings, k)

    def loss(self, factor, i, rating, u):

        prediction_error = (float(rating) - self.predict(u, i))

        return prediction_error

    def split_data(self, min_rank, ratings):

        users = self.user_ids

        train_data_len = int((len(users) * 70 / 100))
        test_users = set(random.sample(users, (len(users) - train_data_len)))
        train_users = users - test_users

        train = ratings[ratings['user_id'].isin(train_users)]
        test_temp = ratings[ratings['user_id'].isin(test_users)].sort_values('rating_timestamp', ascending=False)
        test = test_temp.groupby('user_id').head(min_rank)
        additional_training_data = test_temp[~test_temp.index.isin(test.index)]

        train = train.append(additional_training_data)

        return test, train

    def meta_parameter_train(self, ratings_df):

        for k in [15, 20, 30, 40, 50, 75, 100, 125, 150, 200]:
            self.initialize_factors(ratings_df, k)
            self.log(str(k), "factor, iterations, train_mse, test_mse, time")

            test_data, train_data = self.split_data(10,
                                                    ratings_df)
            columns = ['user_id', 'movie_id', 'rating']
            ratings = train_data[columns].as_matrix()
            test = test_data[columns].as_matrix()

            self.MAX_ITERATIONS = 100
            iterations = 0
            index_randomized = random.sample(range(0, len(ratings)), (len(ratings) - 1))

            for factor in range(k):
                factor_iteration = 0
                factor_time = datetime.now()

                last_err = sys.maxsize
                last_test_mse = sys.maxsize
                finished = False

                while not finished:
                    start_time = datetime.now()
                    train_mse = self.stocastic_gradient_descent(factor,
                                                                index_randomized,
                                                                ratings)

                    iterations += 1
                    test_mse = self.calculate_mse(test, factor)

                    finished = self.finished(factor_iteration,
                                             last_err,
                                             train_mse,
                                             last_test_mse,
                                             test_mse)

                    last_err = train_mse
                    last_test_mse = test_mse
                    factor_iteration += 1

                    self.log(str(k), f"{factor}, {iterations}, {train_mse}, {test_mse}, {datetime.now() - factor_time}")

                self.save(factor, finished)

    def calculate_mse(self, ratings, factor):

        def difference(row):
            user = self.u_inx[row[0]]
            item = self.i_inx[row[1]]

            pq = np.dot(self.item_factors[item][:factor], self.user_factors[user][:factor].T)
            b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
            prediction = b_ui + pq

            return (prediction - float(row[2])) ** 2

        squared = np.apply_along_axis(difference, 1, ratings).sum()
        return squared / ratings.shape[0]

    def train(self, ratings_df, k=40):

        self.initialize_factors(ratings_df, k)
        print("training matrix factorization at {}".format(datetime.now()))

        ratings = ratings_df[['user_id', 'movie_id', 'rating']].as_matrix()

        index_randomized = random.sample(range(0, len(ratings)), (len(ratings) - 1))

        for factor in range(k):
            factor_time = datetime.now()
            iterations = 0
            last_err = sys.maxsize
            iteration_err = sys.maxsize
            finished = False

            while not finished:
                start_time = datetime.now()
                iteration_err = self.stocastic_gradient_descent(factor,
                                                              index_randomized,
                                                              ratings)


                iterations += 1
                print("one epoch in {} on f={} i={} err={}".format(datetime.now() - start_time,
                                                                   factor,
                                                                   iterations,
                                                                   iteration_err))
                finished = self.finished(iterations,
                                         last_err,
                                         iteration_err)
                last_err = iteration_err
            self.save(factor, finished)
            print("finished factor {} on f={} i={} err={}".format(factor,
                                                                  datetime.now() - factor_time,
                                                                  iterations,
                                                                  iteration_err))

    def stocastic_gradient_descent(self, factor, index_randomized, ratings):

        lr = self.LearnRate
        r = self.Regularization
        bias_r = self.BiasReg

        current_err = 0
        for inx in index_randomized:
            rating_row = ratings[inx]

            u = self.u_inx[rating_row[0]]
            i = self.i_inx[rating_row[1]]
            rating = rating_row[2]

            err = (float(rating) - self.predict(u, i))

            self.user_bias[u] += lr * (err - bias_r * self.user_bias[u])
            self.item_bias[i] += lr * (err - bias_r * self.item_bias[i])

            user_fac = self.user_factors[u][factor].copy()
            item_fac = self.item_factors[i][factor].copy()

            self.user_factors[u][factor] += lr * (err * item_fac
                                                  - r * user_fac)
            self.item_factors[i][factor] += lr * (err * user_fac
                                                  - r * item_fac)
        return self.calculate_mse(ratings, factor)

    def finished(self, iterations, last_err, current_err,
                 last_test_mse=0, test_mse=0):

        if last_test_mse < test_mse or iterations >= self.MAX_ITERATIONS or last_err < current_err:
            print('Finish w iterations: {}, last_err: {}, current_err {}'
                  .format(iterations, last_err, current_err))
            return True
        else:
            self.iterations += 1
            return False

    def calculate_all_movies_mean(self, ratings):

        avg = ratings['rating'].sum() / ratings.shape[0]
        return float(avg)

    def save(self, factor, finished):

        save_path = self.save_path + '/model/'
        if not finished:
            save_path += str(factor) + '/'

        ensure_dir(save_path)

        print("saving factors in {}".format(save_path))
        user_bias = {uid: self.user_bias[self.u_inx[uid]] for uid in self.u_inx.keys()}
        item_bias = {iid: self.item_bias[self.i_inx[iid]] for iid in self.i_inx.keys()}

        uf = pd.DataFrame(self.user_factors,
                          index=self.user_ids)
        it_f = pd.DataFrame(self.item_factors,
                            index=self.movie_ids)

        with open(save_path + 'user_factors.json', 'w') as outfile:
            outfile.write(uf.to_json())
        with open(save_path + 'item_factors.json', 'w') as outfile:
            outfile.write(it_f.to_json())
        with open(save_path + 'user_bias.data', 'wb') as ub_file:
            pickle.dump(user_bias, ub_file)
        with open(save_path + 'item_bias.data', 'wb') as ub_file:
            pickle.dump(item_bias, ub_file)

    def log(self, filename, logtext):
        path = self.save_path + '/meta/' + filename + '.csv'
        ensure_dir(path)

        with open(path, 'a') as log_file:
            log_file.write(logtext + '\n')


def load_all_ratings():
    columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    ratings['rating'] = ratings['rating'].astype(float)
    return ratings


if __name__ == '__main__':
    print("Calculating matrix factorization...")

    MF = MatrixFactorization(save_path='./models/prod/')
    # MF.meta_parameter_train(load_all_ratings())
    MF.train(load_all_ratings(), k=40)
