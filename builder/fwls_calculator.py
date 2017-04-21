import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "prs_project.settings")

import django
from django.db.models import Count

django.setup()

import pandas as pd
import numpy as np

from recs.contentbasedrecs import ContentBasedRecs
from recs.neighborhoodbasedrecs import NeighborhoodBasedRecs
from analytics.models import Rating

import numpy as np
from sklearn.model_selection import train_test_split

import statsmodels.formula.api as sm


class FWLSCalculator(object):
    def __init__(self):
        self.train = None
        self.test = None
        self.rating_count = None
        self.cb = ContentBasedRecs()
        self.cf = NeighborhoodBasedRecs()

    def get_real_training_data(self):
        columns = ['user_id', 'movie_id', 'rating', 'type']
        ratings_data = Rating.objects.all().values(*columns)
        df = pd.DataFrame.from_records(ratings_data, columns=columns)
        self.train, self.test = train_test_split(df, test_size=0.2)

    def get_training_data(self):
        print('load data')

        data = np.array([['1', '2', 3.6],
                         ['1', '3', 5.0],
                         ['1', '4', 5.0],
                         ['2', '2', 3.0]])
        self.train = pd.DataFrame(data, columns=['user_id', 'movie_id', 'rating'])
        self.rating_count = self.train.groupby('user_id').count().reset_index()
        return self.train

    def calculate_predictions_for_training_data(self):
        self.train['cb'] = self.train.apply(lambda data:
                                            self.cb.predict_score(data['user_id'], data['movie_id']))
        self.train['cf'] = self.train.apply(lambda data:
                                            self.cf.predict_score(data['user_id'], data['movie_id']))
        return None

    def calculate_feature_functions_for_training_data(self):
        self.train['cb1'] = self.train.apply(lambda data:
                                             data.cb * self.func1())
        self.train['cb2'] = self.train.apply(lambda data:
                                             data.cb * self.func2(data['user_id']))

        self.train['cf1'] = self.train.apply(lambda data:
                                             data.cf * self.func1())
        self.train['cf2'] = self.train.apply(lambda data:
                                             data.cf * self.func2(data['user_id']))

        return None

    def train(self):
        result = sm.ols(formula="rating ~ cb1+cb2+cf1+cf2", data=fwls.train).fit()
        print(result)


if __name__ == '__main__':
    print("Calculating Feature Weighted Linear Stacking...")

    fwls = FWLSCalculator()
    fwls.get_training_data()
    print(fwls.train)
    print(fwls.fun2('1'))
    fwls.calculate_predictions_for_training_data()
    fwls.calculate_feature_functions_for_training_data()
    fwls.train()