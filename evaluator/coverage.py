import os
import json
import time
import argparse
import logging
from decimal import Decimal
from collections import defaultdict
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

from recs.funksvd_recommender import FunkSVDRecs
from analytics.models import Rating
from recs.bpr_recommender import BPRRecs
from recs.content_based_recommender import ContentBasedRecs
from recs.fwls_recommender import FeatureWeightedLinearStacking
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs


class RecommenderCoverage(object):

    def __init__(self, recommender):
        self.ratings = self.load_all_ratings()
        self.all_users = set(self.ratings['user_id'])
        self.all_movies = set(self.ratings['movie_id'])
        self.recommender = recommender
        self.items_in_rec = defaultdict(int)
        self.user_recs = []
        self.users_with_recs = dict()

    def calculate_coverage(self, K=6, recName=''):

        logger.debug('calculating coverage for all users ({} in total)'.format(len(self.all_users)))

        for user in list(self.all_users):
            user_id = user
            recset = self.recommender.recommend_items(int(user_id), num=K)
            self.users_with_recs[user] = recset
            inx = 1
            if recset:

                for rec in recset:
                    self.items_in_rec[rec[0]] += 1
                    self.add_user_recs(inx, rec, user)
                    inx += 1

        self.save_user_recs(recName)

        no_movies = len(self.all_movies)
        no_movies_in_rec = len(self.items_in_rec)
        no_users = len(self.all_users)
        no_users_in_rec = len(self.users_with_recs)
        user_coverage = float(no_users_in_rec / no_users)
        movie_coverage = float(no_movies_in_rec / no_movies)
        logger.info("{} {} {}".format(no_users, no_users_in_rec, user_coverage))
        logger.info("{} {} {}".format(no_movies, no_movies_in_rec, movie_coverage))
        return user_coverage, movie_coverage

    def save_user_recs(self, recName):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        logger.debug('writing cf coverage to file.')
        json.dump(self.items_in_rec, open('{}-{}_item_coverage.json'.format(timestr, recName), 'w'))
        json.dump(self.user_recs,
                  open('{}-{}_user_coverage.json'.format(timestr, recName), 'w')
                  , cls=DecimalEncoder)

    def add_user_recs(self, inx, rec, user):
        self.user_recs.append({"userid": user,
                               "itemid": rec[0],
                               "prediction": float(rec[1]['prediction']),
                               "inx": inx})

    @staticmethod
    def load_all_ratings(min_ratings=1):
        columns = ['user_id', 'movie_id', 'rating', 'type', 'rating_timestamp']

        ratings_data = Rating.objects.all().values(*columns)

        ratings = pd.DataFrame.from_records(ratings_data, columns=columns)

        user_count = ratings[['user_id', 'movie_id']].groupby('user_id').count()
        user_count = user_count.reset_index()
        user_ids = user_count[user_count['movie_id'] > min_ratings]['user_id']

        ratings = ratings[ratings['user_id'].isin(user_ids)]

        ratings['rating'] = ratings['rating'].astype(float)
        logger.debug("using {} ratings".format(ratings.shape[0]))
        return ratings


class DecimalEncoder(json.JSONEncoder):
    def _iterencode(self, o, markers=None):
        if isinstance(o, Decimal):
            # wanted a simple yield str(o) in the next line,
            # but that would mean a yield on the line with super(...),
            # which wouldn't work (see my comment below), so...
            return (str(o) for o in [o])
        return super(DecimalEncoder, self)._iterencode(o, markers)

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logger = logging.getLogger('Evaluation runner')

    parser = argparse.ArgumentParser(description='Evaluate coverage of the recommender algorithms.')
    parser.add_argument('-fwls', help="run evaluation on fwls rec", action="store_true")
    parser.add_argument('-funk', help="run evaluation on funk rec", action="store_true")
    parser.add_argument('-cf', help="run evaluation on cf rec", action="store_true")
    parser.add_argument('-cb', help="run evaluation on cb rec", action="store_true")
    parser.add_argument('-ltr', help="run evaluation on rank rec", action="store_true")

    args = parser.parse_args()

    print(args.fwls)
    k = 10
    cov = None
    if args.fwls:
        logger.debug("evaluating coverage of fwls")
        cov = RecommenderCoverage(FeatureWeightedLinearStacking)
        cov.calculate_coverage(K=k, recName='fwls{}'.format(k))

    if args.cf:
        logger.debug("evaluating coverage of cf")
        cov = RecommenderCoverage(NeighborhoodBasedRecs())
        cov.calculate_coverage(K=k, recName='cf{}'.format(k))

    if args.cb:
        logger.debug("evaluating coverage of cb")
        cov = RecommenderCoverage(ContentBasedRecs())
        cov.calculate_coverage(K=k, recName='cb{}'.format(k))

    if args.ltr:
        logger.debug("evaluating coverage of ltr")
        cov = RecommenderCoverage(BPRRecs())
        cov.calculate_coverage(K=k, recName='bpr{}'.format(k))

    if args.funk:
        logger.debug("evaluating coverage of funk")
        cov = RecommenderCoverage(FunkSVDRecs())

        cov.calculate_coverage(K=k, recName='funk{}'.format(k))

