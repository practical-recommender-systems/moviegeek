import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import pandas as pd

from builder.bpr_calculator import BayesianPersonalizationRanking
import unittest

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

        bpr = BayesianPersonalizationRanking('')
        bpr.initialize_factors(ratings)
        for d in bpr.draw(2):
            print(d)
