import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import decimal
import pandas as pd
import math
import numpy as np
import time

from recommender.models import Similarity
from analytics.models import Rating
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from datetime import datetime


class ItemSimilarityMatrixBuilder(object):

    def __init__(self, min_overlap=15):
        self.min_overlap = min_overlap

    def save_sparse_matrix(self, sm, index, created=datetime.now()):
        start_time = datetime.now()
        print('saving similarities (number:{})'.format(sm.shape[0]*sm.shape[1]))
        Similarity.objects.all().delete()
        sims = []
        no_saved = 0
        rows, cols = self.interesting_indexes(sm, 0)
        for row, col in zip(rows, cols):

            if len(sims) == 1000:
                Similarity.objects.bulk_create(sims)
                sims = []

            if row != col:
                new_similarity = Similarity(
                    created=created,
                    source=index[row],
                    target=index[col],
                    similarity=decimal.Decimal(str(sm[row, col]))
                )
                no_saved +=1
                sims.append(new_similarity)

        Similarity.objects.bulk_create(sims)
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    def interesting_indexes(self, sm, min_sim=0.2):

        cors = sm.tocoo()
        nz_mask = np.bitwise_and(~np.isnan(cors.data), cors.data > min_sim)
        return cors.row[nz_mask], cors.col[nz_mask]

    def build(self, ratings):

        print("Calculating similarities ... using {} ratings".format(len(ratings)))
        start_time = datetime.now()
        ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))
        ratings['avg'] = ratings['avg'].astype(float)

        print("normalized ratings.")

        rp = ratings.pivot_table(index=['movie_id'], columns=['user_id'], values='avg', fill_value=0)
        print("rating matrix finished, done in {} seconds".format(datetime.now() - start_time))

        sparsity_level = 1-(ratings.shape[0] / (rp.shape[0] * rp.shape[1]))
        print("sparsity level is ", sparsity_level)

        start_time = datetime.now()
        #cor = cosine_similarity(sparse.csr_matrix(rp.transpose()), dense_output=False)
        cor = sparse.csr_matrix(rp.transpose().corr(method='pearson', min_periods=self.min_overlap))
        print('correlation is finished, done in {} seconds'.format(datetime.now() - start_time))

        self.save_sparse_matrix(cor, rp.index)

        return cor


def normalize(x):
    x = x.astype(float)
    if x.std() == 0:
        return 0.0
    return (x - x.mean()) / (x.max() - x.min())


def split_ratings2(min_rank=3):
    print('loading ratings')
    ratings = Rating.objects.all()
    print('ranking ratings')
    df = pd.DataFrame.from_records(ratings.values())
    print(df.head())
    df['rank'] = df.groupby('user_id')['rating_timestamp'].rank(ascending=False)

    return df[df['rank'] <= min_rank]


def load_all_ratings():
    columns = ['user_id', 'movie_id', 'rating', 'type']

    ratings_data = Rating.objects.all().values(*columns)
    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    ratings['rating'] = ratings['rating'].astype(float)
    return ratings


if __name__ == '__main__':
    TEST = True

    if TEST:
        ratings = pd.DataFrame(
            [[1, '0011', 5, '2013-10-12 23:20:27+00:00'],
             [1, '12', 3, '2014-10-12 23:20:27+00:00'],
             [1, '14', 2, '2015-10-12 23:20:27+00:00'],
             [2, '0011', 4, '2013-10-12 23:20:27+00:00'],
             [2, '12', 3, '2014-10-12 23:20:27+00:00'],
             [2, '13', 4, '2015-10-12 23:20:27+00:00'],
             [3, '0011', 5, '2013-10-12 23:20:27+00:00'],
             [3, '12', 2, '2014-10-12 23:20:27+00:00'],
             [3, '13', 5, '2015-10-12 23:20:27+00:00'],
             [3, '14', 2, '2016-10-12 23:20:27+00:00'],
             [4, '0011', 3, '2013-10-12 23:20:27+00:00'],
             [4, '12', 5, '2014-10-12 23:20:27+00:00'],
             [4, '13', 3, '2015-10-12 23:20:27+00:00'],
             [5, '0011', 3, '2013-10-12 23:20:27+00:00'],
             [5, '12', 3, '2014-10-12 23:20:27+00:00'],
             [5, '13', 3, '2015-10-12 23:20:27+00:00'],
             [5, '14', 2, '2016-10-12 23:20:27+00:00'],
             [6, '0011', 2, '2013-10-12 23:20:27+00:00'],
             [6, '12', 3, '2014-10-12 23:20:27+00:00'],
             [6, '13', 2, '2015-10-12 23:20:27+00:00'],
             [6, '14', 3, '2016-10-12 23:20:27+00:00'],
             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

        result = ItemSimilarityMatrixBuilder(2).build(ratings)
        print(result)

    else:
        ItemSimilarityMatrixBuilder().build(load_all_ratings())
