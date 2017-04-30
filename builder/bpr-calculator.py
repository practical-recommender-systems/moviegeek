import numpy as np
from math import exp
import random
import pandas as pd

class BayesianPersonalizationRanking(object):

    def build(self, data, num_iterations):

        for iteration in range(num_iterations):
            for u, i, j in self.generate_samples():
                self.step(u,i,j)

    def step(self, u, i, j):
        pass

    def generate_samples(self):
        return 1,1,1

def get_data():
    return pd.DataFrame([[0,1], [1,0]])

if __name__  == '__main__':
    data = get_data()
    model = BayesianPersonalizationRanking(data)



