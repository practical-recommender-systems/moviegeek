import decimal
import pandas as pd
import unittest

from evaluator.evaluation_runner import EvaluationRunner
from builder.item_similarity_calculator import ItemSimilarityMatrixBuilder
from recs.neighborhood_based_recommender import NeighborhoodBasedRecs

STAR_WARS = 'sw'
WONDER_WOMAN = 'wwoman'
AVENGERS = 'avengers'
WOLVERINE = 'logan'
PIRATES_OF = 'potc'
HARRY = 'hpI'
CAPTAIN_AMERICA = 'cap.amer'
ALIEN = 'alien'
DR_STRANGELOVE = 'doc.stra'
JACQUES = 'jacques'


class TestEvaluationRunner(unittest.TestCase):
    def test(self):
        er = EvaluationRunner(5, ItemSimilarityMatrixBuilder(1, min_sim=0.0), NeighborhoodBasedRecs())

        ratings = pd.DataFrame(
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
             [10, HARRY, 10, '2016-10-12 23:20:27+00:00'],
             [10, CAPTAIN_AMERICA, 6, '2016-10-12 23:20:27+00:00'],
             [10, DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],

             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])
        ratings['rating'] = ratings['rating'].astype(decimal.Decimal)
        result = er.calculate_using_ratings(ratings, min_number_of_ratings=4, min_rank=5)

        # figure out what to do with result ;)
        self.assertLess(result['mae'], decimal.Decimal(1.7))
        self.assertLess(result['pak'], decimal.Decimal(0.7))
        self.assertLess(result['rak'], decimal.Decimal(0.7))
        print(result)

    def test_split_data(self):
        ratings = pd.DataFrame(
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
             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])
        er = EvaluationRunner(5, ItemSimilarityMatrixBuilder(1, min_sim=0.0), NeighborhoodBasedRecs())

        test, train = er.split_data(2, ratings, [1, 2], [3])
        self.assertTrue(test is not None)
        self.assertTrue(test.shape[0], 4)
        self.assertEqual(train.shape[0], 16)
