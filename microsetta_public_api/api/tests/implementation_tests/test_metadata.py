import json
from unittest.mock import patch, PropertyMock
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.exceptions import UnknownID, UnknownCategory
from microsetta_public_api.api.metadata import (
    category_values,
    filter_sample_ids,
    filter_sample_ids_query_builder,
    categories,
    get_metadata_values,
    category_values_alt,
    filter_sample_ids_alt,
    filter_sample_ids_query_builder_alt,
    categories_alt,
    get_metadata_values_alt,
)
import pandas as pd


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

    def test_metadata_categories(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6]], columns=['cat', 'fish', 'dog'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            response, code = categories()
        self.assertEqual(code, 200)
        exp_values = ['cat', 'fish', 'dog']
        obs = json.loads(response)
        self.assertEqual(obs, exp_values)

    def test_metadata_values(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            response, code = get_metadata_values(body=['sample-01',
                                                       'sample-03'],
                                                 cat=['fish', 'dog']
                                                 )
        self.assertEqual(code, 200)
        exp_values = [[2, 3], ['bar', 'baz']]
        obs = json.loads(response)
        self.assertEqual(obs, exp_values)

    def test_metadata_values_dne_category_404(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            with self.assertRaises(UnknownCategory):
                get_metadata_values(body=['sample-01',
                                          'sample-03'],
                                    cat=['fish', 'dne_cat']
                                    )

    def test_metadata_values_dne_sample_id_404(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            with self.assertRaises(UnknownID):
                get_metadata_values(body=['sample-01',
                                          'sample-dne'],
                                    cat=['fish', 'dog']
                                    )

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


class MetadataAltImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.metadata.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    filter_methods = [filter_sample_ids_alt,
                      filter_sample_ids_query_builder_alt]

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
        cls.dataset = 'dataset_name_example'

    def test_metadata_categories(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6]], columns=['cat', 'fish', 'dog'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo_alt') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            response, code = categories_alt(self.dataset)
            mock_repo.assert_called_with(self.dataset)
        self.assertEqual(code, 200)
        exp_values = ['cat', 'fish', 'dog']
        obs = json.loads(response)
        self.assertEqual(obs, exp_values)

    def test_metadata_values(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo_alt') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            response, code = get_metadata_values_alt(
                dataset=self.dataset,
                body=['sample-01', 'sample-03'],
                cat=['fish', 'dog']
            )
        self.assertEqual(code, 200)
        exp_values = [[2, 3], ['bar', 'baz']]
        obs = json.loads(response)
        self.assertEqual(obs, exp_values)

    def test_metadata_values_dne_category_404(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo_alt') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            with self.assertRaises(UnknownCategory):
                get_metadata_values_alt(
                    body=['sample-01',
                          'sample-03'],
                    dataset=self.dataset,
                    cat=['fish', 'dne_cat']
                    )

    def test_metadata_values_dne_sample_id_404(self):
        metadata_df = pd.DataFrame(
            [[1, 2, 3], [4, 5, 6], ['foo', 'bar', 'baz']],
            columns=['cat', 'fish', 'dog'],
            index=['sample-01', 'sample-02', 'sample-03'],
        )
        with patch('microsetta_public_api.api.metadata._get_repo_alt') as \
                mock_repo:
            mock_repo.return_value = MetadataRepo(metadata_df)
            with self.assertRaises(UnknownID):
                get_metadata_values_alt(
                    body=['sample-01',
                          'sample-dne'],
                    dataset=self.dataset,
                    cat=['fish', 'dog']
                    )

    def test_metadata_category_values(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as \
                mock_categories, patch.object(MetadataRepo,
                                              'category_values') as \
                mock_category_values:
            mock_categories.return_value = ['age_cat', 'bmi']
            mock_category_values.return_value = ['30s', '40s', '50s']
            response, code = category_values_alt(self.dataset, 'age_cat')

        self.assertEqual(code, 200)
        exp_values = ['30s', '40s', '50s']
        obs = json.loads(response)
        self.assertCountEqual(exp_values, obs)

    def test_metadata_category_values_category_dne(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as mock_categories:
            mock_categories.return_value = ['age_cat', 'bmi']
            response, code = category_values_alt(self.dataset, 'foo')

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
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                age_cat='30s')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_bmi(self):
        with patch.object(MetadataRepo, 'sample_id_matches') as mock_matches, \
                patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                      'categories', new_callable=PropertyMock) \
                as mock_categories:
            mock_matches.return_value = ['sample-1', 'sample-3']
            mock_categories.return_value = ['bmi']
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                bmi='normal')
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
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                bmi='normal', age_cat='30s')
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
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                some_other_cat='bar')
        self.assertEqual(code, 200)
        exp = {'sample_ids': ['sample-1', 'sample-3']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)

    def test_metadata_filter_sample_ids_category_unknown_expect_404(self):
        with patch('microsetta_public_api.repo._metadata_repo.MetadataRepo.'
                   'categories', new_callable=PropertyMock) as \
                mock_categories:
            mock_categories.return_value = ['age_cat', 'bmi']
            response, code = filter_sample_ids_alt(some_other_cat='bar',
                                                   dataset=self.dataset,
                                                   )
        self.assertEqual(code, 404)

    def test_metadata_filter_sample_ids_taxonomy_unknown(self):
        args = [[], [dict(condition="AND", rules=[])]]
        for method, arg in zip(self.filter_methods, args):
            with self.subTest():
                response, code = method(*arg,
                                        dataset=self.dataset,
                                        taxonomy='some-tax')
                self.assertEqual(code, 404)

    def test_metadata_filter_sample_ids_alpha_metric_unknown(self):
        args = [[], [dict(condition="AND", rules=[])]]
        for method, arg in zip(self.filter_methods, args):
            with self.subTest():
                response, code = method(*arg,
                                        dataset=self.dataset,
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
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                age_cat='30s',
                taxonomy='agp')
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
            response, code = filter_sample_ids_alt(
                dataset=self.dataset,
                age_cat='30s', alpha_metric='faith_pd')
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
            response, code = filter_sample_ids_query_builder_alt(
                self.sample_querybuilder,
                dataset=self.dataset,
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
            response, code = filter_sample_ids_query_builder_alt(
                self.sample_querybuilder,
                dataset=self.dataset,
                taxonomy='agp',
                alpha_metric='alpha_met',
            )
        self.assertEqual(200, code)
        exp = {'sample_ids': ['sample-2']}
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)
