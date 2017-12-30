import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()


from recs.popularity_recommender import PopularityBasedRecs

import unittest


class TestNeighborhoodBasedRecs(unittest.TestCase):

    def test_top_n(self):
        rec_sys = PopularityBasedRecs()

        recs = rec_sys.recommend_items(10)
        self.assertIsNotNone(recs)

    def test_rating_prediction(self):
        rec_sys = PopularityBasedRecs()

        predicted_rating = rec_sys.predict_score(10, '0993846')
        self.assertTrue(predicted_rating > 0)


