import biom
import numpy as np
import pandas as pd
from numpy.testing import assert_allclose
import json
from unittest.mock import patch, PropertyMock
from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo
from microsetta_public_api.models._taxonomy import Taxonomy as TaxonomyModel
from microsetta_public_api.utils import DataTable
from microsetta_public_api.exceptions import UnknownResource
from microsetta_public_api.utils.testing import (
    MockMetadataElement,
    MockedJsonifyTestCase,
    TrivialVisitor,
)
from microsetta_public_api.api.taxonomy import (
    resources, summarize_group, _summarize_group, single_sample,
    group_taxa_present, single_sample_taxa_present,
    exists_single, exists_group,
    single_sample_alt,
    summarize_group_alt,
    resources_alt,
    single_sample_taxa_present_alt,
    group_taxa_present_alt,
    exists_single_alt,
    exists_group_alt,
    ranks_sample,
    ranks_specific,
    get_empress,
)
from microsetta_public_api.config import DictElement, TaxonomyElement


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

    def test_taxonomy_exists_single(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources, \
                patch.object(TaxonomyRepo, 'exists') as mock_exists:
            mock_resources.return_value = [
                'table2', 'othertab',
            ]
            mock_exists.return_value = True

            response, code = exists_single(resource='table2',
                                           sample_id='sample_1')
            obs = json.loads(response)
        self.assertTrue(obs)
        self.assertEqual(200, code)

    def test_taxonomy_exists_single_404(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources, \
                patch.object(TaxonomyRepo, 'exists') as mock_exists:
            mock_resources.return_value = [
                'table2', 'othertab',
            ]
            mock_exists.side_effect = [True]

            response, code = exists_single(resource='other-tab',
                                           sample_id='sample_1')
        self.assertEqual(404, code)

    def test_taxonomy_exists_group(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources, \
                patch.object(TaxonomyRepo, 'exists') as mock_exists:
            mock_resources.return_value = [
                'table2', 'othertab',
            ]
            mock_exists.return_value = [True, False, True]

            response, code = exists_group(resource='table2',
                                          body=['s1', 's2', 's3'])
            obs = json.loads(response)
        self.assertListEqual(obs, [True, False, True])
        self.assertEqual(200, code)

    def test_taxonomy_exists_group_404(self):
        with patch.object(TaxonomyRepo, 'resources') as mock_resources, \
                patch.object(TaxonomyRepo, 'exists') as mock_exists:
            mock_resources.return_value = [
                'table2', 'othertab',
            ]
            mock_exists.side_effect = [True, False, True]

            response, code = exists_group(resource='other-tab',
                                          body=['s1', 's2', 's3'])
        self.assertEqual(404, code)

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
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
        with patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = [
                'alpha', 'beta'
            ]
            response, code = _summarize_group(list(self.post_body.values()),
                                              'some-other-table',
                                              taxonomy_repo=TaxonomyRepo(),
                                              )

        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")
        self.assertEqual(code, 404)

    def test_taxonomy_from_list_unknown_sample(self):
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
        # One ID not found (out of two)
        with patch.object(TaxonomyRepo, 'exists') as mock_exists, \
                patch.object(TaxonomyRepo, 'resources') as mock_resources:
            mock_resources.return_value = ['foo-table']
            mock_exists.side_effect = [True, False]
            response, code = _summarize_group(
                ['sample-1', 'sample-baz-bat'], 'foo-table',
                taxonomy_repo=TaxonomyRepo(),
            )

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
                 'sample-baz-bat'], 'bar-table',
                taxonomy_repo=TaxonomyRepo(),
            )
        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-foo-bar',
                              'sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

    def test_taxonomy_from_list_summarize_group_simple(self):
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo.'
                   'tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {
                'some-table': {
                    'table': self.table,
                    'feature-data-taxonomy': self.taxonomy_df,
                },
            }
            response, code = _summarize_group(self.post_body['sample_ids'],
                                              "some-table",
                                              taxonomy_repo=TaxonomyRepo(),
                                              )
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
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
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
                                              "some-table",
                                              taxonomy_repo=TaxonomyRepo(),
                                              )
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
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
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
                                              "some-table",
                                              taxonomy_repo=TaxonomyRepo(),
                                              )
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
        # NOTE: do not delete this test when converting _alt methods to non
        # _alt methods
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
                ['sample-1'], "some-table",
                taxonomy_repo=TaxonomyRepo(),
            )

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


class TestTaxonomyAltImplementation(MockedJsonifyTestCase):

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

        cls.table_name = 'some-table'
        cls.table_with_var_name = 'some-table-w-var'

        cls.resources = DictElement({
            'datasets': DictElement({
                'dataset1': DictElement({
                    '__taxonomy__': TaxonomyElement({
                        cls.table_name: {
                            'table': cls.table,
                            'feature-data-taxonomy': cls.taxonomy_df,
                        },
                        cls.table_with_var_name: {
                            'table': cls.table,
                            'feature-data-taxonomy': cls.taxonomy_df,
                            'variances': cls.table_vars,
                        }
                    })
                }),
                'dataset2': DictElement({}),
                '__metadata__': MockMetadataElement(pd.DataFrame({
                    'age_cat': ['30s', '40s', '50s', '30s', '30s'],
                    'num_var': [3, 4, 5, 6, 7],
                }, index=['s01', 's02', 's04', 's05', 'sOther']))
            }),
        })
        cls.resources.accept(TrivialVisitor())
        cls.res_patcher = patch(
            'microsetta_public_api.api.taxonomy.get_resources')
        cls.mock_resources = cls.res_patcher.start()
        cls.mock_resources.return_value = cls.resources

    def test_get_empress(self):
        response = get_empress('dataset1', self.table_name)
        tree_names = [
            -1,
            'a; b; c; d; e',
            'a; b; c; d;',
            'a; b; c;',
            'a; b; c',
            'a; b;',
            'a; f; g; h',
            'a; f; g;',
            'a; f;',
            'a;',
            None
        ]
        self.assertCountEqual(
            tree_names, response['names']
        )

    def test_single_sample_alt(self):
        response, code = single_sample_alt('dataset1', 'sample-1',
                                           self.table_with_var_name)
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

    def test_single_sample_unknown_errors(self):
        response, code = single_sample_alt('dataset1', 'sample-1',
                                           'other-table')
        self.assertEqual(code, 404)

        with self.assertRaises(UnknownResource):
            single_sample_alt('dataset2', 'sample-1', self.table_name)

    def test_taxonomy_unknown_resource_alt(self):
        response, code = summarize_group_alt(self.post_body,
                                             'dataset1',
                                             'some-other-table',
                                             )

        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")
        self.assertEqual(code, 404)

    def test_taxonomy_unknown_sample_alt(self):
        # One ID not found (out of two)
        response, code = summarize_group_alt(
            {'sample_ids': ['sample-1', 'sample-baz-bat']},
            'dataset1', self.table_name)

        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

        # Multiple IDs do not exist
        response, code = summarize_group_alt(
            {'sample_ids': ['sample-foo-bar',
                            'sample-baz-bat']},
            'dataset1',
            self.table_name)
        self.assertEqual(code, 404)
        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-foo-bar',
                              'sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')

    def test_taxonomy_ranks_sample(self):
        response, code = ranks_sample('dataset1', self.table_name,
                                      5)
        self.assertEqual(code, 200)
        api_out = json.loads(response.data)
        exp = {'b', 'f'}
        self.assertTrue(set(api_out['Taxon']).issubset(exp))

    def test_taxonomy_ranks_sample_unknown_dataset(self):
        with self.assertRaises(UnknownResource):
            ranks_sample('dataset-foo', self.table_name, 100)

    def test_taxonomy_ranks_sample_unknown_resource(self):
        response, code = ranks_sample('dataset1', 'some-other-table',
                                      100)
        self.assertEqual(code, 404)
        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")

    def test_taxonomy_ranks_specific(self):
        response, code = ranks_specific('dataset1', self.table_name,
                                        'sample-1')
        self.assertEqual(code, 200)
        api_out = json.loads(response.data)
        exp = {'Taxon': ['b', 'f'],
               'Rank': [1.0, 2.0],
               'Taxa-order': ['b', 'f']}
        self.assertEqual(api_out, exp)

    def test_taxonomy_ranks_specific_unknown_dataset(self):
        with self.assertRaises(UnknownResource):
            ranks_specific('dataset-foo', self.table_name, 'sample-1')

    def test_taxonomy_ranks_specific_unknown_resource(self):
        response, code = ranks_specific('dataset1', 'some-other-table',
                                        'sample-1')
        self.assertEqual(code, 404)
        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested resource: 'some-other-table' is "
                         r"unavailable. "
                         r"Available resource\(s\): \[(.*)\]")
        self.assertEqual(code, 404)

    def test_taxonomy_ranks_specific_unknown_sample_id(self):
        response, code = ranks_specific('dataset1', self.table_name, 'foobar')
        self.assertEqual(code, 404)
        response = json.loads(response.data)
        self.assertListEqual(response['missing_ids'], ['foobar', ])

    def test_taxonomy_summarize_group_simple_alt(self):
        response, code = summarize_group_alt(self.post_body,
                                             'dataset1',
                                             self.table_name)
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

    def test_taxonomy_summarize_group_simple_with_variances_alt(self):
        response, code = summarize_group_alt(self.post_body,
                                             'dataset1',
                                             self.table_with_var_name)
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

    def test_taxonomy_summarize_group_one_sample_with_variance_alt(self):
        response, code = summarize_group_alt(
            {'sample_ids': ['sample-1']},
            'dataset1',
            self.table_with_var_name,
        )

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

    def test_taxonomy_resources_available_alt(self):
        response, code = resources_alt('dataset1')
        obs = json.loads(response)
        self.assertEqual(code, 200)
        self.assertIn('resources', obs)
        exp_res = [self.table_name, self.table_with_var_name]
        self.assertCountEqual(exp_res, obs['resources'])

    def test_single_sample_taxa_data_table_alt(self):
        with patch.object(TaxonomyModel, 'presence_data_table') as mock_model:
            mock_model.return_value = DataTable.from_dataframe(
                pd.DataFrame({
                    'sampleId': ['sample-1', 'sample-1'],
                    'rank_1': ['a', 'a'],
                    'rank_2': ['b', 'f'],
                })
            )
            response, code = single_sample_taxa_present_alt(
                'dataset1',
                'sample-1', self.table_name)

        self.assertEqual(code, 200)
        exp_keys = ['data', 'columns']
        obs = json.loads(response)
        self.assertCountEqual(exp_keys, obs.keys())
        self.assertCountEqual(obs['columns'], [{'data': 'sampleId'},
                                               {'data': 'rank_1'},
                                               {'data': 'rank_2'}])
        for item in obs['data']:
            self.assertCountEqual(item.keys(), ['sampleId', 'rank_1',
                                                'rank_2'])

    def test_group_taxa_data_table_alt(self):
        with patch.object(TaxonomyModel, 'presence_data_table') as mock_model:
            mock_model.return_value = DataTable.from_dataframe(
                pd.DataFrame({
                    'sampleId': ['sample-1', 'sample-1', 'sample-2'],
                    'rank_1': ['a', 'a', 'a'],
                    'rank_2': ['b', 'f', 'b'],
                })
            )
            response, code = group_taxa_present_alt(
                {'sample_ids': ['sample-1', 'sample-2']},
                "dataset1",
                "some-table")

        self.assertEqual(code, 200)
        exp_keys = ['data', 'columns']
        obs = json.loads(response)
        self.assertCountEqual(exp_keys, obs.keys())
        self.assertCountEqual(obs['columns'], [{'data': 'sampleId'},
                                               {'data': 'rank_1'},
                                               {'data': 'rank_2'}])
        for item in obs['data']:
            self.assertCountEqual(item.keys(), ['sampleId', 'rank_1',
                                                'rank_2'])

    def test_group_taxa_data_table_404_alt(self):
        response, code = group_taxa_present_alt(
            {'sample_ids': ['sample-1', 'dne-sample']},
            "dataset1",
            "some-table")

        self.assertEqual(code, 404)

    def test_taxonomy_exists_single_alt(self):
        response, code = exists_single_alt(resource=self.table_name,
                                           dataset='dataset1',
                                           sample_id='sample-1')
        obs = json.loads(response)
        self.assertTrue(obs)
        self.assertEqual(200, code)

    def test_taxonomy_exists_single_404_alt(self):
        response, code = exists_single_alt(resource='other-tab',
                                           dataset='dataset1',
                                           sample_id='sample_1')
        self.assertEqual(404, code)

        with self.assertRaises(UnknownResource):
            exists_single_alt(resource=self.table_name,
                              dataset='dne',
                              sample_id='none',
                              )

    def test_taxonomy_exists_group_alt(self):
        response, code = exists_group_alt(resource=self.table_name,
                                          dataset='dataset1',
                                          body=['sample-1', 's2', 'sample-3'])
        obs = json.loads(response)
        self.assertListEqual(obs, [True, False, True])
        self.assertEqual(200, code)

    def test_taxonomy_exists_group_404(self):
        response, code = exists_group_alt(resource='other-tab',
                                          dataset='dataset1',
                                          body=['s1', 's2', 's3'])
        self.assertEqual(404, code)

        with self.assertRaises(UnknownResource):
            exists_group_alt(resource=self.table_name,
                             dataset='dne',
                             body=['s1', 's2', 's3']
                             )
