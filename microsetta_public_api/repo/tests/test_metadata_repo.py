import pandas as pd
import numpy as np
from qiime2 import Metadata
from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import (TempfileTestCase,
                                                 ConfigTestCase)
from microsetta_public_api.repo._metadata_repo import MetadataRepo


class TestMetadataRepo(TempfileTestCase, ConfigTestCase):

    def setUp(self):
        TempfileTestCase.setUp(self)
        ConfigTestCase.setUp(self)

        self.metadata_filename = self.create_tempfile(suffix='.qza').name

        self.test_metadata = pd.DataFrame({
                'age_cat': ['30s', '40s', '50s', '30s', np.nan],
                'num_cat': [7.24, 7.24, 8.25, 7.24, np.nan],
                'other': [1, 2, 3, 4, np.nan],
            }, index=pd.Series(['a', 'b', 'c', 'd', 'e'], name='#SampleID')
        )
        Metadata(self.test_metadata).save(self.metadata_filename)
        config.resources.update({'metadata': self.metadata_filename})
        resources.update(config.resources)
        self.repo = MetadataRepo()

    def tearDown(self):
        TempfileTestCase.tearDown(self)
        ConfigTestCase.tearDown(self)

    def test_categories(self):
        exp = ['age_cat', 'num_cat', 'other']
        obs = self.repo.categories
        self.assertCountEqual(exp, obs)

    def test_category_values_string(self):
        exp = ['30s', '40s', '50s']
        obs = self.repo.category_values('age_cat')
        self.assertCountEqual(exp, obs)

    def test_category_values_with_na(self):
        exp = ['30s', '40s', '50s', np.nan]
        obs = self.repo.category_values('age_cat', exclude_na=False)
        self.assertCountEqual(exp, obs)

    def test_category_values_with_na_np_dropped(self):
        exp = ['30s', '40s', '50s']
        obs = self.repo.category_values('age_cat', exclude_na=True)
        self.assertCountEqual(exp, obs)

    def test_category_values_numeric(self):
        exp = [7.24, 8.25]
        obs = self.repo.category_values('num_cat')
        self.assertCountEqual(exp, obs)

    def test_category_sample_id_matches_query_multiple_category(self):
        exp = ['a', 'd']
        query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "age_cat",
                    "operator": "equal",
                    "value": "30s",
                },
                {
                    "id": "num_cat",
                    "operator": "equal",
                    "value": 7.24,
                }
            ]
        }
        obs = self.repo.sample_id_matches(query)
        self.assertCountEqual(exp, obs)

    def test_category_sample_id_matches_query_nested(self):
        exp = ['a', 'c', 'd']
        query = {
            "condition": "OR",
            "rules": [
                {
                    "condition": "AND",
                    "rules": [
                        {
                            "id": "age_cat",
                            "operator": "equal",
                            "value": "30s",
                        },
                        {
                            "id": "num_cat",
                            "operator": "equal",
                            "value": 7.24,
                        }
                    ]

                },
                {
                    "id": "other",
                    "operator": "greater_or_equal",
                    "value": 3,
                },
            ],
        }
        obs = self.repo.sample_id_matches(query)
        self.assertCountEqual(exp, obs)

    def test_category_sample_id_matches_query_single_category(self):
        exp = ['c']
        query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "age_cat",
                    "operator": "equal",
                    "value": "50s",
                },
            ]
        }
        obs = self.repo.sample_id_matches(query)
        self.assertCountEqual(exp, obs)

    def test_category_sample_id_matches_query_no_category(self):
        exp = ['a', 'b', 'c', 'd', 'e']
        query = {
            "condition": "AND",
            "rules": [
            ]
        }
        obs = self.repo.sample_id_matches(query)
        self.assertCountEqual(exp, obs)

    def test_category_sample_id_ill_formed_query_no_condition(self):
        query = {
            "rules": [
                {
                    "id": "age_cat",
                    "operator": "equal",
                    "value": "50s",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, r'does not appear to be a '
                                                r'rule or a group'):
            self.repo.sample_id_matches(query)

    def test_category_sample_id_ill_formed_query_bad_rule(self):
        query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "age_cat",
                    "value": "50s",
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, r'does not appear to be a '
                                                r'rule or a group'):
            self.repo.sample_id_matches(query)

    def test_category_sample_id_ill_formed_query_unsupported_condition(self):
        query = {
            "condition": "XOR",
            "rules": [
                {
                    "id": "age_cat",
                    "value": "50s",
                    "operator": "equal"
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, r'Only conditions in (.*) '
                                                r'are supported. Got '):
            self.repo.sample_id_matches(query)

    def test_category_sample_id_ill_formed_query_unsupported_operator(self):
        query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "age_cat",
                    "value": "50s",
                    "operator": "something_weird"
                }
            ]
        }
        with self.assertRaisesRegex(ValueError, r'Only operators in (.*) '
                                                r'are supported. Got '):
            self.repo.sample_id_matches(query)
