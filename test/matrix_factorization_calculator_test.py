import os

from builder.matrix_factorization_calculator import MatrixFactorization

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django

django.setup()

import unittest
from decimal import Decimal
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

class TestMatrixFactorizationCalculator(unittest.TestCase):
    def setUp(self):
        self.ratings = pd.DataFrame(
            [['1' , STAR_WARS, 9, '2013-10-12 23:21:27+00:00'],
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
             ['5', AVENGERS, 6, '2014-10-12 23:20:27+00:00'],
             ['5', WOLVERINE, 8, '2015-10-12 23:20:27+00:00'],
             ['5', PIRATES_OF, 2, '2016-10-12 23:20:27+00:00'],
             ['5', HARRY, 10, '2016-10-12 23:20:27+00:00'],
             ['5', CAPTAIN_AMERICA, 6, '2016-10-12 23:20:27+00:00'],
             ['5', ALIEN, 4, '2016-10-12 23:20:27+00:00'],
             ['5', DR_STRANGELOVE, 8, '2016-10-12 23:20:27+00:00'],
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
        self.ratings['rating'] = self.ratings['rating'].astype(Decimal)
        print(self.ratings)

    def test_simple_factorization(self):
        save_path = './test/'
        k=3

        MF = MatrixFactorization(save_path=save_path)
        MF.train(self.ratings, k=k)

        self.assertEqual(MF.user_factors.shape[0], len(set(self.ratings['user_id'])))
        self.assertEqual(MF.user_factors.shape[1], k)

    def test_factorization(self):
        ratings = pd.DataFrame(
            [['1', "SW", Decimal(5), '2013-10-12 23:21:27+00:00'],
             ['1', "SW2", Decimal(5), '2014-10-12 23:22:27+00:00'],
             ['1', "SW3", Decimal(5), '2015-11-12 23:20:27+00:00'],
             ['1', "MM", Decimal(2), '2015-08-12 23:20:27+00:00'],
             ['1', "MM2", Decimal(1), '2015-10-12 22:20:27+00:00'],

             ['2', "SW", Decimal(4), '2013-10-12 23:21:27+00:00'],
             ['2', "SW2", Decimal(5), '2014-10-12 23:22:27+00:00'],
             ['2', "SW3", Decimal(5), '2015-11-12 23:20:27+00:00'],
             ['2', "MM", Decimal(1), '2015-08-12 23:20:27+00:00'],
             ['2', "MM2", Decimal(2), '2015-10-12 22:20:27+00:00'],

             ['3', "SW", Decimal(5), '2013-10-12 23:21:27+00:00'],
             ['3', "SW2", Decimal(5), '2014-10-12 23:22:27+00:00'],

             ['4', "SW", Decimal(1), '2013-10-12 23:21:27+00:00'],
             ['4', "SW2", Decimal(2), '2014-10-12 23:22:27+00:00'],
             ['4', "SW3", Decimal(1), '2015-11-12 23:20:27+00:00'],
             ['4', "MM", Decimal(5), '2015-08-12 23:20:27+00:00'],
             ['4', "MM2", Decimal(5), '2015-10-12 22:20:27+00:00'],

             ['5', "SW", Decimal(2), '2013-10-12 23:21:27+00:00'],
             ['5', "SW2", Decimal(1), '2014-10-12 23:22:27+00:00'],
             ['5', "SW3", Decimal(2), '2015-11-12 23:20:27+00:00'],
             ['5', "MM", Decimal(4), '2015-08-12 23:20:27+00:00'],
             ['5', "MM2", Decimal(5), '2015-10-12 22:20:27+00:00'],
             ], columns=['user_id', 'movie_id', 'rating', 'rating_timestamp'])
        ratings['rating'] = ratings['rating'].astype(Decimal)

        save_path = './test/small_model/'
        k = 2

        MF = MatrixFactorization(save_path=save_path)
        MF.train(ratings, k=k)

        self.assertEqual(MF.user_factors.shape[0], len(set(ratings['user_id'])))
        self.assertEqual(MF.user_factors.shape[1], k)
        u_inx = MF.u_inx['3']
        i_inx = MF.i_inx['SW3']

        r_sw3 = MF.predict(u_inx, i_inx)

        print(MF.item_factors)
        print("user factors {}".format(MF.user_factors))
        print("u_inx {}".format(MF.u_inx))
        print("i_inx {}".format(MF.i_inx))
        print("user bias {}".format(dict(MF.user_bias)))
        print("item bias {}".format(dict(MF.item_bias)))

        i_inx = MF.i_inx['MM']
        recommendation = {i: MF.predict(u_inx, MF.i_inx[i]) for i in set(ratings['movie_id'])}
        print(recommendation)
        print(sorted(recommendation, key=recommendation.__getitem__))
        r_mm2 = MF.predict(u_inx, i_inx)

        print("SW3 {} vs. MM2 {}".format(r_sw3, r_mm2))
        self.assertGreater(r_sw3, r_mm2)



