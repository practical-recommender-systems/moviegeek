import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Avg, Count

from scipy.sparse import dok_matrix
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

from builder import data_helper

db = './../db.sqlite3'

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
    k = 3
    all_movies_mean = 0
    number_of_ratings = 0

    item_factors = None
    user_factors = None
    item_bias = None
    user_bias = None

    iterations = 0

    def __init__(self):

        self.ratings = Rating.objects.all()[:1000]
        self.initialize_factors()
        self.all_movies_mean = self.calculate_all_movies_mean()
        self.number_of_ratings = self.calculate_number_of_ratings

    def initialize_factors(self):

        self.user_ids = set(['u'+str(i.user_id) for i in self.ratings])
        self.movie_ids = set(['i'+str(i.movie_id) for i in Movie.objects.all()])
        num_users = len(self.user_ids)
        num_items = len(self.movie_ids)

        self.item_factors = pd.DataFrame(np.random.ranf(size=(self.k, num_items)), columns=self.movie_ids)
        self.user_factors = pd.DataFrame(np.random.ranf(size=(self.k, num_users)), columns=self.user_ids)
        print(self.user_factors.columns)
        self.user_bias = defaultdict(lambda: 10)
        self.item_bias = defaultdict(lambda: 10)
        print('initialized factors, items: {}, users: {}'.format(num_items, num_users))

    def predict(self, user, item):
        pq = self.item_factors[item].dot(self.user_factors[user])
        b_ui = self.all_movies_mean + self.user_bias[user] + self.item_bias[item]
        return b_ui + pq

    def train(self):
        print("training matrix factorization")

        lr = self.LearnRate
        r = self.Regularization

        for f in range(self.k):
            print('finding factor {}'.format(f))

            iterations = 0
            last_err = 0
            current_err = sys.maxsize
            while not self.finished(iterations, last_err, current_err):
                last_err = current_err
                current_err = 0

                for user_rating in self.ratings.iterator():
                    u = 'u' + str(user_rating.user_id)
                    i = 'i' + str(user_rating.movie_id)
                    rating = user_rating.rating

                    err = float(rating) - self.predict(u, i)
                    current_err += math.pow(err, 2)

                    self.user_bias[u] += lr * (err - r * self.user_bias[u])
                    self.item_bias[i] += lr * (err - r * self.item_bias[i])

                    user_factor = self.user_factors[u][f]
                    item_factor = self.item_factors[i][f]

                    self.user_factors[u][f] += lr * (err * item_factor
                                                     - r * user_factor)
                    self.item_factors[i][f] += lr * (err * user_factor
                                                     - r * item_factor)
                current_err = math.sqrt(current_err/self.ratings.count())
                print("{},{}\n".format(self.iterations, current_err))
                iterations += 1

        #save
        self.save()

    def finished(self, iterations, last_err, current_err):

        if iterations >= 5 or abs(last_err-current_err) < 1:
            print('Finish w iterations: {}, last_err: {}, current_err {}'
                  .format(iterations, last_err, current_err))
            return True
        else:
            self.iterations += 1
            return False

    def calculate_all_movies_mean(self):
        avg = Rating.objects.all().aggregate(Avg('rating')).values()
        return list(avg)[0]

    def calculate_number_of_ratings(self):
        return Rating.objects.all().aggregate(Count()).values()[0]

    def save(self):

        thresshold = 1

        print("global mean: {}".format(self.all_movies_mean))

        for user in self.user_ids:
            for item in self.movie_ids:
                prediction = self.predict(user, item)

                if prediction > thresshold:
                    Recs(
                        user=user,
                        item=item,
                        rating=prediction
                    ).save()

        print("saving factors")

        with open('user_factors.json', 'w') as outfile:
            outfile.write(self.user_factors.to_json())
        with open('item_factors.json', 'w') as outfile:
            outfile.write(self.item_factors.to_json())

        with open('user_bias.data', 'wb') as ub_file:
            pickle.dump(dict(self.user_bias), ub_file)

        with open('item_bias.data', 'wb') as ub_file:
            pickle.dump(dict(self.item_bias), ub_file)

if __name__ == '__main__':
    print("Calculating user clusters...")

    MF = MatrixFactorization()
    MF.train()
