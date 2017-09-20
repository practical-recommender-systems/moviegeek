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
from scipy.sparse import coo_matrix
from datetime import datetime

import psycopg2

class ItemSimilarityMatrixBuilder(object):
    def __init__(self, min_overlap=15, min_sim=0.2):
        self.min_overlap = min_overlap
        self.min_sim = min_sim

    def save_similarities(self, sm, index, created=datetime.now()):
        start_time = datetime.now()

        print(f'truncating table in {datetime.now() - start_time} seconds')
        sims = []
        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(sm)
        csr = coo.tocsr()

        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')

        query = "insert into similarity (created, source, target, similarity) values %s;"

        conn = psycopg2.connect("dbname=moviegeek user=postgres password=hullo1!")
        cur = conn.cursor()

        cur.execute('truncate table similarity')

        print(f'{coo.count_nonzero()} similarities to save')
        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):

            if x == y:
                continue

            sim = csr[x, y]

            if sim < self.min_sim:
                continue

            if len(sims) == 500000:
                psycopg2.extras.execute_values(cur, query, sims)
                sims = []
                print(f"{no_saved} saved in {datetime.now() - start_time}")

            new_similarity = (str(created), index[x], index[y], sim)
            no_saved += 1
            sims.append(new_similarity)

        psycopg2.extras.execute_values(cur, query, sims, template=None, page_size=1000)
        conn.commit()
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    def save_with_django(self, sm, index, created=datetime.now()):
        start_time = datetime.now()
        Similarity.objects.all().delete()
        print(f'truncating table in {datetime.now() - start_time} seconds')
        sims = []
        no_saved = 0
        start_time = datetime.now()
        coo = coo_matrix(sm)
        csr = coo.tocsr()

        print(f'instantiation of coo_matrix in {datetime.now() - start_time} seconds')
        print(f'{coo.count_nonzero()} similarities to save')
        xs, ys = coo.nonzero()
        for x, y in zip(xs, ys):

            if x == y:
                continue

            sim = csr[x, y]

            if sim < self.min_sim:
                continue

            if len(sims) == 500000:

                Similarity.objects.bulk_create(sims)
                sims = []
                print(f"{no_saved} saved in {datetime.now() - start_time}")

            new_similarity = Similarity(
                source=index[x],
                target=index[y],
                created=created,
                similarity=sim
            )
            no_saved += 1
            sims.append(new_similarity)

        Similarity.objects.bulk_create(sims)
        print('{} Similarity items saved, done in {} seconds'.format(no_saved, datetime.now() - start_time))

    def build(self, ratings, save=True):

        print("Calculating similarities ... using {} ratings".format(len(ratings)))
        start_time = datetime.now()

        print("create ratings matrix")
        ratings['rating'] = ratings['rating'].astype(float)
        ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))

        ratings['avg'] = ratings['avg'].astype(float)
        ratings['user_id'] = ratings['user_id'].astype('category')
        ratings['movie_id'] = ratings['movie_id'].astype('category')


        coo = coo_matrix((ratings['avg'].astype(float),
                          (ratings['user_id'].cat.codes.copy(),
                           ratings['movie_id'].cat.codes.copy())))

        print("normalized ratings.")
        overlap_matrix = coo.transpose().astype(bool).astype(int).dot(coo.astype(bool).astype(int))

        print(
            f"rating matrix (size {coo.shape[0]}x{coo.shape[1]})finished, done in {datetime.now() - start_time} seconds")

        sparsity_level = 1 - (ratings.shape[0] / (coo.shape[0] * coo.shape[1]))
        print("sparsity level is ", sparsity_level)

        start_time = datetime.now()
        cor = cosine_similarity(coo.transpose(), dense_output=False)
        # cor = rp.corr(method='pearson', min_periods=self.min_overlap)
        # cor = (cosine(rp.T))

        cor = cor.multiply(cor > self.min_sim)
        cor = cor.multiply(overlap_matrix > self.min_overlap)

        movies = dict(enumerate(ratings['movie_id'].cat.categories))
        print(f'correlation is finished, done in {datetime.now() - start_time} seconds')
        if save:

            start_time = datetime.now()
            print('save starting')
            self.save_similarities(cor, movies)
            print('save finished, done in {} seconds'.format(datetime.now() - start_time))

        return cor, movies


def normalize(x):
    x = x.astype(float)
    x_sum = x.sum()
    x_num = x.astype(bool).sum()
    x_mean = x_sum / x_num

    if x.std() == 0:
        return 0.0
    return (x - x_mean) / (x.max() - x.min())


def load_all_ratings():
    columns = ['user_id', 'movie_id', 'rating', 'type']

    ratings_data = Rating.objects.all().values(*columns)
    ratings = pd.SparseDataFrame.from_records(ratings_data, columns=columns)
    ratings['rating'] = ratings['rating'].astype(float)
    return ratings


if __name__ == '__main__':
    all_ratings = load_all_ratings()
    ItemSimilarityMatrixBuilder().build(all_ratings)
