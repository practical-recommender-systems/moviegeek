import os
import logging


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")
import django
django.setup()

import pickle
from tqdm import tqdm
from datetime import datetime
from math import exp

import random
import pandas as pd
import numpy as np

from decimal import Decimal
from collections import defaultdict

from analytics.models import Rating

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
logger = logging.getLogger('BPR calculator')

class BayesianPersonalizationRanking(object):

    def __init__(self, save_path):

        self.save_path = save_path
        self.user_factors = None
        self.item_factors = None
        self.user_ids = None
        self.movie_ids = None
        self.ratings = None
        self.user_movies = None
        self.error = 0

        self.learning_rate = 0.05
        self.bias_regularization = 0.002
        self.user_regularization = 0.005
        self.positive_item_regularization = 0.003
        self.negative_item_regularization = 0.0003


    def initialize_factors(self, train_data, k=25):
        self.ratings = train_data[['user_id', 'movie_id', 'rating']].as_matrix()
        self.k = k
        self.user_ids = pd.unique(train_data['user_id'])
        self.movie_ids = pd.unique(train_data['movie_id'])

        self.u_inx = {r: i for i, r in enumerate(self.user_ids)}
        self.i_inx = {r: i for i, r in enumerate(self.movie_ids)}

        self.user_factors = np.random.random_sample((len(self.user_ids), k))
        self.item_factors = np.random.random_sample((len(self.movie_ids), k))
        self.user_movies = train_data.groupby('user_id')['movie_id'].apply(lambda x: x.tolist()).to_dict()
        self.item_bias = defaultdict(lambda: 0)
        self.create_loss_samples()

    def build(self, ratings, params):

        if params:
            k = params['k']
            num_iterations = params['num_iterations']

        self.train(ratings, k, num_iterations)

    def train(self, train_data, k=25, num_iterations=4):

        self.initialize_factors(train_data, k)
        for iteration in tqdm(range(num_iterations)):
            self.error = self.loss()

            logger.debug('iteration {} loss {}'.format(iteration, self.error))

            for usr, pos, neg in self.draw(self.ratings.shape[0]):
                self.step(usr, pos, neg)

            self.save(iteration, iteration == num_iterations - 1)

    def step(self, u, i, j):

        lr = self.learning_rate
        ur = self.user_regularization
        br = self.bias_regularization
        pir = self.positive_item_regularization
        nir = self.negative_item_regularization

        ib = self.item_bias[i]
        jb = self.item_bias[j]

        u_dot_i = np.dot(self.user_factors[u, :],
                         self.item_factors[i, :] - self.item_factors[j, :])
        x = ib - jb + u_dot_i

        z = 1.0/(1.0 + exp(x))

        ib_update = z - br * ib
        self.item_bias[i] += lr * ib_update

        jb_update = - z - br * jb
        self.item_bias[j] += lr * jb_update

        update_u = ((self.item_factors[i,:] - self.item_factors[j,:]) * z
                    - ur * self.user_factors[u,:])
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
        i_fac = self.item_factors[item]
        u_fac = self.user_factors[user]
        pq = i_fac.dot(u_fac)

        return pq + self.item_bias[item]

    def create_loss_samples(self):

        num_loss_samples = int(100 * len(self.user_ids) ** 0.5)
        logger.debug("[BEGIN]building {} loss samples".format(num_loss_samples))

        self.loss_samples = [t for t in self.draw(num_loss_samples)]
        logger.debug("[END]building {} loss samples".format(num_loss_samples))

    def draw(self, no):

        for _ in range(no):
            u = random.choice(self.user_ids)
            user_items = self.user_movies[u]

            pos = random.choice(user_items)

            neg = pos
            while neg in user_items:
                neg = random.choice(self.movie_ids)

            yield self.u_inx[u], self.i_inx[pos], self.i_inx[neg]

    def save(self, factor, finished):

        save_path = self.save_path + '/model/'
        if not finished:
            save_path += str(factor) + '/'

        ensure_dir(save_path)

        logger.info("saving factors in {}".format(save_path))
        item_bias = {iid: self.item_bias[self.i_inx[iid]] for iid in self.i_inx.keys()}

        uf = pd.DataFrame(self.user_factors,
                          index=self.user_ids)
        it_f = pd.DataFrame(self.item_factors,
                            index=self.movie_ids)

        with open(save_path + 'user_factors.json', 'w') as outfile:
            outfile.write(uf.to_json())
        with open(save_path + 'item_factors.json', 'w') as outfile:
            outfile.write(it_f.to_json())
        with open(save_path + 'item_bias.data', 'wb') as ub_file:
            pickle.dump(item_bias, ub_file)

def load_all_ratings(min_ratings=1):
    columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)

    item_count = ratings[['movie_id', 'rating']].groupby('movie_id').count()

    item_count = item_count.reset_index()
    item_ids = item_count[item_count['rating'] > min_ratings]['movie_id']
    ratings = ratings[ratings['movie_id'].isin(item_ids)]

    ratings['rating'] = ratings['rating'].astype(Decimal)
    return ratings


def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

if __name__ == '__main__':

    number_of_factors = 10
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('BPR calculator')

    train_data = load_all_ratings(1)
    bpr = BayesianPersonalizationRanking(save_path='./models/bpr/{}/'.format(datetime.now()))
    bpr.train(train_data, 10, 20)



