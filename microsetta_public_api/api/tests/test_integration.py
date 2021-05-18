import json
import numpy as np
import pandas as pd
import biom
from biom.util import biom_open
from qiime2 import Artifact, Metadata
from numpy.testing import assert_allclose
from skbio.stats.ordination import OrdinationResults
from copy import deepcopy

from microsetta_public_api import config
from microsetta_public_api.config import schema
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import FlaskTests, \
    TempfileTestCase, ConfigTestCase
from microsetta_public_api.utils import create_data_entry, DataTable
from microsetta_public_api.resources_alt import resources_alt, Q2Visitor


def _update_resources_from_config(config):
    config_elements = deepcopy(config)
    schema.make_elements(config_elements)
    resources_alt.updates(config_elements)
    resources_alt.accept(Q2Visitor())


class IntegrationTests(FlaskTests, TempfileTestCase, ConfigTestCase):
    def setUp(self):
        ConfigTestCase.setUp(self)
        FlaskTests.setUp(self)
        TempfileTestCase.setUp(self)

    def tearDown(self):
        TempfileTestCase.tearDown(self)
        FlaskTests.tearDown(self)
        ConfigTestCase.tearDown(self)


class MetadataIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.metadata_path = self.create_tempfile(suffix='.txt').name
        self.metadata_table = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not',
                            'normal', 'overweight'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15, np.nan],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6',
                                'sample-7',
                                ],
                               name='#SampleID')
        )

        Metadata(self.metadata_table).save(self.metadata_path)

        self.sample_querybuilder = {
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
        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__metadata__': self.metadata_path,
                },
                '__metadata__': self.metadata_path,
            }
        }
        _update_resources_from_config(config_alt)

    def test_dataset_available(self):
        exp = ['16SAmplicon']
        response = self.client.get(
            '/results-api/sample/list/dataset/sample-3'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

        exp = []
        response = self.client.get(
            '/results-api/sample/list/dataset/sample-dne'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_dataset_contains(self):
        response = self.client.get(
            '/results-api/sample/dataset/16SAmplicon/contains/sample-3'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertTrue(obs)

        response = self.client.get(
            '/results-api/sample/dataset/16SAmplicon/contains/sample-dne'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertFalse(obs)

    def test_metadata_available_categories_with_dataset(self):
        exp = ['age_cat', 'bmi_cat', 'num_cat']
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/metadata'
            '/category/available'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_available_categories(self):
        exp = ['age_cat', 'bmi_cat', 'num_cat']
        response = self.client.get(
            'results-api/metadata/category/available'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_category_values_returns_string_array(self):
        exp = ['30s', '40s', '50s']
        response = self.client.get(
            "/results-api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_category_values_returns_numeric_array(self):
        exp = [20, 30, 7.15, 8.25]
        response = self.client.get(
            "/results-api/metadata/category/values/num_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_category_values_returns_404(self):
        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/results-api/metadata/category/values/non-existing-cat")
        self.assertStatusCode(404, response)

    def test_metadata_sample_ids_returns_simple(self):
        exp_ids = ['sample-1', 'sample-4']
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_returns_simple_post(self):
        exp_ids = ['sample-1', 'sample-4']
        response = self.client.post(
            "/results-api/metadata/sample_ids",
            content_type='application/json',
            data=json.dumps({
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
                    {
                        "id": "bmi_cat",
                        "field": "bmi_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "normal"
                    },
                ]
            })
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_returns_nested_post(self):
        exp_ids = ['sample-1', 'sample-4', 'sample-5']
        response = self.client.post(
            "/results-api/metadata/sample_ids",
            content_type='application/json',
            data=json.dumps({
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
                    {
                        "condition": "OR",
                        "rules": [
                            {
                                "id": "bmi_cat",
                                "field": "bmi_cat",
                                "type": "string",
                                "input": "select",
                                "operator": "equal",
                                "value": "normal"
                            },
                            {
                                "id": "bmi_cat",
                                "field": "bmi_cat",
                                "type": "string",
                                "input": "select",
                                "operator": "equal",
                                "value": "not"
                            },
                        ],
                    },
                ]
            })
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_returns_empty(self):
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=20s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertEqual(obs['sample_ids'], [])

    def test_metadata_sample_ids_extra_categories_have_no_effect(self):
        exp_ids = ['sample-1', 'sample-4']
        # num_cat is not configured to be able to be queried on, so this
        #  tests to make sure it is ignored
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s&bmi_cat=normal&"
            "num_cat=30")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_age_cat_only(self):
        response = self.client.get(
            "/results-api/metadata/sample_ids?age_cat=30s")
        exp_ids = ['sample-1', 'sample-4', 'sample-5']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_bmi_only(self):
        response = self.client.get(
            "/results-api/metadata/sample_ids?bmi_cat=normal")
        exp_ids = ['sample-1', 'sample-4', 'sample-6']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_null_parameters_succeeds(self):
        response = self.client.get(
            "/results-api/metadata/sample_ids")
        exp_ids = ['sample-1', 'sample-2', 'sample-3', 'sample-4',
                   'sample-5', 'sample-6', 'sample-7']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_filter_on_metric_dne(self):
        response = self.client.get(
            # careful not to use a metric that exists in AlphaIntegrationTests
            '/results-api/metadata/sample_ids?alpha_metric=bad-metric')
        self.assertEqual(response.status_code, 404)

    def test_metadata_filter_on_taxonomy_dne(self):
        response = self.client.get(
            # careful not to use a table that exists in
            #  TaxonomyIntegrationTests
            '/results-api/metadata/sample_ids?alpha_metric=bad-table')
        self.assertEqual(response.status_code, 404)

    def test_metadata_filter_on_metric_and_taxonomy_dne(self):
        response = self.client.get(
            # careful not to use a metric that exists in AlphaIntegrationTests
            # careful not to use a table that exists in
            #  TaxonomyIntegrationTests
            '/results-api/metadata/sample_ids?alpha_metric=bad-metric&'
            'taxonomy=bad-table')
        self.assertEqual(response.status_code, 404)


class TaxonomyIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.table1_filename = self.create_tempfile(suffix='.qza').name
        self.taxonomy1_filename = self.create_tempfile(suffix='.qza').name
        self.table2_filename = self.create_tempfile(suffix='.qza').name
        self.taxonomy2_filename = self.create_tempfile(suffix='.qza').name
        self.table3_filename = self.create_tempfile(suffix='.qza').name
        self.var_table_filename = self.create_tempfile(suffix='.qza').name
        self.table_biom = self.create_tempfile(suffix='.biom').name
        self.taxonomy_greengenes_df_filename = self.create_tempfile(
            suffix='.qza').name

        self.table = biom.Table(np.array([[0, 1, 2],
                                          [2, 4, 6],
                                          [3, 0, 1]]),
                                ['feature-1', 'feature-2', 'feature-3'],
                                ['sample-1', 'sample-2', 'sample-3'])

        self.taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                         ['feature-2', 'a; b; c; d; e', 0.345],
                                         ['feature-3', 'a; f; g; h', 0.678]],
                                        columns=['Feature ID', 'Taxon',
                                                 'Confidence'])
        self.taxonomy_greengenes_df = pd.DataFrame(
            [['feature-1', 'k__a;p__b; o__c', 0.123],
             ['feature-2', 'k__a; p__b; o__c; f__d; g__e', 0.34],
             ['feature-3', 'k__a; p__f; o__g; f__h', 0.678]],
            columns=['Feature ID', 'Taxon', 'Confidence'])
        self.taxonomy_greengenes_df.set_index('Feature ID', inplace=True)

        self.taxonomy_df.set_index('Feature ID', inplace=True)

        self.table2 = biom.Table(np.array([[0, 1, 2],
                                           [2, 4, 6],
                                           [3, 0, 1]]),
                                 ['feature-1', 'feature-X', 'feature-3'],
                                 ['sample-1', 'sample-2', 'sample-3'])
        self.taxonomy2_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                          ['feature-X', 'a; b; c; d; e', 0.34],
                                          ['feature-3', 'a; f; g; h', 0.678]],
                                         columns=['Feature ID', 'Taxon',
                                                  'Confidence'])
        self.taxonomy2_df.set_index('Feature ID', inplace=True)

        self.table3 = biom.Table(np.array([[1, 2],
                                           [0, 1]]),
                                 ['feature-X', 'feature-3'],
                                 ['sample-2', 'sample-3'])

        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table
        )
        imported_artifact.save(self.table1_filename)
        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_df
        )
        imported_artifact.save(self.taxonomy1_filename)
        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table2
        )
        imported_artifact.save(self.table2_filename)
        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy2_df
        )
        imported_artifact.save(self.taxonomy2_filename)
        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table3
        )
        imported_artifact.save(self.table3_filename)
        with biom_open(self.table_biom, 'w') as f:
            self.table.to_hdf5(f, 'test-table')

        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_greengenes_df
        )
        imported_artifact.save(self.taxonomy_greengenes_df_filename)

        config.resources.update({'table_resources': {
            'table1': {
                'table': self.table1_filename,
            },
            'table2': {
                'table': self.table1_filename,
                'feature-data-taxonomy': self.taxonomy1_filename,
            },
            'table2-greengenes': {
                'table': self.table1_filename,
                'feature-data-taxonomy': self.taxonomy_greengenes_df_filename,
            },
            'table-fish': {
                'table': self.table_biom,
                'feature-data-taxonomy': self.taxonomy1_filename,
                'table-format': 'biom'
            },
            'table5': {
                'table': self.table2_filename,
            },
            'table6': {
                'table': self.table_biom,
                'table-format': 'biom',
            },
            'table-cached-model': {
                'table': self.table1_filename,
                'feature-data-taxonomy': self.taxonomy1_filename,
                'cache-taxonomy': True,
            },
        }})
        resources.update(config.resources)

    def test_resources(self):
        response = self.client.get(
            '/results-api/taxonomy/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('resources', obs)
        self.assertCountEqual(['table2', 'table-fish', 'table-cached-model',
                               'table2-greengenes'],
                              obs['resources'])

    def test_exists_single(self):
        response = self.client.get('/results-api/taxonomy/exists/'
                                   'table2?sample_id=sample-2')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertTrue(obs)

        response = self.client.get('/results-api/taxonomy/exists/'
                                   'table2?sample_id=sample-dne')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertFalse(obs)

    def test_exists_single_404(self):
        response = self.client.get('/results-api/taxonomy/exists/'
                                   'shannon?sample_id=sample-foo-bar')

        self.assertStatusCode(404, response)

    def test_exists_group(self):
        response = self.client.post(
            '/results-api/taxonomy/exists/table2',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 'sample-2']),
            content_type='application/json',
        )

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(obs, [False, False, True])

    def test_exists_group_404(self):
        response = self.client.post(
            '/results-api/diversity/alpha/exists/shannon',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 's3']),
            content_type='application/json',
        )

        self.assertStatusCode(404, response)

    def test_summarize_group(self):
        response = self.client.post('/results-api/taxonomy/group/table2',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1']}))

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())

        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_summarize_group_cached_model(self):
        response = self.client.post('/results-api/taxonomy/group/'
                                    'table-cached-model',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1']}))

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())

        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_summarize_single_sample(self):
        response = self.client.get(
            '/results-api/taxonomy/single/table2/sample-1',
        )

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_group_data_table(self):
        response = self.client.post('/results-api/taxonomy/present/group/'
                                    'table2-greengenes',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1', 'sample-2']}))

        self.assertEqual(response.status_code, 200)

        obs = json.loads(response.data)

        exp_columns = ['sampleId', 'Kingdom', 'Phylum', 'Class', 'Order',
                       'Family', 'Genus', 'Species', 'relativeAbundance']
        DataEntry = create_data_entry(exp_columns)
        exp = DataTable(
            data=[
                DataEntry(**{
                    'sampleId': 'sample-1',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': 'd',
                    'Genus': 'e',
                    'Species': None,
                    'relativeAbundance': 2. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-1',
                    'Kingdom': 'a',
                    'Phylum': 'f',
                    'Class': None,
                    'Order': 'g',
                    'Family': 'h',
                    'Genus': None,
                    'Species': None,
                    'relativeAbundance': 3. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-2',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': None,
                    'Genus': None,
                    'Species': None,
                    'relativeAbundance': 1. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-2',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': 'd',
                    'Genus': 'e',
                    'Species': None,
                    'relativeAbundance': 4. / 5,
                }),
            ],
            columns=[{'data': col} for col in exp_columns],
        ).to_dict()

        self.assertListEqual(exp['columns'],
                             obs['columns'])
        # wouldn't want to do this on a huge dataframe..., but it checks if
        #  there is a row of obs corresponding to each row of exp...
        exp_df = pd.DataFrame(exp['data'])
        obs_df = pd.DataFrame(obs['data'])
        obs_df_copy = obs_df.copy()
        for e_idx, row_exp in exp_df.iterrows():
            for o_idx, row_obs in obs_df.iterrows():
                if row_exp.eq(row_obs).all():
                    obs_df_copy.drop(index=o_idx, inplace=True)
                    break
        self.assertTrue(obs_df_copy.empty)

    def test_single_sample_data_table(self):
        response = self.client.get(
            '/results-api/taxonomy/present/single/table2/sample-1'
        )

        self.assertEqual(response.status_code, 200)


class AlphaIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.series1_filename = self.create_tempfile(suffix='.qza').name
        self.series2_filename = self.create_tempfile(suffix='.qza').name
        self.series3_filename = self.create_tempfile(suffix='.qza').name

        self.series_1 = pd.Series({
            'sample-foo-bar': 7.24, 'sample-baz-qux': 8.25,
            'sample-3': 6.4, },
            name='observed_otus'
        )

        self.series_2 = pd.Series({
            'sample-foo-bar': 9.01, 'sample-qux-quux': 9.04},
            name='chao1'
        )

        self.series_3 = pd.Series({
            'sample-1': 9.01, 'sample-2': 9.04,
            'sample-3': 9.31, 'sample-4': 9.33,
            'sample-5': 9.09, 'sample-6': 9.02,
            'sample-unique-name': 7.24,
        },
            name='shannon'
        )

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.series_1
        )
        imported_artifact.save(self.series1_filename)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.series_2
        )
        imported_artifact.save(self.series2_filename)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.series_3
        )
        imported_artifact.save(self.series3_filename)
        config.resources.update({'alpha_resources': {
            'observed_otus': self.series1_filename,
            'chao1': self.series2_filename,
            'shannon': self.series3_filename,
        }})
        resources.update(config.resources)

        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__alpha__': {
                        'observed_otus': self.series1_filename,
                        'chao1': self.series2_filename,
                        'shannon': self.series3_filename,
                    }
                }
            }
        }
        _update_resources_from_config(config_alt)

    def test_resources_available(self):
        response = self.client.get('/results-api/diversity/alpha/metrics/'
                                   'available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('alpha_metrics', obs)
        self.assertCountEqual(['observed_otus', 'chao1', 'shannon'],
                              obs['alpha_metrics'])

    def test_resources_available_alt(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/alpha/metrics/'
            'available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('alpha_metrics', obs)
        self.assertCountEqual(['observed_otus', 'chao1', 'shannon'],
                              obs['alpha_metrics'])

    def test_exists_single(self):
        response = self.client.get('/results-api/diversity/alpha/exists/'
                                   'chao1?sample_id=sample-foo-bar')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertTrue(obs)

        response = self.client.get('/results-api/diversity/alpha/exists/'
                                   'chao1?sample_id=sample-dne')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertFalse(obs)

    def test_exists_single_alt(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/alpha/exists/'
            'chao1?sample_id=sample-foo-bar')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertTrue(obs)

        response = self.client.get('/results-api/diversity/alpha/exists/'
                                   'chao1?sample_id=sample-dne')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertFalse(obs)

    def test_exists_single_404(self):
        response = self.client.get('/results-api/diversity/alpha/exists/'
                                   'dne-metric?sample_id=sample-foo-bar')

        self.assertStatusCode(404, response)

    def test_exists_single_404_alt(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/alpha/exists/'
            'dne-metric?sample_id=sample-foo-bar')

        self.assertStatusCode(404, response)

        response = self.client.get(
            '/results-api/dataset/dataset_dne/diversity/alpha/exists/'
            'dne-metric?sample_id=sample-foo-bar')

        self.assertStatusCode(404, response)

    def test_exists_group(self):
        response = self.client.post(
            '/results-api/diversity/alpha/exists/chao1',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 's3']),
            content_type='application/json',
            )

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(obs, [True, False, False])

    def test_exists_group_alt(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/exists/chao1',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 's3']),
            content_type='application/json',
        )

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(obs, [True, False, False])

    def test_exists_group_404(self):
        response = self.client.post(
            '/results-api/diversity/alpha/exists/dne-metric',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 's3']),
            content_type='application/json',
        )

        self.assertStatusCode(404, response)

    def test_exists_group_404_alt(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/exists/dne'
            '-metric',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 's3']),
            content_type='application/json',
        )

        self.assertStatusCode(404, response)

    def test_group_summary(self):
        response = self.client.post(
            '/results-api/diversity/alpha/group/observed_otus'
            '?summary_statistics=true&percentiles=0,50,100&return_raw=true',
            content_type='application/json',
            data=json.dumps({'sample_ids': ['sample-foo-bar',
                                            'sample-baz-qux']})
        )
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['alpha_metric', 'group_summary',
                               'alpha_diversity'],
                              obs.keys())
        self.assertCountEqual(['mean', 'median', 'std', 'group_size',
                               'percentile', 'percentile_values'],
                              obs['group_summary'].keys())
        self.assertListEqual([0, 50, 100],
                             obs['group_summary']['percentile'])
        self.assertEqual(3, len(obs['group_summary']['percentile_values']))
        self.assertDictEqual({'sample-foo-bar': 7.24, 'sample-baz-qux': 8.25},
                             obs['alpha_diversity'])
        self.assertEqual('observed_otus', obs['alpha_metric'])

    def test_group_summary_alt(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/group'
            '/observed_otus?summary_statistics=true&percentiles=0,50,100'
            '&return_raw=true',
            content_type='application/json',
            data=json.dumps({'sample_ids': ['sample-foo-bar',
                                            'sample-baz-qux']})
        )
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['alpha_metric', 'group_summary',
                               'alpha_diversity'],
                              obs.keys())
        self.assertCountEqual(['mean', 'median', 'std', 'group_size',
                               'percentile', 'percentile_values'],
                              obs['group_summary'].keys())
        self.assertListEqual([0, 50, 100],
                             obs['group_summary']['percentile'])
        self.assertEqual(3, len(obs['group_summary']['percentile_values']))
        self.assertDictEqual({'sample-foo-bar': 7.24, 'sample-baz-qux': 8.25},
                             obs['alpha_diversity'])
        self.assertEqual('observed_otus', obs['alpha_metric'])


class TaxonomyAltIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.table1_filename = self.create_tempfile(suffix='.qza').name
        self.taxonomy1_filename = self.create_tempfile(suffix='.qza').name
        self.table2_filename = self.create_tempfile(suffix='.qza').name
        self.taxonomy2_filename = self.create_tempfile(suffix='.qza').name
        self.table3_filename = self.create_tempfile(suffix='.qza').name
        self.var_table_filename = self.create_tempfile(suffix='.qza').name
        self.table_biom = self.create_tempfile(suffix='.biom').name
        self.taxonomy_greengenes_df_filename = self.create_tempfile(
            suffix='.qza').name

        self.table = biom.Table(np.array([[0, 1, 2],
                                          [2, 4, 6],
                                          [3, 0, 1]]),
                                ['feature-1', 'feature-2', 'feature-3'],
                                ['sample-1', 'sample-2', 'sample-3'])

        self.taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                         ['feature-2', 'a; b; c; d; e', 0.345],
                                         ['feature-3', 'a; f; g; h', 0.678]],
                                        columns=['Feature ID', 'Taxon',
                                                 'Confidence'])
        self.taxonomy_greengenes_df = pd.DataFrame(
            [['feature-1', 'k__a;p__b; o__c', 0.123],
             ['feature-2', 'k__a; p__b; o__c; f__d; g__e', 0.34],
             ['feature-3', 'k__a; p__f; o__g; f__h', 0.678]],
            columns=['Feature ID', 'Taxon', 'Confidence'])
        self.taxonomy_greengenes_df.set_index('Feature ID', inplace=True)

        self.taxonomy_df.set_index('Feature ID', inplace=True)

        self.table2 = biom.Table(np.array([[0, 1, 2],
                                           [2, 4, 6],
                                           [3, 0, 1]]),
                                 ['feature-1', 'feature-X', 'feature-3'],
                                 ['sample-1', 'sample-2', 'sample-3'])
        self.taxonomy2_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                          ['feature-X', 'a; b; c; d; e', 0.34],
                                          ['feature-3', 'a; f; g; h', 0.678]],
                                         columns=['Feature ID', 'Taxon',
                                                  'Confidence'])
        self.taxonomy2_df.set_index('Feature ID', inplace=True)

        self.table3 = biom.Table(np.array([[1, 2],
                                           [0, 1]]),
                                 ['feature-X', 'feature-3'],
                                 ['sample-2', 'sample-3'])

        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table
        )
        imported_artifact.save(self.table1_filename)
        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_df
        )
        imported_artifact.save(self.taxonomy1_filename)
        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table2
        )
        imported_artifact.save(self.table2_filename)
        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy2_df
        )
        imported_artifact.save(self.taxonomy2_filename)
        imported_artifact = Artifact.import_data(
            "FeatureTable[Frequency]", self.table3
        )
        imported_artifact.save(self.table3_filename)
        with biom_open(self.table_biom, 'w') as f:
            self.table.to_hdf5(f, 'test-table')

        imported_artifact = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_greengenes_df
        )
        imported_artifact.save(self.taxonomy_greengenes_df_filename)

        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__taxonomy__': {
                        'table-cached-model': {
                            'table': self.table1_filename,
                            'feature-data-taxonomy': self.taxonomy1_filename,
                            'cache-taxonomy': True,
                        },
                        'table6': {
                            'table': self.table_biom,
                            'table-format': 'biom',
                        },
                        'table5': {
                            'table': self.table2_filename,
                        },
                    },
                },
                'ShotgunMetagenomics': {
                    '__taxonomy__': {
                        'table1': {
                            'table': self.table1_filename,
                        },
                        'table2': {
                            'table': self.table1_filename,
                            'feature-data-taxonomy': self.taxonomy1_filename,
                        },
                        'table2-greengenes': {
                            'table': self.table1_filename,
                            'feature-data-taxonomy':
                                self.taxonomy_greengenes_df_filename,
                        },
                        'table-fish': {
                            'table': self.table_biom,
                            'feature-data-taxonomy': self.taxonomy1_filename,
                            'table-format': 'biom'
                        },
                    },
                },
            },
        }
        _update_resources_from_config(config_alt)

    def test_resources(self):
        response = self.client.get(
            '/results-api/dataset/ShotgunMetagenomics/taxonomy/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('resources', obs)
        self.assertCountEqual(['table2', 'table-fish', 'table2-greengenes',
                               ],
                              obs['resources'])

    def test_exists_single(self):
        response = self.client.get('/results-api/dataset/ShotgunMetagenomics/'
                                   'taxonomy/exists/'
                                   'table2?sample_id=sample-2')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertTrue(obs)

        response = self.client.get('/results-api/dataset/ShotgunMetagenomics/'
                                   'taxonomy/exists/'
                                   'table2?sample_id=sample-dne')

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertFalse(obs)

    def test_exists_single_404(self):
        response = self.client.get('/results-api/dataset/ShotgunMetagenomics/'
                                   'taxonomy/exists/'
                                   'shannon?sample_id=sample-foo-bar')

        self.assertStatusCode(404, response)

    def test_exists_group(self):
        response = self.client.post(
            '/results-api/dataset/ShotgunMetagenomics/taxonomy/exists/table2',
            data=json.dumps(['sample-foo-bar', 'sample-dne', 'sample-2']),
            content_type='application/json',
        )

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(obs, [False, False, True])

    def test_group_counts(self):
        self.table = biom.Table(np.array([[0, 1, 2],
                                          [2, 4, 6],
                                          [3, 0, 1]]),
                                ['feature-1', 'feature-2', 'feature-3'],
                                ['sample-1', 'sample-2', 'sample-3'])

        self.taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                         ['feature-2', 'a; b; c; d; e', 0.345],
                                         ['feature-3', 'a; f; g; h', 0.678]],
                                        columns=['Feature ID', 'Taxon',
                                                 'Confidence'])
        response = self.client.post(
            '/results-api/dataset/ShotgunMetagenomics/taxonomy/group/'
            'table2-greengenes/counts?level=Phylum',
            data=json.dumps({'sample_ids': []}),
            content_type='application/json',
        )

        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertEqual(obs, {'b': 2, 'f': 1})

    def test_specific_counts(self):
        response = self.client.get(
            '/results-api/dataset/ShotgunMetagenomics/taxonomy/single/'
            'table2-greengenes/sample-1/counts?level=Phylum'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertEqual(obs, {'b': 1, 'f': 1})

    def test_summarize_group(self):
        response = self.client.post('/results-api/dataset/ShotgunMetagenomics/'
                                    'taxonomy/group/table2',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1']}))

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())

        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_summarize_group_cached_model(self):
        response = self.client.post('/results-api/dataset/16SAmplicon/'
                                    'taxonomy/group/'
                                    'table-cached-model',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1']}))

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())

        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_summarize_single_sample(self):
        response = self.client.get(
            '/results-api/dataset/ShotgunMetagenomics/'
            'taxonomy/single/table2/sample-1',
        )

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())
        self.assertEqual('((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',
                         obs['taxonomy']
                         )
        self.assertListEqual(['feature-2', 'feature-3'],
                             obs['features'])
        assert_allclose([2. / 5, 3. / 5],
                        obs['feature_values']
                        )
        assert_allclose([0, 0],
                        obs['feature_variances']
                        )

    def test_group_data_table(self):
        response = self.client.post('/results-api/dataset/ShotgunMetagenomics/'
                                    'taxonomy/present/group/'
                                    'table2-greengenes',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1', 'sample-2']}))

        self.assertEqual(response.status_code, 200)

        obs = json.loads(response.data)

        exp_columns = ['sampleId', 'Kingdom', 'Phylum', 'Class', 'Order',
                       'Family', 'Genus', 'Species', 'relativeAbundance']
        DataEntry = create_data_entry(exp_columns)
        exp = DataTable(
            data=[
                DataEntry(**{
                    'sampleId': 'sample-1',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': 'd',
                    'Genus': 'e',
                    'Species': None,
                    'relativeAbundance': 2. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-1',
                    'Kingdom': 'a',
                    'Phylum': 'f',
                    'Class': None,
                    'Order': 'g',
                    'Family': 'h',
                    'Genus': None,
                    'Species': None,
                    'relativeAbundance': 3. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-2',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': None,
                    'Genus': None,
                    'Species': None,
                    'relativeAbundance': 1. / 5,
                }),
                DataEntry(**{
                    'sampleId': 'sample-2',
                    'Kingdom': 'a',
                    'Phylum': 'b',
                    'Class': None,
                    'Order': 'c',
                    'Family': 'd',
                    'Genus': 'e',
                    'Species': None,
                    'relativeAbundance': 4. / 5,
                }),
            ],
            columns=[{'data': col} for col in exp_columns],
        ).to_dict()

        self.assertListEqual(exp['columns'],
                             obs['columns'])
        # wouldn't want to do this on a huge dataframe..., but it checks if
        #  there is a row of obs corresponding to each row of exp...
        exp_df = pd.DataFrame(exp['data'])
        obs_df = pd.DataFrame(obs['data'])
        obs_df_copy = obs_df.copy()
        for e_idx, row_exp in exp_df.iterrows():
            for o_idx, row_obs in obs_df.iterrows():
                if row_exp.eq(row_obs).all():
                    obs_df_copy.drop(index=o_idx, inplace=True)
                    break
        self.assertTrue(obs_df_copy.empty)

    def test_single_sample_data_table(self):
        response = self.client.get(
            '/results-api/dataset/ShotgunMetagenomics/'
            'taxonomy/present/single/table2/sample-1'
        )

        self.assertEqual(response.status_code, 200)


class PlottingIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.plotting_metadata_path = self.create_tempfile(suffix='.txt').name
        self.plotting_metadata_table = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not', 'normal'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6'],
                               name='#SampleID')
        )

        Metadata(self.plotting_metadata_table).save(
            self.plotting_metadata_path)

        config.resources.update({'metadata': self.plotting_metadata_path})

        self.plotting_series1_filename = self.create_tempfile(
            suffix='.qza').name
        self.plotting_series2_filename = self.create_tempfile(
            suffix='.qza').name

        self.plotting_series_1 = pd.Series({
            'sample-2': 7.24, 'sample-4': 8.25,
            'sample-3': 6.4, },
            name='observed_otus'
        )

        self.plotting_series_2 = pd.Series({
            'sample-2': 9.01, 'sample-5': 9.04},
            name='chao1'
        )

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.plotting_series_1
        )
        imported_artifact.save(self.plotting_series1_filename)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.plotting_series_2
        )
        imported_artifact.save(self.plotting_series2_filename)
        config.resources.update({'alpha_resources': {
            'observed_otus': self.plotting_series1_filename,
            'chao1': self.plotting_series2_filename,
        }})
        resources.update(config.resources)

    def test_percentiles_plot_with_filtering_422(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/chao1/percentiles-plot'
            '?age_cat=30s'
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_with_filtering_and_sample_422(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/chao1/percentiles-plot'
            '?age_cat=30s&sample_id=sample-2'
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_404(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/dne-metric/percentiles-plot'
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not&sample_id=sample-2'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample_dne(self):
        response = self.client.get(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not&sample_id=sample-does-not-exist'
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot_with_filtering_422_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/chao1/percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_with_filtering_and_sample_422_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/chao1/percentiles-plot'
            '?sample_id=sample-2',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_404_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/dne-metric/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                ],
            })
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "bmi_cat",
                        "field": "bmi_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "not",
                    },
                ],
            })
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample_post(self):
        response = self.client.post(
            '/results-api/plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?sample_id=sample-2',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "bmi_cat",
                        "field": "bmi_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "not",
                    },
                ],
            })
        )
        self.assertStatusCode(200, response)


class BetaIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.neighbors = pd.DataFrame([['s2', 's3', 's4'],
                                       ['s1', 's3', 's4'],
                                       ['s4', 's1', 's2'],
                                       ['s3', 's1', 's2']],
                                      columns=['k0', 'k1', 'k2'],
                                      index=['s1', 's2', 's3', 's4'])
        self.neighbors.index.name = 'sample_id'

        self.neighbors_path = self.create_tempfile(suffix='.tsv').name
        self.neighbors.to_csv(self.neighbors_path, sep='\t', index=True,
                              header=True)
        import os
        print(os.stat(self.neighbors_path))
        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__neighbors__': {
                        'awesome-metric': self.neighbors_path,
                    },
                },
            }
        }
        _update_resources_from_config(config_alt)

    def test_k_nearest(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/beta/awesome-metric'
            '/nearest?sample_id=s1'
        )
        self.assertStatusCode(200, response)
        exp = ['s2']
        obs = json.loads(response.data)
        self.assertCountEqual(exp, obs)

    def test_k_nearest_k_2(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/beta/awesome-metric'
            '/nearest?sample_id=s1&k=2'
        )
        self.assertStatusCode(200, response)
        exp = ['s2', 's3']
        obs = json.loads(response.data)
        self.assertCountEqual(exp, obs)

    def test_k_nearest_unknown_id(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/diversity/beta/awesome-metric'
            '/nearest?sample_id=a'
        )
        self.assertStatusCode(404, response)


class PlottingAltIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.plotting_metadata_path = self.create_tempfile(suffix='.txt').name
        self.plotting_metadata_table = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not', 'normal'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6'],
                               name='#SampleID')
        )

        Metadata(self.plotting_metadata_table).save(
            self.plotting_metadata_path)

        self.plotting_series1_filename = self.create_tempfile(
            suffix='.qza').name
        self.plotting_series2_filename = self.create_tempfile(
            suffix='.qza').name

        self.plotting_series_1 = pd.Series({
            'sample-2': 7.24, 'sample-4': 8.25,
            'sample-3': 6.4, },
            name='observed_otus'
        )

        self.plotting_series_2 = pd.Series({
            'sample-2': 9.01, 'sample-5': 9.04},
            name='chao1'
        )

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.plotting_series_1
        )
        imported_artifact.save(self.plotting_series1_filename)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.plotting_series_2
        )
        imported_artifact.save(self.plotting_series2_filename)
        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__metadata__': self.plotting_metadata_path,
                    '__alpha__': {
                        'observed_otus': self.plotting_series1_filename,
                        'chao1': self.plotting_series2_filename,
                    }
                },
            },
        }
        _update_resources_from_config(config_alt)

    def test_percentiles_plot_with_filtering_422(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/chao1/percentiles-plot'
            '?age_cat=30s'
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_with_filtering_and_sample_422(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/chao1/percentiles-plot'
            '?age_cat=30s&sample_id=sample-2'
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_404(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/dne-metric/percentiles-plot'
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not&sample_id=sample-2'
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample_dne(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?bmi_cat=not&sample_id=sample-does-not-exist'
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot_with_filtering_422_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/chao1/percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_with_filtering_and_sample_422_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/chao1/percentiles-plot'
            '?sample_id=sample-2',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(422, response)

    def test_percentiles_plot_404_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/dne-metric/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "age_cat",
                        "field": "age_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "30s",
                    },
                ],
            })
        )
        self.assertStatusCode(404, response)

    def test_percentiles_plot_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                ],
            })
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/plotting/'
            'diversity/alpha/observed_otus/'
            'percentiles-plot',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "bmi_cat",
                        "field": "bmi_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "not",
                    },
                ],
            })
        )
        self.assertStatusCode(200, response)

    def test_percentiles_plot_with_filtering_and_sample_post(self):
        response = self.client.post(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/alpha/observed_otus/'
            'percentiles-plot'
            '?sample_id=sample-2',
            content_type='application/json',
            data=json.dumps({
                "condition": "AND",
                "rules": [
                    {
                        "id": "bmi_cat",
                        "field": "bmi_cat",
                        "type": "string",
                        "input": "select",
                        "operator": "equal",
                        "value": "not",
                    },
                ],
            })
        )
        self.assertStatusCode(200, response)


class PCoAIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.metadata_path_pc = self.create_tempfile(suffix='.txt').name
        self.metadata_table_pc = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not',
                            'normal', 'overweight'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15, np.nan],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6',
                                'sample-7',
                                ],
                               name='#SampleID')
        )

        Metadata(self.metadata_table_pc).save(self.metadata_path_pc)

        axis_labels = ['PC1', 'PC2', 'PC3']
        self.pcoa_fh1 = self.create_tempfile(suffix='.qza')
        self.pcoa_fh2 = self.create_tempfile(suffix='.qza')
        self.pcoa_path1 = self.pcoa_fh1.name
        self.pcoa_path2 = self.pcoa_fh2.name
        self.test_pcoa_df1 = pd.DataFrame.from_dict({
            'sample-1': [0.1, 0.2, 7],
            'sample-2': [0.9, 0.2, 7],
        },
            orient='index',
            columns=axis_labels,
        )
        self.test_pcoa_df1.index.name = 'Sample ID'
        self.test_pcoa_df2 = pd.DataFrame.from_dict({
            'sample-1': [0.1, 0.2, 7],
            's2': [0.9, 0.2, 7],
            'sample-3': [0.2, -0.3, 0],
            'sample-7': [0.111, -4, 0.2],
        },
            orient='index',
            columns=axis_labels,
        )
        self.test_pcoa_df2.index.name = 'Sample ID'

        self.pcoa1 = OrdinationResults('pcoa1', 'pcoa1',
                                       eigvals=pd.Series([7, 2, 1],
                                                         index=axis_labels,
                                                         ),
                                       samples=self.test_pcoa_df1,
                                       proportion_explained=pd.Series(
                                           [0.7, 0.2, 0.1],
                                           index=axis_labels,
                                       ),
                                       )
        self.pcoa2 = OrdinationResults('pcoa2', 'pcoa2',
                                       eigvals=pd.Series([6, 3, 1],
                                                         index=axis_labels,
                                                         ),
                                       samples=self.test_pcoa_df2,
                                       proportion_explained=pd.Series(
                                           [0.6, 0.3, 0.1],
                                           index=axis_labels,
                                       ),
                                       )
        imported_artifact = Artifact.import_data(
            "PCoAResults", self.pcoa1,
        )
        imported_artifact.save(self.pcoa_path1)
        imported_artifact = Artifact.import_data(
            "PCoAResults", self.pcoa2,
        )
        imported_artifact.save(self.pcoa_path2)

        config.resources.update({
            'metadata': self.metadata_path_pc,
            'pcoa': {
                'sample_set_name': {
                    'pcoa1': self.pcoa_path1,
                    'pcoa2': self.pcoa_path2,
                 }
            }
        })
        resources.update(config.resources)

    def test_pcoa(self):
        response = self.client.get(
            '/results-api/plotting/diversity/beta/pcoa1/pcoa/sample_set_name'
            '/emperor?metadata_categories=age_cat,bmi_cat'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)

        decomp = obs['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa1.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa1.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['sample-1', 'sample-2']
                                      )

        self.assertListEqual(obs['metadata'],
                             [['30s', 'normal'], ['40s', 'not']]
                             )
        self.assertListEqual(obs['metadata_headers'],
                             ['age_cat', 'bmi_cat']
                             )

    def test_pcoa_with_nan(self):
        response = self.client.get(
            '/results-api/plotting/diversity/beta/pcoa2/pcoa/sample_set_name'
            '/emperor?metadata_categories=age_cat,num_cat&fillna=fish'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)

        decomp = obs['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa2.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa2.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['sample-1', 's2', 'sample-3',
                                       'sample-7',
                                       ]
                                      )
        self.assertListEqual(obs['metadata'],
                             [['30s', 20], ['fish', 'fish'],
                              ['50s', 7.15], ['50s', 'fish'],
                              ]
                             )
        self.assertListEqual(obs['metadata_headers'],
                             ['age_cat', 'num_cat']
                             )

    def test_pcoa_pcoa_404(self):
        response = self.client.get(
            '/results-api/plotting/diversity/beta/pcoa_dne/pcoa'
            '/sample_set_name/emperor?metadata_categories=age_cat,bmi_cat'
        )
        self.assertStatusCode(404, response)

    def test_pcoa_400(self):
        response = self.client.get(
            '/results-api/plotting/diversity/beta/pcoa_dne/pcoa'
            '/sample_set_name/emperor'
        )
        self.assertStatusCode(400, response)

    def test_pcoa_metadata_404(self):
        response = self.client.get(
            '/results-api/plotting/diversity/beta/pcoa1/pcoa'
            '/sample_set_name/emperor?metadata_categories=age_cat,dne_cat'
        )
        self.assertStatusCode(404, response)
        obs = json.loads(response.data)
        self.assertRegexpMatches(obs['text'], 'dne_cat')


class PCoAAltIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.metadata_path_pc = self.create_tempfile(suffix='.txt').name
        self.metadata_table_pc = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not',
                            'normal', 'overweight'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15, np.nan],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6',
                                'sample-7',
                                ],
                               name='#SampleID')
        )

        Metadata(self.metadata_table_pc).save(self.metadata_path_pc)

        axis_labels = ['PC1', 'PC2', 'PC3']
        self.pcoa_fh1 = self.create_tempfile(suffix='.qza')
        self.pcoa_fh2 = self.create_tempfile(suffix='.qza')
        self.pcoa_path1 = self.pcoa_fh1.name
        self.pcoa_path2 = self.pcoa_fh2.name
        self.test_pcoa_df1 = pd.DataFrame.from_dict({
            'sample-1': [0.1, 0.2, 7],
            'sample-2': [0.9, 0.2, 7],
        },
            orient='index',
            columns=axis_labels,
        )
        self.test_pcoa_df1.index.name = 'Sample ID'
        self.test_pcoa_df2 = pd.DataFrame.from_dict({
            'sample-1': [0.1, 0.2, 7],
            's2': [0.9, 0.2, 7],
            'sample-3': [0.2, -0.3, 0],
            'sample-7': [0.111, -4, 0.2],
        },
            orient='index',
            columns=axis_labels,
        )
        self.test_pcoa_df2.index.name = 'Sample ID'

        self.pcoa1 = OrdinationResults('pcoa1', 'pcoa1',
                                       eigvals=pd.Series([7, 2, 1],
                                                         index=axis_labels,
                                                         ),
                                       samples=self.test_pcoa_df1,
                                       proportion_explained=pd.Series(
                                           [0.7, 0.2, 0.1],
                                           index=axis_labels,
                                       ),
                                       )
        self.pcoa2 = OrdinationResults('pcoa2', 'pcoa2',
                                       eigvals=pd.Series([6, 3, 1],
                                                         index=axis_labels,
                                                         ),
                                       samples=self.test_pcoa_df2,
                                       proportion_explained=pd.Series(
                                           [0.6, 0.3, 0.1],
                                           index=axis_labels,
                                       ),
                                       )
        imported_artifact = Artifact.import_data(
            "PCoAResults", self.pcoa1,
        )
        imported_artifact.save(self.pcoa_path1)
        imported_artifact = Artifact.import_data(
            "PCoAResults", self.pcoa2,
        )
        imported_artifact.save(self.pcoa_path2)

        config_alt = {
            'datasets': {
                '16SAmplicon': {
                    '__metadata__': self.metadata_path_pc,
                    '__pcoa__': {
                        'sample_set_name': {
                            'pcoa1': self.pcoa_path1,
                            'pcoa2': self.pcoa_path2,
                        }
                    }
                },
            },
        }
        _update_resources_from_config(config_alt)

    def test_pcoa(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/beta/pcoa1/pcoa/sample_set_name'
            '/emperor?metadata_categories=age_cat,bmi_cat'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)

        decomp = obs['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa1.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa1.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['sample-1', 'sample-2']
                                      )

        self.assertListEqual(obs['metadata'],
                             [['30s', 'normal'], ['40s', 'not']]
                             )
        self.assertListEqual(obs['metadata_headers'],
                             ['age_cat', 'bmi_cat']
                             )

    def test_pcoa_with_nan(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/beta/pcoa2/pcoa/sample_set_name'
            '/emperor?metadata_categories=age_cat,num_cat&fillna=fish'
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)

        decomp = obs['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa2.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa2.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['sample-1', 's2', 'sample-3',
                                       'sample-7',
                                       ]
                                      )
        self.assertListEqual(obs['metadata'],
                             [['30s', 20], ['fish', 'fish'],
                              ['50s', 7.15], ['50s', 'fish'],
                              ]
                             )
        self.assertListEqual(obs['metadata_headers'],
                             ['age_cat', 'num_cat']
                             )

    def test_pcoa_pcoa_404(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/beta/pcoa_dne/pcoa'
            '/sample_set_name/emperor?metadata_categories=age_cat,bmi_cat'
        )
        self.assertStatusCode(404, response)

    def test_pcoa_400(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/beta/pcoa_dne/pcoa'
            '/sample_set_name/emperor'
        )
        self.assertStatusCode(400, response)

    def test_pcoa_metadata_404(self):
        response = self.client.get(
            '/results-api/dataset/16SAmplicon/'
            'plotting/diversity/beta/pcoa1/pcoa'
            '/sample_set_name/emperor?metadata_categories=age_cat,dne_cat'
        )
        self.assertStatusCode(404, response)
        obs = json.loads(response.data)
        self.assertRegexpMatches(obs['text'], 'dne_cat')


class AllIntegrationTest(
        AlphaIntegrationTests,
        TaxonomyIntegrationTests,
        MetadataIntegrationTests,
        PCoAIntegrationTests,
        ):

    def test_available_datasets(self):
        response = self.client.get('/results-api/available/dataset')
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['16SAmplicon'],
                              obs
                              )

    def test_metadata_filter_on_taxonomy(self):
        response = self.client.get('/results-api/metadata/sample_ids?'
                                   'taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-1', 'sample-2', 'sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/results-api/metadata/sample_ids?taxonomy=table2&age_cat=50s')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_age_cat(self):
        response = self.client.get(
            '/results-api/metadata/sample_ids?alpha_metric=observed_otus&'
            'age_cat=50s')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/results-api/metadata/sample_ids?alpha_metric=observed_otus&'
            'age_cat=50s'
            '&taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat_empty(self):
        response = self.client.get(
            '/results-api/metadata/sample_ids?alpha_metric=observed_otus&'
            'age_cat=30s'
            '&taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual([],
                              obs['sample_ids'])

    def test_alpha_group_metadata_integration(self):
        # TODO change this to alpha query
        generic_metadata_query = {
                    "condition": "AND",
                    "rules": [
                        {
                            "id": "bmi_cat",
                            "field": "bmi_cat",
                            "type": "string",
                            "input": "select",
                            "operator": "equal",
                            "value": "not",
                        },
                    ],
                }

        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/group/shannon'
            '?return_raw=True',
            content_type='application/json',
            data=json.dumps({
                "metadata_query": generic_metadata_query,
            })
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(obs['alpha_diversity'].keys(),
                              ['sample-2', 'sample-3', 'sample-5'])

    def test_alpha_group_metadata_integration_with_sample_ids_OR(self):
        generic_metadata_query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "bmi_cat",
                    "field": "bmi_cat",
                    "type": "string",
                    "input": "select",
                    "operator": "equal",
                    "value": "not",
                },
            ],
        }

        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/group/shannon'
            '?return_raw=True',
            content_type='application/json',
            data=json.dumps({
                "metadata_query": generic_metadata_query,
                "sample_ids": ['sample-1'],
                "condition": "OR",
            })
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(obs['alpha_diversity'].keys(),
                              ['sample-1', 'sample-2', 'sample-3', 'sample-5'])

    def test_alpha_group_metadata_integration_with_sample_ids_AND(self):
        generic_metadata_query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "bmi_cat",
                    "field": "bmi_cat",
                    "type": "string",
                    "input": "select",
                    "operator": "equal",
                    "value": "not",
                },
            ],
        }

        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/group/shannon'
            '?return_raw=True',
            content_type='application/json',
            data=json.dumps({
                "metadata_query": generic_metadata_query,
                "sample_ids": ['sample-2', 'sample-3', 'sample-unique-name'],
                "condition": "AND",
            })
        )
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(obs['alpha_diversity'].keys(),
                              ['sample-2', 'sample-3'])

    def test_alpha_group_metadata_integration_with_sample_ids_400(self):
        generic_metadata_query = {
            "condition": "AND",
            "rules": [
                {
                    "id": "bmi_cat",
                    "field": "bmi_cat",
                    "type": "string",
                    "input": "select",
                    "operator": "equal",
                    "value": "not",
                },
            ],
        }

        response = self.client.post(
            '/results-api/dataset/16SAmplicon/diversity/alpha/group/shannon'
            '?return_raw=True',
            content_type='application/json',
            data=json.dumps({
                "metadata_query": generic_metadata_query,
                "sample_ids": ['sample-1'],
            })
        )
        self.assertStatusCode(400, response)
