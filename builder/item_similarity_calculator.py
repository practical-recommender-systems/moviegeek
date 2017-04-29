import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import datetime
import decimal
import pandas as pd
import numpy as np
import time

from recommender.models import Similarity
from analytics.models import Rating


class ItemSimilarityMatrixBuilder(object):
    def save_cf(self, df, created=datetime.datetime.now()):
        print("Save item-item model")

        Similarity.objects.all().delete()
        sims = []
        inx = 0
        for row in df.iterrows():
            if inx == 100:
                Similarity.objects.bulk_create(sims)
                sims = []

            else:
                inx += 1

            new_similarity = Similarity(
                created=created,
                source=int(row[0]),
                target=int(row[1].values[0]),
                similarity=decimal.Decimal(str(row[1].values[1]))
            )
            if not new_similarity.target == new_similarity.source and new_similarity.similarity > 0:
                sims.append(new_similarity)
        Similarity.objects.bulk_create(sims)
        print('Similarity items saved')

    def build(self, ratings):
        print("calculating the similarities.")
        print("Calculating similarites ... using {} ratings".format(len(ratings)))

        ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))
        ratings['avg'] = ratings['avg'].astype(float)
        print("normalized ratings.")
        print(ratings.head())

        rp = ratings.pivot_table(index=['movie_id'], columns=['user_id'], values='avg')
        print("rating matrix finished")

        cor = rp.transpose().corr(method='pearson', min_periods=10)

        # todo: implement cosine_similarity
        # cor = cosine_similarity(rp.trainspose())
        print('correlation is finished')

        long_format_cor = cor.stack().reset_index(level=0)

        self.save_cf(long_format_cor)

        return cor


def normalize(x):
    x = x.astype(float)
    if x.std() == 0:
        return 0.0
    return (x - x.mean()) / x.std()


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
    print("Load ratings...")

    ItemSimilarityMatrixBuilder().build(load_all_ratings())
