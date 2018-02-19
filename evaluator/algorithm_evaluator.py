import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import logging
from decimal import Decimal
from tqdm import tqdm



from analytics.models import Rating


class MeanAverageError(object):
    def __init__(self, recommender):
        self.rec = recommender
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s',
                            level=logging.DEBUG)
        self.l = logging.getLogger('Evaluation runner')

    def calculate(self, train_ratings, test_ratings):

        user_ids = test_ratings['user_id'].unique()
        self.l.info('evaluating based on {} users (MAE)'.format(len(user_ids)))
        error = Decimal(0.0)

        if len(user_ids) == 0:
            return Decimal(0.0)

        for user_id in user_ids:
            user_error = Decimal(0.0)

            ratings_for_rec = train_ratings[train_ratings.user_id == user_id]
            movies = {m['movie_id']: Decimal(m['rating']) for m in
                      ratings_for_rec[['movie_id', 'rating']].to_dict(orient='records')}

            this_test_ratings = test_ratings[test_ratings['user_id'] == user_id]

            num_movies = 0
            if len(this_test_ratings) > 0:

                movie_ids = this_test_ratings['movie_id'].unique()
                for item_id in tqdm(movie_ids):
                    actual_rating = this_test_ratings[this_test_ratings['movie_id'] == item_id].iloc[0]['rating']
                    predicted_rating = self.rec.predict_score_by_ratings(item_id, movies)

                    if actual_rating > 0 and predicted_rating > 0:
                        num_movies += 1
                        item_error = abs(actual_rating - predicted_rating)
                        user_error += item_error

                if num_movies > 0:
                    error += user_error / num_movies

                    print(
                        "AE userid:{}, test_ratings:{} predicted {} error {}".format(user_id,
                                                                                     len(this_test_ratings),
                                                                                     num_movies,
                                                                                     user_error / num_movies))

        return error / len(user_ids)


class PrecisionAtK(object):
    def __init__(self, k, recommender):

        self.all_users = Rating.objects.all().values('user_id').distinct()
        self.K = k
        self.rec = recommender

    def calculate_mean_average_precision(self, train_ratings, test_ratings):

        total_precision_score = Decimal(0.0)
        total_recall_score = Decimal(0.0)

        apks = []
        arks = []
        user_id_count = 0
        no_rec = 0
        for user_id, users_test_data in test_ratings.groupby('user_id'):
            user_id_count += 1
            training_data_for_user = train_ratings[train_ratings['user_id'] == user_id][:20]

            dict_for_rec = training_data_for_user.to_dict(orient='records')

            relevant_ratings = list(users_test_data['movie_id'])

            if len(dict_for_rec) > 0:
                recs = list(self.rec.recommend_items_by_ratings(user_id,
                                                                dict_for_rec,
                                                                num=self.K))
                if len(recs) > 0:
                    AP = self.average_precision_k(recs, relevant_ratings)
                    AR = self.recall_at_k(recs, relevant_ratings)
                    arks.append(AR)
                    apks.append(AP)
                    total_precision_score += AP
                    total_recall_score += AR
                else:
                    no_rec += 1

        average_recall = total_recall_score/len(arks) if len(arks) > 0 else 0
        mean_average_precision = total_precision_score/len(apks) if len(apks) > 0 else 0
        output_str = "#userid {}, MAP {}, average recall {}, len-ap {}, len-ar {}, no_recs {}"
        print(output_str.format(user_id_count,
                                mean_average_precision,
                                average_recall,
                                len(apks),
                                len(arks),
                                no_rec))
        return mean_average_precision, average_recall

    @staticmethod
    def recall_at_k(recs, actual):

        if len(actual) == 0:
            return Decimal(0.0)

        TP = set([r[0] for r in recs if r[0] in actual])

        return Decimal(len(TP) / len(actual))

    @staticmethod
    def average_precision_k(recs, actual):
        score = Decimal(0.0)
        num_hits = 0

        for i, p in enumerate(recs):
            TP = p[0] in actual
            if TP:
                num_hits += 1.0
            score += Decimal(num_hits / (i + 1.0))
        if score > 0:
            score /= min(len(recs), len(actual))
        return score


