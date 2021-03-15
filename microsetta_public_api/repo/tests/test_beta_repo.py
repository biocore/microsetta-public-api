from unittest import TestCase
from microsetta_public_api.exceptions import (
    UnknownID, InvalidParameter, UnknownMetric,
)
import pandas as pd
from microsetta_public_api.repo._beta_repo import NeighborsRepo


class NeighborsRepoTestCase(TestCase):

    def setUp(self) -> None:
        self.neighbors = pd.DataFrame([['s2', 's3', 's4', 's5', 's6'],
                                       ['s1', 's3', 's4', 's5', 's6'],
                                       ['s4', 's5', 's6', 's1', 's2'],
                                       ['s3', 's6', 's5', 's1', 's2'],
                                       ['s3', 's4', 's6', 's1', 's2'],
                                       ['s3', 's4', 's5', 's1', 's2']],
                                      index=['s1', 's2', 's3', 's4', 's5',
                                             's6'])
        self.neighbors.index.name = 'sample_id'
        self.repo = NeighborsRepo({'unifrac': self.neighbors})

    def test_exists(self):
        exp = [True, False, True]
        obs = self.repo.exists(['s1', 'dne', 's3'], 'unifrac')
        self.assertListEqual(exp, obs)

    def test_exists_single(self):
        obs = self.repo.exists('s1', 'unifrac')
        self.assertTrue(obs)
        obs = self.repo.exists('dne', 'unifrac')
        self.assertFalse(obs)

    def test_exists_bad_metric(self):
        with self.assertRaises(UnknownMetric):
            self.repo.exists(['s1'], 'bad-metric')

    def test_k_nearest(self):
        exp = ['s3', 's4', 's6']
        obs = self.repo.k_nearest('s5', 'unifrac', k=3)
        self.assertListEqual(exp, obs)

    def test_k_nearest_k_too_high(self):
        with self.assertRaises(InvalidParameter):
            self.repo.k_nearest('s5', 'unifrac', k=70)

    def test_k_nearest_invalid_id(self):
        with self.assertRaises(UnknownID):
            self.repo.k_nearest('dne', 'unifrac', k=3)

    def test_k_nearest_invalid_metric(self):
        with self.assertRaises(UnknownMetric):
            self.repo.k_nearest('dne', 'dne-metric', k=3)
