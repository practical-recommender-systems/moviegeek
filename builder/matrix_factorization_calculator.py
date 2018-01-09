import logging
import os
import random
import sys
import pickle

import numpy as np
import pandas as pd
from decimal import Decimal
from collections import defaultdict
import math
from datetime import datetime

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django


django.setup()

from analytics.models import Rating


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


class MatrixFactorization(object):

    Regularization = Decimal(0.002)
    BiasLearnRate = Decimal(0.005)
    BiasReg = Decimal(0.002)

    LearnRate = Decimal(0.002)
    all_movies_mean = 0
    number_of_ratings = 0

    item_bias = None
    user_bias = None
    beta = 0.02

    iterations = 0

    def __init__(self, save_path, max_iterations=10):
        self.logger = logging.getLogger('funkSVD')
        self.save_path = save_path
        self.user_factors = None
        self.item_factors = None
        self.item_counts = None
        self.item_sum = None
        self.u_inx = None
        self.i_inx = None
        self.user_ids = None
        self.movie_ids = None

        self.all_movies_mean = 0.0
        self.number_of_ratings = 0
        self.MAX_ITERATIONS = max_iterations
        random.seed(42)

        ensure_dir(save_path)

    def initialize_factors(self, ratings, k=25):
        self.user_ids = set(ratings['user_id'].values)
        self.movie_ids = set(ratings['movie_id'].values)
        self.item_counts = ratings[['movie_id', 'rating']].groupby('movie_id').count()
        self.item_counts = self.item_counts.reset_index()

        self.item_sum = ratings[['movie_id', 'rating']].groupby('movie_id').sum()
        self.item_sum = self.item_sum.reset_index()

        self.u_inx = {r: i for i, r in enumerate(self.user_ids)}
        self.i_inx = {r: i for i, r in enumerate(self.movie_ids)}

        self.item_factors = np.full((len(self.i_inx), k), Decimal(0.1))
        self.user_factors = np.full((len(self.u_inx), k), Decimal(0.1))

        self.all_movies_mean = calculate_all_movies_mean(ratings)
        self.logger.info("user_factors are {}".format(self.user_factors.shape))
        self.user_bias = defaultdict(lambda: 0)
        self.item_bias = defaultdict(lambda: 0)

    def predict(self, user, item):

        pq = np.dot(self.item_factors[item], self.user_factors[user].T)
        b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
        prediction = b_ui + pq

        if prediction > 10:
            prediction = 10
        elif prediction < 1:
            prediction = 10
        return prediction

    def build(self, ratings, params):

        if params:
            k = params['k']
            self.save_path = params['save_path']

        self.train(ratings, k)

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

        for k in [15, 20, 30, 40, 50, 75, 100]:
            self.initialize_factors(ratings_df, k)
            self.logger.info("Training model with {} factors".format(k))
            self.log(str(k), "factor, iterations, train_mse, test_mse, time")

            test_data, train_data = self.split_data(10,
                                                    ratings_df)
            columns = ['user_id', 'movie_id', 'rating']
            ratings = train_data[columns].as_matrix()
            test = test_data[columns].as_matrix()

            self.MAX_ITERATIONS = 10
            iterations = 0
            index_randomized = random.sample(range(0, len(ratings)), (len(ratings) - 1))

            for factor in range(k):
                factor_iteration = 0
                factor_time = datetime.now()

                last_err = sys.maxsize
                last_test_mse = sys.maxsize
                finished = False

                while not finished:
                    train_mse = self.stocastic_gradient_descent(factor,
                                                                index_randomized,
                                                                ratings)

                    iterations += 1
                    test_mse = self.calculate_rmse(test, factor)

                    finished = self.finished(factor_iteration,
                                             last_err,
                                             train_mse,
                                             last_test_mse,
                                             test_mse)

                    last_err = train_mse
                    last_test_mse = test_mse
                    factor_iteration += 1

                    self.log(str(k), f"{factor}, {iterations}, {train_mse}, {test_mse}, {datetime.now() - factor_time}")

            self.save(k, False)

    def calculate_rmse(self, ratings, factor):

        def difference(row):
            user = self.u_inx[row[0]]
            item = self.i_inx[row[1]]

            pq = np.dot(self.item_factors[item][:factor + 1], self.user_factors[user][:factor + 1].T)
            b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
            prediction = b_ui + pq
            MSE = (prediction - Decimal(row[2])) ** 2
            return MSE

        squared = np.apply_along_axis(difference, 1, ratings).sum()
        return math.sqrt(squared / ratings.shape[0])

    def train(self, ratings_df, k=40):

        self.initialize_factors(ratings_df, k)
        self.logger.info("training matrix factorization at {}".format(datetime.now()))

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
                self.logger.info("epoch in {}, f={}, i={} err={}".format(datetime.now() - start_time,
                                                                       factor,
                                                                       iterations,
                                                                       iteration_err))
                finished = self.finished(iterations,
                                         last_err,
                                         iteration_err)
                last_err = iteration_err
            self.save(factor, finished)
            self.logger.info("finished factor {} on f={} i={} err={}".format(factor,
                                                                  datetime.now() - factor_time,
                                                                  iterations,
                                                                  iteration_err))

    def stocastic_gradient_descent(self, factor, index_randomized, ratings):

        lr = self.LearnRate
        b_lr = self.BiasLearnRate
        r = self.Regularization
        bias_r = self.BiasReg

        for inx in index_randomized:
            rating_row = ratings[inx]

            u = self.u_inx[rating_row[0]]
            i = self.i_inx[rating_row[1]]
            rating = Decimal(rating_row[2])

            err = (rating - self.predict(u, i))

            self.user_bias[u] += b_lr * (err - bias_r * self.user_bias[u])
            self.item_bias[i] += b_lr * (err - bias_r * self.item_bias[i])

            user_fac = self.user_factors[u][factor]
            item_fac = self.item_factors[i][factor]

            self.user_factors[u][factor] += lr * (err * item_fac
                                                  - r * user_fac)
            self.item_factors[i][factor] += lr * (err * user_fac
                                                  - r * item_fac)
        return self.calculate_rmse(ratings, factor)

    def finished(self, iterations, last_err, current_err,
                 last_test_mse=0.0, test_mse=0.0):

        if last_test_mse < test_mse or iterations >= self.MAX_ITERATIONS or last_err - current_err < 0.01:
            self.logger.info('Finish w iterations: {}, last_err: {}, current_err {}, lst_rmse {}, rmse {}'
                             .format(iterations, last_err, current_err, last_test_mse, test_mse))
            return True
        else:
            self.iterations += 1
            return False

    def save(self, factor, finished):

        save_path = self.save_path + '/model/'
        if not finished:
            save_path += str(factor) + '/'

        ensure_dir(save_path)

        self.logger.info("saving factors in {}".format(save_path))
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


def load_all_ratings(min_ratings=1):
    columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)

    user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
    user_count = user_count.reset_index()
    user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
    ratings = ratings[ratings['user_id'].isin(user_ids)]

    ratings['rating'] = ratings['rating'].astype(Decimal)
    return ratings


def calculate_all_movies_mean(ratings):
    avg = ratings['rating'].sum() / ratings.shape[0]
    return Decimal(avg)


if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    logger = logging.getLogger('funkSVD')
    logger.info("[BEGIN] Calculating matrix factorization")

    MF = MatrixFactorization(save_path='./models/funkSVD/{}/'.format(datetime.now()), max_iterations=40)
    loaded_ratings = load_all_ratings(20)
    logger.info("using {} ratings".format(loaded_ratings.shape[0]))
    #MF.meta_parameter_train(loaded_ratings)
    MF.train(load_all_ratings(), k=20)
    logger.info("[DONE] Calculating matrix factorization")
