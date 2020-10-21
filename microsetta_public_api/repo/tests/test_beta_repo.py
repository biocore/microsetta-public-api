from unittest import TestCase
from skbio import DistanceMatrix
from microsetta_public_api.exceptions import (
    UnknownID, InvalidParameter, UnknownMetric,
)
from microsetta_public_api.repo._beta_repo import BetaRepo


class BetaRepoTestCase(TestCase):

    def setUp(self) -> None:
        self.dm = DistanceMatrix(
            [
                [0, 1, 2, 4, 5, 6],
                [1, 0, 3, 4, 5, 6],
                [2, 3, 0, 1, 1, 1],
                [4, 4, 1, 0, 2, 1],
                [5, 5, 1, 2, 0, 3],
                [6, 6, 1, 1, 3, 0],
            ], ids=['s1', 's2', 's3', 's4', 's5', 's6'],
        )

        self.repo = BetaRepo({'unifrac': self.dm})

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
