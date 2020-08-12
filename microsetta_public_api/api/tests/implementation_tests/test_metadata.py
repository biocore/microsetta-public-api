import json
from unittest.mock import patch, PropertyMock
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.api.metadata import (
    category_values,
    filter_sample_ids,
    filter_sample_ids_query_builder,
)
from microsetta_public_api.resources_alt import resources_alt, Component
from microsetta_public_api.config import SERVER_CONFIG


class MetadataComponentImplementationTests(MockedJsonifyTestCase):
    jsonify_to_patch = [
        'microsetta_public_api.api.metadata.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()
        root = Component('root')
        datasets = Component('datasets')
        metadata = Component('metadata')
        root.add_child(datasets).add_child(metadata)

        class MockRepo:
            categories = ['age_cat']

            def category_values(self, _):
                return ['30s', '40s', '90s']

        metadata.set_data(MockRepo())
        resources_alt.set(root)

    def tearDown(self):
        res = Component.from_dict(SERVER_CONFIG['resources'])
        resources_alt.set(res)
        super().tearDown()

    def test_metadata_category_values_with_component_resources(self):
        response, code = category_values('age_cat')

        self.assertEqual(code, 200)
        exp_values = ['30s', '40s', '90s']
        obs = json.loads(response)
        self.assertCountEqual(exp_values, obs)


class MetadataImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.metadata.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    filter_methods = [filter_sample_ids, filter_sample_ids_query_builder]

    @classmethod
    def setUpClass(cls):
        cls.sample_querybuilder = {
            "condition": "AND",
            "rules": [
                {
                    "id": "age_cat",
                    "field": "age_cat",
                    "type": "string",
                    "input": "select",
                    "operator": "equal",
                    "value": "30s"
                },
            ]
        }

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
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['age_cat']
            response, code = filter_sample_ids(age_cat='30s')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_bmi(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
            patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                  'categories', new_callable=PropertyMock) as mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['bmi']
            response, code = filter_sample_ids(bmi='normal')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_bmi_and_age_cat(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['bmi', 'age_cat']
            response, code = filter_sample_ids(bmi='normal', age_cat='30s')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_neither_bmi_or_age_cat(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['some_other_cat']
            response, code = filter_sample_ids(some_other_cat='bar')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_category_unknown_expect_404(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as \
                    mock_categories:
            mock_categories.return_value = ['age_cat', 'bmi']
            response, code = filter_sample_ids(some_other_cat='bar')
        self.assertEqual(code, 404)

    def test_metadata_filter_sample_ids_taxonomy_unknown(self):
        args = [[], [dict(condition="AND", rules=[])]]
        for method, arg in zip(self.filter_methods, args):
            with self.subTest():
                response, code = method(*arg, taxonomy='some-tax')
                self.assertEqual(code, 404)

    def test_metadata_filter_sample_ids_alpha_metric_unknown(self):
        args = [[], [dict(condition="AND", rules=[])]]
        for method, arg in zip(self.filter_methods, args):
            with self.subTest():
                response, code = method(*arg,
                                        alpha_metric='some-unknown-metric')
                self.assertEqual(code, 404)

    def test_metadata_filter_sample_ids_taxonomy_filter(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories, \
                patch('microsetta_public_api.api.metadata'
                      '.TaxonomyRepo.exists') as mock_exists, \
                patch('microsetta_public_api.api.metadata.validate_resource'
                      '') as mock_invalid_resource:
            mock_matches.return_value = ['sample-1', 'sample-2', 'sample-3']
            mock_categories.return_value = ['age_cat']
            mock_exists.side_effect = [False, True, True]
            mock_invalid_resource.return_value = False
            response, code = filter_sample_ids(age_cat='30s', taxonomy='agp')
        self.assertEqual(200, code)
        exp = {'sample_ids': ['sample-2', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_alpha_metric_filter(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories, \
                patch('microsetta_public_api.api.metadata'
                      '.AlphaRepo.exists') as mock_exists, \
                patch('microsetta_public_api.api.metadata.validate_resource'
                      '') as mock_invalid_resource:
            mock_matches.return_value = ['sample-1', 'sample-2', 'sample-3']
            mock_categories.return_value = ['age_cat']
            mock_exists.side_effect = [True, False, True]
            mock_invalid_resource.return_value = False
            response, code = filter_sample_ids(age_cat='30s',
                                               alpha_metric='faith_pd')
        self.assertEqual(200, code)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_query_builder(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['age_cat']
            response, code = filter_sample_ids_query_builder(
                self.sample_querybuilder,
            )
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_query_builder_resource_filters(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) as \
                mock_categories, \
                patch('microsetta_public_api.api.metadata'
                      '.TaxonomyRepo.exists') as mock_exists, \
                patch('microsetta_public_api.api.metadata'
                      '.AlphaRepo.exists') as mock_exists_alpha, \
                patch('microsetta_public_api.api.metadata.validate_resource'
                      '') as mock_invalid_resource:
            mock_matches.return_value = ['sample-1', 'sample-2', 'sample-3']
            mock_categories.return_value = ['age_cat']
            # filters sample_id's down to ['sample-2', 'sample-3']
            mock_exists.side_effect = [False, True, True]
            # filters ['sample-2', 'sample-3'] down to ['sample-2']
            mock_exists_alpha.side_effect = [True, False]
            mock_invalid_resource.side_effect = [False, False]
            response, code = filter_sample_ids_query_builder(
                self.sample_querybuilder,
                taxonomy='agp',
                alpha_metric='alpha_met',
            )
        self.assertEqual(200, code)
        exp = {'sample_ids': ['sample-2']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)
