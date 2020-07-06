import biom
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose
import json
from unittest.mock import patch, PropertyMock
from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.models._taxonomy import Taxonomy as TaxonomyModel
from microsetta_public_api.utils import DataTable
from microsetta_public_api.utils.testing import MockedJsonifyTestCase
from microsetta_public_api.api.taxonomy import (
    resources, summarize_group, _summarize_group, single_sample,
    group_taxa_present, single_sample_taxa_present,
)


class TaxonomyImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.taxonomy.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    @classmethod
    def setUpClass(cls):
        cls.post_body = {'sample_ids': ['sample-1',
                                        'sample-2',
                                        ]}
        cls.table = biom.Table(np.array([[0, 1, 2],
                                         [2, 4, 6],
                                         [3, 0, 1]]),
                               ['feature-1', 'feature-2', 'feature-3'],
                               ['sample-1', 'sample-2', 'sample-3'])
        cls.taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                        ['feature-2', 'a; b; c; d; e', 0.345],
                                        ['feature-3', 'a; f; g; h', 0.678]],
                                       columns=['Feature ID', 'Taxon',
                                                'Confidence'])
        cls.taxonomy_df.set_index('Feature ID', inplace=True)

        # variances
        cls.table_vars = biom.Table(np.array([[0, 1, 2],
                                              [2, 4, 6],
                                              [3, 0, 1]]),
                                    ['feature-1', 'feature-2', 'feature-3'],
                                    ['sample-1', 'sample-2', 'sample-3'])

    def setUp(self):
        super().setUp()

    def test_taxonomy_resources_available(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = [
                'alpha', 'beta'
            ]
            exp_res = ['alpha', 'beta']
            response, code = resources()

        obs = json.loads(response)
        self.assertEqual(code, 200)
        self.assertIn('resources', obs)
        self.assertCountEqual(exp_res, obs['resources'])

    def test_taxonomy_unknown_resource(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = [
                'alpha', 'beta'
            ]
            response, code = summarize_group(self.post_body,
                                             'some-other-table'
                                             )

        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")
        self.assertEqual(code, 404)

    def test_taxonomy_unknown_sample(self):
        # One ID not found (out of two)
        with patch.object(TaxonomyRepo, 'exists') as mock_exists, \
                patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = ['foo-table']
            mock_exists.side_effect = [True, False]
            response, code = summarize_group(
                {'sample_ids': ['sample-1', 'sample-baz-bat']}, 'foo-table')

        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

        # Multiple IDs do not exist
        with patch.object(TaxonomyRepo, 'exists') as mock_exists, \
                patch.object(TaxonomyRepo, 'resources') as mock_metrics:
            mock_metrics.return_value = ['bar-table']
            mock_exists.side_effect = [False, False]
            response, code = summarize_group(
                {'sample_ids': ['sample-foo-bar',
                                'sample-baz-bat']}, 'bar-table')
        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-foo-bar',
                              'sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

    def test_taxonomy_summarize_group_simple(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                },
            }
            response, code = summarize_group(self.post_body,
                                             "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((feature-1,((feature-2)e)d)c)b,'
                         '(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-1', 'feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([1. / 10, 6. / 10, 3. / 10],
                        obs['feature_values']
                        )
        assert_allclose([0, 0, 0],
                        obs['feature_variances']
                        )

    def test_taxonomy_summarize_group_simple_with_variances(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                },
            }
            response, code = summarize_group(self.post_body,
                                             "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((feature-1,((feature-2)e)d)c)b,'
                         '(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-1', 'feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([1. / 10, 6. / 10, 3. / 10],
                        obs['feature_values']
                        )
        assert_allclose([0, 0, 0],
                        obs['feature_variances']
                        )

    def test_taxonomy_summarize_group_one_sample_with_variance(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                },
            }
            response, code = summarize_group(
                {'sample_ids': ['sample-1']}, "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([2.0, 3.0],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_unknown_resource(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = [
                'alpha', 'beta'
            ]
            response, code = _summarize_group(list(self.post_body.values()),
                                              'some-other-table'
                                              )

        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")
        self.assertEqual(code, 404)

    def test_taxonomy_from_list_unknown_sample(self):
        # One ID not found (out of two)
        with patch.object(TaxonomyRepo, 'exists') as mock_exists, \
                patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = ['foo-table']
            mock_exists.side_effect = [True, False]
            response, code = _summarize_group(
                ['sample-1', 'sample-baz-bat'], 'foo-table')

        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

        # Multiple IDs do not exist
        with patch.object(TaxonomyRepo, 'exists') as mock_exists, \
                patch.object(TaxonomyRepo, 'resources') as mock_metrics:
            mock_metrics.return_value = ['bar-table']
            mock_exists.side_effect = [False, False]
            response, code = _summarize_group(
                ['sample-foo-bar',
                 'sample-baz-bat'], 'bar-table')
        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-foo-bar',
                              'sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

    def test_taxonomy_from_list_summarize_group_simple(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                },
            }
            response, code = _summarize_group(self.post_body['sample_ids'],
                                              "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((feature-1,((feature-2)e)d)c)b,'
                         '(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-1', 'feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([1. / 10, 6. / 10, 3. / 10],
                        obs['feature_values']
                        )
        assert_allclose([0, 0, 0],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_summarize_group_simple_cached_model(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'model': TaxonomyModel(self.table, self.taxonomy_df)
                },
            }
            response, code = _summarize_group(self.post_body['sample_ids'],
                                              "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((feature-1,((feature-2)e)d)c)b,'
                         '(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-1', 'feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([1. / 10, 6. / 10, 3. / 10],
                        obs['feature_values']
                        )
        assert_allclose([0, 0, 0],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_summarize_group_simple_with_variances(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                },
            }
            response, code = _summarize_group(self.post_body['sample_ids'],
                                              "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((feature-1,((feature-2)e)d)c)b,'
                         '(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-1', 'feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([1. / 10, 6. / 10, 3. / 10],
                        obs['feature_values']
                        )
        assert_allclose([0, 0, 0],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_summarize_group_one_sample_with_variance(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                },
            }
            response, code = _summarize_group(
                ['sample-1'], "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([2.0, 3.0],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_summarize_single_simple(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                },
            }
            response, code = single_sample('sample-1',
                                           "some-table")
        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances']
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([2, 3],
                        obs['feature_variances']
                        )

    def test_taxonomy_from_list_summarize_single_sample_simple(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                },
            }
            response, code = single_sample(
                'sample-1', "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['taxonomy', 'features', 'feature_values',
                    'feature_variances'
                    ]
        obs = json.loads(response)

        self.assertCountEqual(exp_keys, obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances'])


class TaxonomyTaxaPresentDataTableImplementationTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.taxonomy.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    @classmethod
    def setUpClass(cls):
        cls.post_body = {'sample_ids': ['sample-1',
                                        'sample-2',
                                        ]}
        cls.table = biom.Table(np.array([[0, 1, 2],
                                         [2, 4, 6],
                                         [3, 0, 1]]),
                               ['feature-1', 'feature-2', 'feature-3'],
                               ['sample-1', 'sample-2', 'sample-3'])
        cls.taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                        ['feature-2', 'a; b; c; d; e', 0.345],
                                        ['feature-3', 'a; f; g; h', 0.678]],
                                       columns=['Feature ID', 'Taxon',
                                                'Confidence'])
        cls.taxonomy_df.set_index('Feature ID', inplace=True)

        # variances
        cls.table_vars = biom.Table(np.array([[0, 1, 2],
                                              [2, 4, 6],
                                              [3, 0, 1]]),
                                    ['feature-1', 'feature-2', 'feature-3'],
                                    ['sample-1', 'sample-2', 'sample-3'])
        cls.taxonomy_model = TaxonomyModel(cls.table, cls.taxonomy_df,
                                           cls.table_vars)

    def test_single_sample_taxa_data_table(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables, \
                patch.object(TaxonomyModel, 'presence_data_table') as \
                mock_model:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                    'model': self.taxonomy_model,
                },
            }
            mock_model.return_value = DataTable.from_dataframe(
                pd.DataFrame({
                    'sampleId': ['sample-1', 'sample-1'],
                    'rank_1': ['a', 'a'],
                    'rank_2': ['b', 'f'],
                })
            )
            response, code = single_sample_taxa_present(
                'sample-1', "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['data', 'columns']
        obs = json.loads(response)
        print(obs)
        self.assertCountEqual(exp_keys, obs.keys())
        self.assertCountEqual(obs['columns'], [{'data': 'sampleId'},
                                               {'data': 'rank_1'},
                                               {'data': 'rank_2'}])
        for item in obs['data']:
            self.assertCountEqual(item.keys(), ['sampleId', 'rank_1',
                                                'rank_2'])

    def test_group_taxa_data_table(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables, \
                patch.object(TaxonomyModel, 'presence_data_table') as \
                mock_model:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                    'model': self.taxonomy_model,
                },
            }
            mock_model.return_value = DataTable.from_dataframe(
                pd.DataFrame({
                    'sampleId': ['sample-1', 'sample-1', 'sample-2'],
                    'rank_1': ['a', 'a', 'a'],
                    'rank_2': ['b', 'f', 'b'],
                })
            )
            response, code = group_taxa_present(
                {'sample_ids': ['sample-1', 'sample-2']}, "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['data', 'columns']
        obs = json.loads(response)
        print(obs)
        self.assertCountEqual(exp_keys, obs.keys())
        self.assertCountEqual(obs['columns'], [{'data': 'sampleId'},
                                               {'data': 'rank_1'},
                                               {'data': 'rank_2'}])
        for item in obs['data']:
            self.assertCountEqual(item.keys(), ['sampleId', 'rank_1',
                                                'rank_2'])

    def test_group_taxa_data_table_404(self):
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                    'variances': self.table_vars,
                    'model': self.taxonomy_model,
                },
            }
            response, code = group_taxa_present(
                {'sample_ids': ['sample-1', 'dne-sample']}, "some-table")

        self.assertEqual(code, 404)
