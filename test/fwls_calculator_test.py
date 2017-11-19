import unittest

import numpy as np
import pandas as pd


class TestNeighborhoodBasedRecs(unittest.TestCase):
    def get_training_data(self):

        data = np.array([['1', '2', 3.6],
                         ['1', '3', 5.0],
                         ['1', '4', 5.0],
                         ['2', '2', 3.0]])
        self.train_data = pd.DataFrame(data, columns=['user_id', 'movie_id', 'rating'])
        self.rating_count = self.train_data.groupby('user_id').count().reset_index()
        return self.train_data