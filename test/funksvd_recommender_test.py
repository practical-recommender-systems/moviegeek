import os

from builder.matrix_factorization_calculator import MatrixFactorization
from recs.funksvd_recommender import FunkSVDRecs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import unittest

import pandas as pd

STAR_WARS = 'star wars'
WONDER_WOMAN = 'wonder woman'
AVENGERS = 'avengers'
WOLVERINE = 'logan'
PIRATES_OF = 'pirates of the caribbien'
HARRY = 'harry potter I'
CAPTAIN_AMERICA = 'captain america'
ALIEN = 'alien'
DR_STRANGELOVE = 'doctor strangelove'
JACQUES = 'jacques'


class TestNeighborhoodBasedRecs(unittest.TestCase):
    def setUp(self):
        self.ratings = pd.DataFrame(
            [['1', STAR_WARS, 9, '2013-10-12 23:21:27+00:00'],
             ['1', WONDER_WOMAN, 10, '2014-10-12 23:22:27+00:00'],
             ['1', AVENGERS, 10, '2015-11-12 23:20:27+00:00'],
             ['1', WOLVERINE, 8, '2015-08-12 23:20:27+00:00'],
             ['1', PIRATES_OF, 10, '2015-10-12 22:20:27+00:00'],
             ['1', HARRY, 10, '2015-10-12 23:21:27+00:00'],
             ['1', CAPTAIN_AMERICA, 10, '2014-10-12 23:20:27+00:00'],
             ['1', ALIEN, 6, '2015-10-12 23:22:27+00:00'],
             ['1', JACQUES, 6, '2015-10-12 11:20:27+00:00'],

             ['2', STAR_WARS, 10, '2013-10-12 23:20:27+00:00'],
             ['2', WONDER_WOMAN, 10, '2014-10-12 23:20:27+00:00'],
             ['2', AVENGERS, 9, '2016-10-12 23:20:27+00:00'],
             ['2', PIRATES_OF, 6, '2010-10-12 23:20:27+00:00'],
             ['2', CAPTAIN_AMERICA, 10, '2005-10-12 23:20:27+00:00'],
             ['2', DR_STRANGELOVE, 10, '2015-01-12 23:20:27+00:00'],

             ['3', STAR_WARS, 9, '2013-10-12 20:20:27+00:00'],
             ['3', AVENGERS, 10, '2015-10-12 10:20:27+00:00'],
             ['3', PIRATES_OF, 9, '2013-03-12 23:20:27+00:00'],
             ['3', HARRY, 8, '2016-10-13 23:20:27+00:00'],
             ['3', DR_STRANGELOVE, 10, '2016-09-12 23:20:27+00:00'],

             ['4', STAR_WARS, 8, '2013-10-12 23:20:27+00:00'],
             ['4', WONDER_WOMAN, 8, '2014-10-12 23:20:27+00:00'],
             ['4', AVENGERS, 9, '2015-10-12 23:20:27+00:00'],
             ['4', PIRATES_OF, 5, '2013-10-12 23:20:27+00:00'],
             ['4', HARRY, 6, '2014-10-12 23:20:27+00:00'],
             ['4', ALIEN, 8, '2015-10-12 23:20:27+00:00'],
             ['4', DR_STRANGELOVE, 9, '2015-10-12 23:20:27+00:00'],

             ['5', STAR_WARS, 6, '2013-10-12 23:20:27+00:00'],
             ['5', AVENGERS, 1, '2014-10-12 23:20:27+00:00'],
             ['5', WOLVERINE, 2, '2015-10-12 23:20:27+00:00'],
             ['5', PIRATES_OF, 2, '2016-10-12 23:20:27+00:00'],
             ['5', HARRY, 10, '2016-10-12 23:20:27+00:00'],
             ['5', CAPTAIN_AMERICA, 1, '2016-10-12 23:20:27+00:00'],
             ['5', ALIEN, 4, '2016-10-12 23:20:27+00:00'],
             ['5', DR_STRANGELOVE, 3, '2016-10-12 23:20:27+00:00'],
             ['5', JACQUES, 10, '2016-10-12 23:20:27+00:00'],

             ['6', STAR_WARS, 8, '2013-10-12 23:20:27+00:00'],
             ['6', WONDER_WOMAN, 8, '2014-10-12 23:20:27+00:00'],
             ['6', AVENGERS, 8, '2014-10-12 23:20:27+00:00'],
             ['6', WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             ['6', PIRATES_OF, 6, '2016-10-12 23:20:27+00:00'],
             ['6', HARRY, 10, '2016-10-12 23:20:27+00:00'],
             ['6', JACQUES, 8, '2016-10-12 23:20:27+00:00'],

             ['7', AVENGERS, 10, '2014-10-12 23:20:27+00:00'],
             ['7', PIRATES_OF, 3, '2016-10-12 23:20:27+00:00'],
             ['7', HARRY, 1, '2016-10-12 23:20:27+00:00'],
             ['7', ALIEN, 8, '2016-10-12 23:20:27+00:00'],
             ['7', DR_STRANGELOVE, 10, '2016-10-12 23:20:27+00:00'],

             ['8', STAR_WARS, 9, '2013-10-12 23:20:27+00:00'],
             ['8', WONDER_WOMAN, 7, '2014-10-12 23:20:27+00:00'],
             ['8', AVENGERS, 7, '2014-10-12 23:20:27+00:00'],
             ['8', WOLVERINE, 7, '2015-10-12 23:20:27+00:00'],
             ['8', PIRATES_OF, 8, '2016-10-12 23:20:27+00:00'],
             ['8', HARRY, 8, '2016-10-12 23:20:27+00:00'],
             ['8', ALIEN, 8, '2016-10-12 23:20:27+00:00'],
             ['8', DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],
             ['8', JACQUES, 10, '2016-10-12 23:20:27+00:00'],

             ['9', WONDER_WOMAN, 7, '2014-10-12 23:20:27+00:00'],
             ['9', AVENGERS, 8, '2014-10-12 23:20:27+00:00'],
             ['9', WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             ['9', PIRATES_OF, 7, '2016-10-12 23:20:27+00:00'],
             ['9', HARRY, 8, '2016-10-12 23:20:27+00:00'],
             ['9', CAPTAIN_AMERICA, 10, '2016-10-12 23:20:27+00:00'],
             ['9', DR_STRANGELOVE, 10, '2016-10-12 23:20:27+00:00'],
             ['9', JACQUES, 7, '2016-10-12 23:20:27+00:00'],

             ['10', AVENGERS, 7, '2014-10-12 23:20:27+00:00'],
             ['10', ALIEN, 10, '2016-10-12 23:20:27+00:00'],
             ['10', CAPTAIN_AMERICA, 6, '2016-10-12 23:20:27+00:00'],
             ['10', DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],

             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

        self.save_path = './test/'
        self.k=3
        MF = MatrixFactorization(save_path=self.save_path)
        MF.train(self.ratings, k=self.k)

    def test_rec(self):

        recommender = FunkSVDRecs(self.save_path)
        recs = recommender.recommend_items_by_ratings('1',
                                                      [{'movie_id': AVENGERS, 'rating': 7},
                                                       {'movie_id': ALIEN, 'rating': 10},
                                                       {'movie_id': CAPTAIN_AMERICA, 'rating': 6}], num=2)
        self.assertIsNotNone(recs)
        self.assertEqual(len(recs), 2)


    def test_rec2(self):
        recommender = FunkSVDRecs(self.save_path)
        recs = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=5)
        self.assertIsNotNone(recs)
        self.assertEqual(len(recs), 5)
        top = [r[0] for r in recs][:2]
        self.assertIn(HARRY, top, '{} was missing from {}'.format(HARRY, top))
        self.assertIn(JACQUES, top, '{} was missing from {}'.format(JACQUES, top))


    def test_rec_increasing(self):
        recommender = FunkSVDRecs(self.save_path)
        recs1 = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=2)
        self.assertIsNotNone(recs1)
        self.assertEqual(len(recs1), 2)

        recs2 = recommender.recommend_items_by_ratings('5',
                                                       [{'movie_id': AVENGERS, 'rating': 1}], num=3)
        self.assertIsNotNone(recs2)
        self.assertEqual(len(recs2), 3)

        self.assertEqual(recs1[0],recs2[0] )
        self.assertEqual(recs1[1],recs2[1] )

    def test_rec_increasing2(self):

        recommender = FunkSVDRecs(self.save_path)
        recs4 = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=4)
        self.assertIsNotNone(recs4)
        self.assertEqual(len(recs4), 4)
        self.assertAlmostEqual(recs4[1][1]['prediction'], 7.812836963)
        recs6 = recommender.recommend_items_by_ratings('5',
                                                       [{'movie_id': AVENGERS, 'rating': 1}], num=6)
        self.assertIsNotNone(recs6)
        self.assertEqual(len(recs6), 6)
        self.compare_recs(recs4, recs6)

        recommender = FunkSVDRecs(self.save_path)
        recs42 = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=4)
        self.compare_recs(recs4, recs42)

        recs1 = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=7)
        recs2 = recommender.recommend_items_by_ratings('5',
                                                      [{'movie_id': AVENGERS, 'rating': 1}], num=9)

        self.compare_recs(recs1, recs2)


    def compare_recs(self, recs1, recs2):
        for i in range(len(recs1)):
            self.assertEqual(recs1[i][0], recs2[i][0])


if __name__ == '__main__':
    unittest.main()