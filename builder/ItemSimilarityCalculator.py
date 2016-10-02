import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Count
django.setup()

import datetime
import decimal
import pandas as pd
from recommender.models import Similarity
from analytics.models import Rating

def save_similarity_from_df(df, created=datetime.datetime.now(), version=1):
    print("Save item-item model")

    similarities = list()
    for row in df.iterrows():
        source = int(row[0])
        target = int(row[1].values[0])
        sim = float(row[1].values[1])

        if not target == source and sim > 0:
            similarities.append((created, source, target, sim, version))
    #todo: use django ORM.

    save_cf(similarities)

def save_cf(similarites):

    for sim in similarites:
        print(sim)
        print(sim[3])

        Similarity(
            created=sim[0],
            source=sim[1],
            target=sim[2],
            similarity=decimal.Decimal(str(sim[3]))
        ).save()


def build(ratings):
    print("calculating the similarities.")

    ratings['avg'] = ratings.groupby('user_id')['rating'].transform(lambda x: normalize(x))
    print("normalized ratings.")

    rp = ratings.pivot_table(index=['movie_id'], columns=['user_id'], values='avg')
    print("rating matrix finished")

    cor = rp.transpose().corr(method='pearson', min_periods=5)
    #cor = cosine_similarity(rp.trainspose())
    print('correlation is finished')
    print(cor)
    long_format_cor = cor.stack().reset_index(level=0)

    save_similarity_from_df(long_format_cor)

    print(long_format_cor.head())

    return cor


def normalize(x):
    x = x.astype(float)
    if x.std() == 0:
        return 0
    return (x - x.mean()) / x.std()

if __name__ == '__main__':
    print("Load ratings...")

    columns = ['user_id', 'movie_id', 'rating', 'type']

    ratings_data = Rating.objects.all().values(*columns)[:10000]
    ratings = pd.DataFrame.from_records(ratings_data, columns=columns)
    ratings['rating'] = ratings['rating'].astype(float)

    print("Calculating similarites ... using {} ratings".format(len(ratings)))

    build(ratings)
