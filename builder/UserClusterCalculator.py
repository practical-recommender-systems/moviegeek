import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Count

from scipy.sparse import dok_matrix
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import numpy as np

from builder import DataHelper

db = './../db.sqlite3'

django.setup()

from analytics.models import Rating, Cluster


class UserClusterCalculator(object):


    def calculate(self):
        print("training k-means clustering")

        user_ids = list(
            Rating.objects.values('user_id').annotate(movie_count=Count('movie_id')).order_by('-movie_count'))
        content_ids = list(Rating.objects.values('movie_id').distinct())
        content_map = {content_ids[i]['movie_id']: i for i in range(len(content_ids))}
        num_users = len(user_ids)

        user_ratings = dok_matrix((num_users, len(content_ids)), dtype=np.float32)
        for i in range(num_users):  # each user corresponds to a row, in the order of all_user_names
            ratings = Rating.objects.filter(user_id=user_ids[i]['user_id'])
            for user_rating in ratings:
                user_ratings[i, content_map[user_rating.movie_id]] = user_rating.rating

        k = 23
        kmeans = KMeans(n_clusters=k)
        clusters = kmeans.fit(user_ratings.tocsr())

        print("saving clusters")
        Cluster.objects.all().delete()


        for i, cluster_label in enumerate(clusters.labels_):
            Cluster(cluster_id=cluster_label, user_id=user_ids[i]['user_id']).save()
        return clusters


if __name__ == '__main__':
    print("Calculating user clusters...")

    cluster = UserClusterCalculator()
    cluster.calculate()
