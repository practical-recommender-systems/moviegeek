import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import unittest

import pandas as pd

from recommender.models import Similarity
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder

STAR_WARS = 'star wars'
WONDER_WOMAN = 'wonder woman'
AVENGERS = 'avengers'
WOLVERINE = 'logan'


class TestItemSimilarityMatrixBuilder(unittest.TestCase):

    def setUp(self):
        self.ratings = pd.DataFrame([[1, STAR_WARS, 7, '2013-10-12 23:21:27+00:00'],
                                [1, WONDER_WOMAN, 5, '2013-10-12 23:21:27+00:00'],
                                [1, AVENGERS, 4, '2013-10-12 23:21:27+00:00'],
                                [2, WONDER_WOMAN, 5, '2013-10-12 23:21:27+00:00'],
                                [2, AVENGERS, 4, '2013-10-12 23:21:27+00:00'],
                                [2, WOLVERINE, 7, '2013-10-12 23:21:27+00:00'],
                                [3, WONDER_WOMAN, 5, '2013-10-12 23:21:27+00:00'],
                                [3, AVENGERS, 4, '2013-10-12 23:21:27+00:00'], ]
                               , columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

    def test_simple_similarity(self):
        builder = ItemSimilarityMatrixBuilder(0)

        no_items = len(set(self.ratings['movie_id']))
        cor = builder.build(ratings=self.ratings, save=False)
        self.assertIsNotNone(cor)
        self.assertEqual(cor.shape[0], no_items, "Expected correlations matrix to have a row for each item")
        self.assertEqual(cor.shape[1], no_items, "Expected correlations matrix to have a column for each item")

        self.assertEqual(cor[WONDER_WOMAN][AVENGERS], - 1, "Expected Wolverine and Star Wars to have similarity 0.5")
        self.assertEqual(cor[AVENGERS][AVENGERS], 1, "Expected items to be similar to themselves similarity 1")
        self.assertEqual(cor[STAR_WARS][STAR_WARS], 1, "Expected items to be similar to themselves similarity 1")
        self.assertEqual(cor[WONDER_WOMAN][WONDER_WOMAN], 1, "Expected items to be similar to themselves similarity 1")
        self.assertEqual(cor[WOLVERINE][WOLVERINE], 1, "Expected items to be similar to themselves similarity 1")

    def test_min_ratings(self):
        builder = ItemSimilarityMatrixBuilder(2)

        cor = builder.build(ratings=self.ratings, save=False)
        self.assertIsNotNone(cor)
        self.assertEqual(cor.shape[0], 2, "Expected correlations matrix to have a row for each item")
        self.assertEqual(cor.shape[1], 2, "Expected correlations matrix to have a column for each item")

        self.assertEqual(cor[WONDER_WOMAN][AVENGERS], -1, "Expected Wolverine and Star Wars to have similarity 0.5")
        self.assertEqual(cor[AVENGERS][AVENGERS], 1, "Expected items to be similar to themselves similarity 1")

    def test_save_similarities(self):
        builder = ItemSimilarityMatrixBuilder(0)

        cor = builder.build(ratings=self.ratings)

        self.assertIsNotNone(cor)

        similarities = Similarity.objects.all()
        av_log = similarities[0]

        self.assertEqual(Similarity.objects.count(), 4)
        self.assertEqual(av_log.source, AVENGERS)
        self.assertEqual(av_log.target, WOLVERINE)
        self.assertEqual(av_log.similarity, 0.5)

if __name__ == '__main__':
    unittest.main()
