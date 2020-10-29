import json
from microsetta_public_api.api.diversity.beta import (
    k_nearest,
)

from microsetta_public_api.config import DictElement, BetaElement

from microsetta_public_api.exceptions import (
    UnknownResource, UnknownID, UnknownMetric, InvalidParameter
)
from microsetta_public_api.utils.testing import (
    MockedJsonifyTestCase,
    TrivialVisitor,
)
from skbio import DistanceMatrix
from unittest.mock import patch


class BetaTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.diversity.beta.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()
        dm_values = [
            [0, 1, 2, 3],
            [1, 0, 3, 4],
            [2, 3, 0, 5],
            [3, 4, 5, 0]
        ]
        ids = ['s1', 's2', 's3', 's4']
        dm = DistanceMatrix(
            dm_values,
            ids=ids,
        )
        self.resources = DictElement({
            'datasets': DictElement({
                'dataset1': DictElement({
                    '__beta__': BetaElement({
                        'unifrac': dm
                    })
                }),
            }),
        })
        self.resources.accept(TrivialVisitor())
        self.res_patcher = patch(
            'microsetta_public_api.api.diversity.beta.get_resources')
        self.mock_resources = self.res_patcher.start()
        self.mock_resources.return_value = self.resources

    def tearDown(self):
        self.res_patcher.stop()
        super().tearDown()

    def test_k_nearest(self):
        results, code = k_nearest(
            dataset='dataset1',
            beta_metric='unifrac',
            k=1,
            sample_id='s1'
        )
        self.assertCountEqual(json.loads(results), ['s2'])

        results, code = k_nearest(
            dataset='dataset1',
            beta_metric='unifrac',
            k=2,
            sample_id='s2'
        )
        self.assertCountEqual(json.loads(results), ['s1', 's3'])

    def test_k_nearest_unknown_dataset(self):
        with self.assertRaises(UnknownResource):
            k_nearest(
                dataset='dne',
                beta_metric='unifrac',
                k=2,
                sample_id='s2'
            )

    def test_k_nearest_unknown_metric(self):
        with self.assertRaises(UnknownMetric):
            k_nearest(
                dataset='dataset1',
                beta_metric='unifork',
                k=2,
                sample_id='s2'
            )

    def test_k_nearest_unknown_id(self):
        with self.assertRaises(UnknownID):
            k_nearest(
                dataset='dataset1',
                beta_metric='unifrac',
                k=2,
                sample_id='s2-dne'
            )

    def test_k_nearest_invalid_k(self):
        with self.assertRaises(InvalidParameter):
            k_nearest(
                dataset='dataset1',
                beta_metric='unifrac',
                k=724,
                sample_id='s2'
            )
