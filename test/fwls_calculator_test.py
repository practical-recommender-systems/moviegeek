import unittest

import numpy as np
import pandas as pd

from builder.fwls_calculator import FWLSCalculator
import pickle

from recs.fwls_recommender import FeatureWeightedLinearStacking


class TestFWLS(unittest.TestCase):

    def get_training_data(self):

        data = np.array([['1', '2', 3.6, 1, 1, 1, 1],
                         ['1', '3', 5.0, 1, 1, 1, 1],
                         ['1', '4', 5.0, 1, 1, 1, 1],
                         ['2', '2', 3.0, 1, 0, 1, 0]])
        self.train_data = pd.DataFrame(data, columns=['user_id', 'movie_id', 'rating', 'cb1','cb2','cf1','cf2' ])
        self.rating_count = self.train_data.groupby('user_id').count().reset_index()
        return self.train_data

    def test_train_FWLSCalculator(self):
        save_path = './models/fwls/'
        builder = FWLSCalculator(save_path)
        train_data = self.get_training_data()
        builder.train_data = train_data
        parameters = builder.train()
        assert(parameters is not None)

        with open(save_path + 'fwls_parameters.data', 'rb') as ub_file:
            loaded = pickle.load(ub_file)
            assert(loaded is not None)
            assert(loaded['cb1'] == parameters['cb1'])
            assert(loaded['cb2'] == parameters['cb2'])
            assert(loaded['cf1'] == parameters['cf1'])
            assert(loaded['cf2'] == parameters['cf2'])

    def test_recFWLS(self):
        save_path = './models/fwls/'
        builder = FWLSCalculator(save_path)
        train_data = self.get_training_data()
        builder.train_data = train_data
        parameters = builder.train()
        assert(parameters is not None)

        rec = FeatureWeightedLinearStacking()
        rec.set_save_path(save_path)
        assert(rec.wcb1 == parameters['cb1'])
        assert(rec.wcb2 == parameters['cb2'])
        assert(rec.wcf1 == parameters['cf1'])
        assert(rec.wcf2 == parameters['cf2'])