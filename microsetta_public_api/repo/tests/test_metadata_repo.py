import pandas as pd
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
                'age_cat': ['30s', '40s', '50s', '30s'],
                'num_cat': [7.24, 7.24, 8.25, 7.24],
            }, index=pd.Series(['a', 'b', 'c', 'd'], name='#SampleID')
        )
        config.resources.update({'metadata': self.test_metadata})
        self.repo = MetadataRepo()

    def tearDown(self):
        TempfileTestCase.tearDown(self)
        ConfigTestCase.tearDown(self)

    def test_categories(self):
        exp = ['age_cat', 'num']
        obs = self.repo.categories
        self.assertCountEqual(exp, obs)

    def test_category_values_string(self):
        exp = ['30s', '40s', '50s']
        obs = self.repo.category_values('age_cat')
        self.assertCountEqual(exp, obs)

    def test_category_values_numeric(self):
        exp = [7.24, 8.25]
        obs = self.repo.category_values('num')
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
        exp = ['a', 'b', 'c', 'd']
        query = {
            "condition": "AND",
            "rules": [
            ]
        }
        obs = self.repo.sample_id_matches(query)
        self.assertCountEqual(exp, obs)