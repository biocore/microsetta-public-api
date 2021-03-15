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
import pandas as pd
from unittest.mock import patch


class BetaTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.diversity.beta.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()
        neighbors = pd.DataFrame([['s2', 's3', 's4'],
                                  ['s1', 's3', 's4'],
                                  ['s1', 's2', 's4'],
                                  ['s1', 's2', 's3']],
                                 columns=['k0', 'k1', 'k2'],
                                 index=['s1', 's2', 's3', 's4'])
        neighbors.index.name = 'sample_id'

        self.resources = DictElement({
            'datasets': DictElement({
                'dataset1': DictElement({
                    '__neighbors__': BetaElement({
                        'unifrac': neighbors
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
