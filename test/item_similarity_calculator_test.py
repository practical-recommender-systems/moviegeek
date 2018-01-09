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
        self.ratings = pd.DataFrame([[1, STAR_WARS, 3, '2013-10-12 23:21:27+00:00'],
                        [1, WONDER_WOMAN, 6, '2013-10-12 23:21:27+00:00'],
                        [1, AVENGERS, 7, '2013-10-12 23:21:27+00:00'],
                        [2, WONDER_WOMAN, 6, '2013-10-12 23:21:27+00:00'],
                        [2, AVENGERS, 7, '2013-10-12 23:21:27+00:00'],
                        [2, WOLVERINE, 3, '2013-10-12 23:21:27+00:00'],
                        [3, WONDER_WOMAN, 7, '2013-10-12 23:21:27+00:00'],
                        [3, AVENGERS, 6, '2013-10-12 23:21:27+00:00'],
                        [3, WOLVERINE, 3, '2013-10-12 23:21:27+00:00'],]
                       , columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

    def test_simple_similarity(self):
        builder = ItemSimilarityMatrixBuilder(0)

        no_items = len(set(self.ratings['movie_id']))
        cor, movies = builder.build(ratings=self.ratings, save=False)
        df = pd.DataFrame(cor.toarray(), columns=movies.values(), index=movies.values())
        self.assertIsNotNone(df)
        self.assertEqual(df.shape[0], no_items, "Expected correlations matrix to have a row for each item")
        self.assertEqual(df.shape[1], no_items, "Expected correlations matrix to have a column for each item")

        self.assertAlmostEqual(df[WONDER_WOMAN][AVENGERS], 0.71066905451870177)
        self.assertAlmostEqual(df[AVENGERS][AVENGERS], 1)
        self.assertAlmostEqual(df[STAR_WARS][STAR_WARS], 1)
        self.assertAlmostEqual(df[WONDER_WOMAN][WONDER_WOMAN], 1.0)
        self.assertAlmostEqual(df[WOLVERINE][WOLVERINE], 1)

    def test_min_ratings(self):
        builder = ItemSimilarityMatrixBuilder(2)

        cor, movies = builder.build(ratings=self.ratings, save=False)
        df = pd.DataFrame(cor.toarray(), columns=movies.values(), index=movies.values())
        self.assertEqual(cor.shape[0], 4, "Expected correlations matrix to have a row for each item")
        self.assertEqual(cor.shape[1], 4, "Expected correlations matrix to have a column for each item")

        self.assertAlmostEqual(df[WONDER_WOMAN][AVENGERS], 0.71066905451870177)
        self.assertAlmostEqual(df[AVENGERS][AVENGERS], 1)

    def test_save_similarities(self):
        builder = ItemSimilarityMatrixBuilder(0, 0.1)

        cor = builder.build(ratings=self.ratings)

        self.assertIsNotNone(cor)

        similarities = Similarity.objects.all()
        av_log = similarities[0]

        self.assertEqual(Similarity.objects.count(), 2)
        self.assertEqual(av_log.source, WONDER_WOMAN)
        self.assertEqual(av_log.target, AVENGERS)
        self.assertAlmostEqual(float(av_log.similarity), 0.71066905451870177)

    def test_overlap(self):
        builder = ItemSimilarityMatrixBuilder(1, -1)

        cor, movies = builder.build(ratings=self.ratings, save=False)

        self.assertIsNotNone(cor)

        self.assertEqual(cor.count_nonzero(), 9)

if __name__ == '__main__':
    unittest.main()
