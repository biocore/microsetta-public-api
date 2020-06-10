import json
from unittest.mock import patch, PropertyMock
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.api.metadata import (category_values,
                                                filter_sample_ids,
                                                )


class MetadataImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = 'microsetta_public_api.api.metadata.jsonify'

    def test_metadata_category_values(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as \
                mock_categories, patch.object(MetadataRepo,
                                              'category_values') as \
                mock_category_values:
            mock_categories.return_value = ['age_cat', 'bmi']
            mock_category_values.return_value = ['30s', '40s', '50s']
            response, code = category_values('age_cat')

        self.assertEqual(code, 200)
        exp_values = ['30s', '40s', '50s']
        obs = json.loads(response)
        self.assertCountEqual(exp_values, obs)

    def test_metadata_category_values_category_dne(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as mock_categories:
            mock_categories.return_value = ['age_cat', 'bmi']
            response, code = category_values('foo')

        self.assertEqual(code, 404)
        api_out = json.loads(response)
        self.assertRegex(api_out['text'],
                         r"Metadata category: 'foo' does not exist.")

    def test_metadata_filter_sample_ids_age_cat(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches:
            mock_matches.return_value = ['sample-1', 'sample-3']
            response, code = filter_sample_ids(age_cat='30s')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_bmi(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches:
            mock_matches.return_value = ['sample-1', 'sample-3']
            response, code = filter_sample_ids(bmi='normal')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_bmi_and_age_cat(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches:
            mock_matches.return_value = ['sample-1', 'sample-3']
            response, code = filter_sample_ids(bmi='normal', age_cat='30s')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_neither_bmi_or_age_cat(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches:
            mock_matches.return_value = ['sample-1', 'sample-3']
            response, code = filter_sample_ids(some_other_cat='bar')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)
