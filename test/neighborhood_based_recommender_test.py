import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import unittest

import pandas as pd


from recs.neighborhood_based_recommender import NeighborhoodBasedRecs
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder

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
            [[1, STAR_WARS, 9, '2013-10-12 23:21:27+00:00'],
             [1, WONDER_WOMAN, 10, '2014-10-12 23:22:27+00:00'],
             [1, AVENGERS, 10, '2015-11-12 23:20:27+00:00'],
             [1, WOLVERINE, 8, '2015-08-12 23:20:27+00:00'],
             [1, PIRATES_OF, 10, '2015-10-12 22:20:27+00:00'],
             [1, HARRY, 10, '2015-10-12 23:21:27+00:00'],
             [1, CAPTAIN_AMERICA, 10, '2014-10-12 23:20:27+00:00'],
             [1, ALIEN, 6, '2015-10-12 23:22:27+00:00'],
             [1, JACQUES, 6, '2015-10-12 11:20:27+00:00'],

             [2, STAR_WARS, 10, '2013-10-12 23:20:27+00:00'],
             [2, WONDER_WOMAN, 10, '2014-10-12 23:20:27+00:00'],
             [2, AVENGERS, 9, '2016-10-12 23:20:27+00:00'],
             [2, PIRATES_OF, 6, '2010-10-12 23:20:27+00:00'],
             [2, CAPTAIN_AMERICA, 10, '2005-10-12 23:20:27+00:00'],
             [2, DR_STRANGELOVE, 10, '2015-01-12 23:20:27+00:00'],

             [3, STAR_WARS, 9, '2013-10-12 20:20:27+00:00'],
             [3, AVENGERS, 10, '2015-10-12 10:20:27+00:00'],
             [3, PIRATES_OF, 9, '2013-03-12 23:20:27+00:00'],
             [3, HARRY, 8, '2016-10-13 23:20:27+00:00'],
             [3, DR_STRANGELOVE, 10, '2016-09-12 23:20:27+00:00'],

             [4, STAR_WARS, 8, '2013-10-12 23:20:27+00:00'],
             [4, WONDER_WOMAN, 8, '2014-10-12 23:20:27+00:00'],
             [4, AVENGERS, 9, '2015-10-12 23:20:27+00:00'],
             [4, PIRATES_OF, 5, '2013-10-12 23:20:27+00:00'],
             [4, HARRY, 6, '2014-10-12 23:20:27+00:00'],
             [4, ALIEN, 8, '2015-10-12 23:20:27+00:00'],
             [4, DR_STRANGELOVE, 9, '2015-10-12 23:20:27+00:00'],

             [5, STAR_WARS, 6, '2013-10-12 23:20:27+00:00'],
             [5, AVENGERS, 6, '2014-10-12 23:20:27+00:00'],
             [5, WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             [5, PIRATES_OF, 2, '2016-10-12 23:20:27+00:00'],
             [5, HARRY, 10, '2016-10-12 23:20:27+00:00'],
             [5, CAPTAIN_AMERICA, 6, '2016-10-12 23:20:27+00:00'],
             [5, ALIEN, 4, '2016-10-12 23:20:27+00:00'],
             [5, DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],
             [5, JACQUES, 10, '2016-10-12 23:20:27+00:00'],

             [6, STAR_WARS, 8, '2013-10-12 23:20:27+00:00'],
             [6, WONDER_WOMAN, 8, '2014-10-12 23:20:27+00:00'],
             [6, AVENGERS, 8, '2014-10-12 23:20:27+00:00'],
             [6, WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             [6, PIRATES_OF, 6, '2016-10-12 23:20:27+00:00'],
             [6, HARRY, 10, '2016-10-12 23:20:27+00:00'],
             [6, JACQUES, 8, '2016-10-12 23:20:27+00:00'],

             [7, AVENGERS, 10, '2014-10-12 23:20:27+00:00'],
             [7, PIRATES_OF, 3, '2016-10-12 23:20:27+00:00'],
             [7, HARRY, 1, '2016-10-12 23:20:27+00:00'],
             [7, ALIEN, 8, '2016-10-12 23:20:27+00:00'],
             [7, DR_STRANGELOVE, 10, '2016-10-12 23:20:27+00:00'],

             [8, STAR_WARS, 9, '2013-10-12 23:20:27+00:00'],
             [8, WONDER_WOMAN, 7, '2014-10-12 23:20:27+00:00'],
             [8, AVENGERS, 7, '2014-10-12 23:20:27+00:00'],
             [8, WOLVERINE, 7, '2015-10-12 23:20:27+00:00'],
             [8, PIRATES_OF, 8, '2016-10-12 23:20:27+00:00'],
             [8, HARRY, 8, '2016-10-12 23:20:27+00:00'],
             [8, ALIEN, 8, '2016-10-12 23:20:27+00:00'],
             [8, DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],
             [8, JACQUES, 10, '2016-10-12 23:20:27+00:00'],

             [9, WONDER_WOMAN, 7, '2014-10-12 23:20:27+00:00'],
             [9, AVENGERS, 8, '2014-10-12 23:20:27+00:00'],
             [9, WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             [9, PIRATES_OF, 7, '2016-10-12 23:20:27+00:00'],
             [9, HARRY, 8, '2016-10-12 23:20:27+00:00'],
             [9, CAPTAIN_AMERICA, 10, '2016-10-12 23:20:27+00:00'],
             [9, DR_STRANGELOVE, 10, '2016-10-12 23:20:27+00:00'],
             [9, JACQUES, 7, '2016-10-12 23:20:27+00:00'],

             [10, AVENGERS, 7, '2014-10-12 23:20:27+00:00'],
             [10, ALIEN, 10, '2016-10-12 23:20:27+00:00'],
             [10, CAPTAIN_AMERICA, 6, '2016-10-12 23:20:27+00:00'],
             [10, DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],

             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])

        ItemSimilarityMatrixBuilder(0, min_sim=0).build(self.ratings, save=True)

    def test_predicting_score(self):
        # predict users 10 rating for DR_STRANGELOVE

        rec_sys = NeighborhoodBasedRecs()
        score = rec_sys.predict_score_by_ratings(DR_STRANGELOVE, {AVENGERS: 10, ALIEN: 10, CAPTAIN_AMERICA: 7})
        self.assertTrue(abs(8 - score) < 1)

    def test_top_n(self):
        rec_sys = NeighborhoodBasedRecs()

        recs = rec_sys.recommend_items_by_ratings(10, [{'movie_id': AVENGERS, 'rating': 7},
                                                       {'movie_id': ALIEN, 'rating': 10},
                                                       {'movie_id': CAPTAIN_AMERICA, 'rating': 6}])
        self.assertIsNotNone(recs)


