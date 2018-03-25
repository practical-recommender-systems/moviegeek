import unittest

from evaluator.evaluation_runner import EvaluationRunner
from recs.funksvd_recommender import FunkSVDRecs


class FunkSvdTest(unittest.TestCase):
    def test_funksvd_ev_build(self):
        k = 5
        save_path = 'evaluation/precision/'
        recommender = FunkSVDRecs()

        er = EvaluationRunner(0,
                              None,  # builder
                              recommender,
                              k,
                              params={'k': 20,
                                      'save_path': save_path + 'model/'})

        result = er.calculate(1, 5)
        print(result)

        recs1 = recommender.recommend_items('14620', num=5)

        k2 = 7

        recommender2 = FunkSVDRecs()

        er = EvaluationRunner(0,
                              None,  # builder,
                              recommender2,
                              k2,
                              params={'k': 20,
                                      'save_path': save_path + 'model/'})

        result = er.calculate(1, 5)
        print(result)

        recs2 = recommender2.recommend_items('14620', num=7)
        self.compare_recs(recs1, recs2)

    def compare_recs(self, recs1, recs2):
        for i, rec in enumerate(recs1):
            self.assertEqual(rec[0], recs2[i][0])
