import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import pandas as pd

from recommender.models import Similarity
from analytics.models import Rating
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import coo_matrix
from datetime import datetime
from prs_project import settings
import psycopg2
import sqlite3


class ItemSimilarityMatrixBuilder(object):

    def __init__(self, min_overlap=15, min_sim=0.2):
        self.min_overlap = min_overlap
        self.min_sim = min_sim
        self.db = settings.DATABASES['default']['ENGINE']

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

        conn= self.get_conn()
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

    @staticmethod
    def get_conn():
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
            dbUsername = settings.DATABASES['default']['USER']
            dbPassword = settings.DATABASES['default']['PASSWORD']
            dbName = settings.DATABASES['default']['NAME']
            conn_str = "dbname={} user={} password={}".format(dbName,
                                                              dbUsername,
                                                              dbPassword)
            conn = psycopg2.connect(conn_str)
        elif settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            dbName = settings.DATABASES['default']['NAME']
            conn = sqlite3.connect(dbName)

        return conn

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
                          (ratings['movie_id'].cat.codes.copy(),
                           ratings['user_id'].cat.codes.copy())))

        print("calculating overlaps between the items")
        overlap_matrix = coo.astype(bool).astype(int).dot(coo.transpose().astype(bool).astype(int))
        print(f"overlap matrix leaves {(overlap_matrix > self.min_overlap).count_nonzero()} out of {overlap_matrix.count_nonzero()} with {self.min_overlap}")
        for i in range(0, self.min_overlap + 1):
            print(f"{i}, {(overlap_matrix > i).count_nonzero()}")
        print()
        print(f"rating matrix (size {coo.shape[0]}x{coo.shape[1]})finished,",
            f" done in {datetime.now() - start_time} seconds")

        sparsity_level = 1 - (ratings.shape[0] / (coo.shape[0] * coo.shape[1]))
        print("sparsity level is ", sparsity_level)

        start_time = datetime.now()
        cor = cosine_similarity(coo, dense_output=False)
        # cor = rp.corr(method='pearson', min_periods=self.min_overlap)
        # cor = (cosine(rp.T))

        cor = cor.multiply(cor > self.min_sim)
        cor = cor.multiply(overlap_matrix > self.min_overlap)

        movies = dict(enumerate(ratings['movie_id'].cat.categories))
        print(f'correlation is finished, done in {datetime.now() - start_time} seconds')
        if save:

            start_time = datetime.now()
            print('save starting')
            if self.db == 'django.db.backends.postgresql':
                self.save_similarities(cor, movies)
            else:
                self.save_with_django(cor, movies)

            print('save finished, done in {} seconds'.format(datetime.now() - start_time))

        return cor, movies


def normalize(x):
    x = x.astype(float)
    x_sum = x.sum()
    x_num = x.astype(bool).sum()
    x_mean = x_sum / x_num

    if x_num == 1 or x.std() == 0:
        return 0.0
    return (x - x_mean) / (x.max() - x.min())


def load_all_ratings(min_ratings=1):
    columns = ['user_id', 'movie_id', 'rating', 'type']

    ratings_data = Rating.objects.all().values(*columns)

    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
    user_count = user_count.reset_index()
    user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']
    ratings = ratings[ratings['user_id'].isin(user_ids)]
    ratings['rating'] = ratings['rating'].astype(float)
    return ratings


if __name__ == '__main__':
    all_ratings = load_all_ratings()
    ItemSimilarityMatrixBuilder(min_overlap=20, min_sim=0.0).build(all_ratings)
