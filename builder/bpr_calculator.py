import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

from datetime import datetime
import logging
import numpy as np
from math import exp
import random
import pandas as pd
from decimal import Decimal
from collections import defaultdict
import django
django.setup()

from analytics.models import Rating


class BayesianPersonalizationRanking(object):

    Regularization = 0.015
    NumFactors = 3
    BiasLearnRate = 0.7
    BiasReg = 0.33
    RegU = 0.0025
    RegI = 0.0025
    FrequencyRegularization = 1
    LearnRate = 0.01
    k = 3
    all_movies_mean = 0
    number_of_ratings = 0

    item_factors = None
    user_factors = None
    item_bias = None
    user_bias = None


    def __init__(self, save_path):
        self.save_path = save_path
        self.saved_predictions = None
        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.movie_ids = None
        self.ratings = None

        self.learning_rate = 0.05
        self.bias_regularization = 1.0
        self.user_regularization = 0.0025
        self.positive_item_regularization = 0.0025
        self.negative_item_regularization = 0.00025

        self.all_movies_mean = 0.0
        self.number_of_ratings = 0

    def initialize_factors(self, train_data, k=25):
        self.ratings = train_data[['user_id', 'movie_id', 'rating']].as_matrix()
        self.k = k
        self.user_ids = set(train_data['user_id'].values)
        self.movie_ids = set(train_data['movie_id'].values)

        self.u_inx = {r: i for i, r in enumerate(self.user_ids)}
        self.i_inx = {r: i for i, r in enumerate(self.movie_ids)}

        self.saved_predictions = np.zeros((len(self.user_ids), len(self.user_ids)))
        self.item_factors = np.full((len(self.movie_ids), k), 0.1)
        self.user_factors = np.full((len(self.user_ids), k), 0.1)

        self.item_bias = defaultdict(lambda: 0)
        self.create_loss_samples()

    def train(self, train_data, k=25, num_iterations=4):

        self.initialize_factors(train_data, k)

        for iteration in range(num_iterations):
            logger.debug('iteration {} loss {}'.format(iteration, self.loss()))
            logger.debug('User factor [{}]: {}'.format(5, self.user_factors[5]))
            logger.debug('Item factor [{}]: {}'.format(5, self.item_factors[5]))

            for usr, pos, neg in self.draw(self.ratings.shape[0]):
                self.step(usr, pos, neg)

    def step(self, u, i, j):

        lr = self.LearnRate
        ur = self.user_regularization
        pir = self.positive_item_regularization
        nir = self.negative_item_regularization

        ib = self.item_bias[i]
        jb = self.item_bias[j]

        u_dot_i = np.dot(self.user_factors[u],
                         self.item_factors[i, :] - self.item_factors[j, :])
        x = ib - jb + u_dot_i

        z = 1.0/(1.0 + exp(x))

        ib_update = z - self.BiasReg * ib
        self.item_bias[i] += lr * ib_update

        jb_update = - z - self.BiasReg * jb
        self.item_bias[j] += lr * jb_update

        update_u = (self.item_factors[i,:] - self.item_factors[j,:]) * z - ur *self.user_factors[u,:]
        self.user_factors[u,:] += lr * update_u

        update_i = self.user_factors[u,:] * z - pir * self.item_factors[i,:]
        self.item_factors[i,:] += lr * update_i

        update_j = -self.user_factors[u,:] * z - nir * self.item_factors[j,:]
        self.item_factors[j,:] += lr * update_j

    def loss(self):
        br = self.bias_regularization
        ur = self.user_regularization
        pir = self.positive_item_regularization
        nir = self.negative_item_regularization

        ranking_loss = 0
        for u, i, j in self.loss_samples:
            x = self.predict(u, i) - self.predict(u, j)
            ranking_loss += 1.0 / (1.0 + exp(x))

        c = 0
        for u, i, j in self.loss_samples:

            c += ur * np.dot(self.user_factors[u], self.user_factors[u])
            c += pir * np.dot(self.item_factors[i], self.item_factors[i])
            c += nir * np.dot(self.item_factors[j], self.item_factors[j])
            c += br * self.item_bias[i] ** 2
            c += br * self.item_bias[j] ** 2

        return ranking_loss + 0.5 * c

    def predict(self, user, item):
        pq = self.item_factors[item].dot(self.user_factors[user])

        return pq + self.item_bias[item]

    def create_loss_samples(self):

        num_loss_samples = int(100 * len(self.user_ids) ** 0.5)
        logger.debug("[BEGIN]building {} loss samples".format(num_loss_samples))

        self.loss_samples = [t for t in self.draw(num_loss_samples)]
        logger.debug("[END]building {} loss samples".format(num_loss_samples))

    def draw(self, no):
        if no == -1:
            no = self.ratings.nnz
        r_size = self.ratings.shape[0] - 1
        size = min(no, r_size)
        index_randomized = random.sample(range(0, r_size), size)
        for i in index_randomized:
            r = self.ratings[i]
            u = r[0]
            pos = r[1]

            user_items = self.ratings[self.ratings[:, 0] == u]
            neg = pos
            while neg in user_items:
                i2 = random.randint(0, r_size)
                r2 = self.ratings[i2]
                neg = r2[1]

            yield self.u_inx[u], self.i_inx[pos], self.i_inx[neg]

def load_all_ratings(min_ratings=1):
    columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)

    # user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
    # user_count = user_count.reset_index()
    # user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
    # ratings = ratings[ratings['user_id'].isin(user_ids)]
    item_count = ratings[['movie_id', 'rating']].groupby('movie_id').count()

    item_count = item_count.reset_index()
    item_ids = item_count[item_count['rating'] > min_ratings]['movie_id']
    ratings = ratings[ratings['movie_id'].isin(item_ids)]

    ratings['rating'] = ratings['rating'].astype(Decimal)
    return ratings

if __name__  == '__main__':

    number_of_factors = 10
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('BPR calculator')

    train_data = load_all_ratings(0)[:10000]
    bpr = BayesianPersonalizationRanking(save_path='./models/bpr/{}/'.format(datetime.now()))
    bpr.train(train_data, 10, 20)



