import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import decimal
import pandas as pd
import numpy as np

from recommender.models import Similarity
from analytics.models import Rating
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from datetime import datetime


class ItemSimilarityMatrixBuilder(object):

    def __init__(self, min_overlap=15, min_sim=0.2):
        self.min_overlap = min_overlap
        self.min_sim = min_sim

    def save_sparse_matrix(self, sm, index, created=datetime.now()):
        start_time = datetime.now()
        Similarity.objects.all().delete()
        sims = []
        no_saved = 0

        for i in sm.itertuples():
            for j in range(1, len(i)):
                row = i[0]
                col = sm.columns[j - 1]
                sim = i[j]
                if sim > self.min_sim:

                    if len(sims) == 100000:
                        Similarity.objects.bulk_create(sims)
                        sims = []

                    if row != col:
                        new_similarity = Similarity(
                            created=created,
                            source=row,
                            target=col,
                            similarity=decimal.Decimal(str(sim))
                        )
                        no_saved +=1
                        sims.append(new_similarity)

        Similarity.objects.bulk_create(sims)
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    def build(self, ratings, save=True):

        print("Calculating similarities ... using {} ratings".format(len(ratings)))
        start_time = datetime.now()

        ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))
        ratings['avg'] = ratings['avg'].astype(float)

        print("normalized ratings.")

        rp = ratings.pivot_table(index=['movie_id'], columns=['user_id'], values='avg', fill_value=0)

        rp = rp.transpose()
        items_to_keep = rp.astype(bool).sum(axis=0) > self.min_overlap

        for i, column in zip(rp.columns, items_to_keep):
            if not column:
                rp.drop(i, axis=1, inplace=True)

        print(
            f"rating matrix (size {rp.shape[0]}x{rp.shape[1]})finished, done in {datetime.now() - start_time} seconds")

        sparsity_level = 1-(ratings.shape[0] / (rp.shape[0] * rp.shape[1]))
        print("sparsity level is ", sparsity_level)

        start_time = datetime.now()
        #cor = cosine_similarity(sparse.csr_matrix(rp.transpose()), dense_output=False)
        #cor = rp.corr(method='pearson', min_periods=self.min_overlap)
        cor = sparse.csr_matrix(cosine(rp.transpose()))
        print(f'correlation is finished, done in {datetime.now() - start_time} seconds')
        if save:
            start_time = datetime.now()

            self.save_sparse_matrix(cor, rp.transpose().index)
            print('save finished, done in {} seconds'.format(datetime.now() - start_time))

        return cor


def cosine(A):
    similarity = np.dot(A, A.T)

    # squared magnitude of preference vectors (number of occurrences)
    square_mag = np.diag(similarity)

    # inverse squared magnitude
    inv_square_mag = 1 / square_mag

    # if it doesn't occur, set it's inverse magnitude to zero (instead of inf)
    inv_square_mag[np.isinf(inv_square_mag)] = 0

    # inverse of the magnitude
    inv_mag = np.sqrt(inv_square_mag)

    # cosine similarity (elementwise multiply by inverse magnitudes)
    cosine = similarity * inv_mag
    return cosine.T * inv_mag

def normalize(x):

    x = x.astype(float)
    x_sum = x.sum()
    x_num = x.astype(bool).sum()
    x_mean = x_sum / x_num

    if x.std() == 0:
        return 0.0
    return (x - x_mean) / (x.max() - x.min())


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
    ratings = pd.SparseDataFrame.from_records(ratings_data, columns=columns)
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
