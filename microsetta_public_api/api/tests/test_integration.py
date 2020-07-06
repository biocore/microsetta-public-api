import json
import numpy as np
import pandas as pd
import biom
from biom.util import biom_open
from qiime2 import Artifact, Metadata
from numpy.testing import assert_allclose

from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import FlaskTests, \
    TempfileTestCase, ConfigTestCase
from microsetta_public_api.utils import create_data_entry, DataTable


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

        config.resources.update({'metadata': self.metadata_path})
        resources.update(config.resources)

    def test_metadata_category_values_returns_string_array(self):
        exp = ['30s', '40s', '50s']
        response = self.client.get(
            "/api/metadata/category/values/age_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_category_values_returns_numeric_array(self):
        exp = [20, 30, 7.15, 8.25]
        response = self.client.get(
            "/api/metadata/category/values/num_cat")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertListEqual(exp, obs)

    def test_metadata_category_values_returns_404(self):
        _, self.client = self.build_app_test_client()
        response = self.client.get(
            "/api/metadata/category/values/non-existing-cat")
        self.assertStatusCode(404, response)

    def test_metadata_sample_ids_returns_simple(self):
        exp_ids = ['sample-1', 'sample-4']
        response = self.client.get(
            "/api/metadata/sample_ids?age_cat=30s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_returns_empty(self):
        response = self.client.get(
            "/api/metadata/sample_ids?age_cat=20s&bmi_cat=normal")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertEqual(obs['sample_ids'], [])

    def test_metadata_sample_ids_extra_categories_have_no_effect(self):
        exp_ids = ['sample-1', 'sample-4']
        # num_cat is not configured to be able to be queried on, so this
        #  tests to make sure it is ignored
        response = self.client.get(
            "/api/metadata/sample_ids?age_cat=30s&bmi_cat=normal&num_cat=30")
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_age_cat_only(self):
        response = self.client.get(
            "/api/metadata/sample_ids?age_cat=30s")
        exp_ids = ['sample-1', 'sample-4', 'sample-5']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_bmi_only(self):
        response = self.client.get(
            "/api/metadata/sample_ids?bmi_cat=normal")
        exp_ids = ['sample-1', 'sample-4', 'sample-6']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_sample_ids_get_null_parameters_succeeds(self):
        response = self.client.get(
            "/api/metadata/sample_ids")
        exp_ids = ['sample-1', 'sample-2', 'sample-3', 'sample-4',
                   'sample-5', 'sample-6', 'sample-7']
        self.assertStatusCode(200, response)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample_ids'], obs.keys())
        self.assertCountEqual(obs['sample_ids'], exp_ids)

    def test_metadata_filter_on_metric_dne(self):
        response = self.client.get(
            # careful not to use a metric that exists in AlphaIntegrationTests
            '/api/metadata/sample_ids?alpha_metric=bad-metric')
        self.assertEqual(response.status_code, 404)

    def test_metadata_filter_on_taxonomy_dne(self):
        response = self.client.get(
            # careful not to use a table that exists in
            #  TaxonomyIntegrationTests
            '/api/metadata/sample_ids?alpha_metric=bad-table')
        self.assertEqual(response.status_code, 404)

    def test_metadata_filter_on_metric_and_taxonomy_dne(self):
        response = self.client.get(
            # careful not to use a metric that exists in AlphaIntegrationTests
            # careful not to use a table that exists in
            #  TaxonomyIntegrationTests
            '/api/metadata/sample_ids?alpha_metric=bad-metric&taxonomy=bad'
            '-table')
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
            [['feature-1', 'k__a; p__b; o__c', 0.123],
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
            '/api/taxonomy/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('resources', obs)
        self.assertCountEqual(['table2', 'table-fish', 'table-cached-model',
                               'table2-greengenes'],
                              obs['resources'])

    def test_summarize_group(self):
        response = self.client.post('/api/taxonomy/group/table2',
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
        response = self.client.post('/api/taxonomy/group/table-cached-model',
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
            '/api/taxonomy/single/table2/sample-1',
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
        response = self.client.post('/api/taxonomy/present/group/'
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
            '/api/taxonomy/present/single/table2/sample-1'
        )

        self.assertEqual(response.status_code, 200)


class AlphaIntegrationTests(IntegrationTests):

    def setUp(self):
        super().setUp()
        self.series1_filename = self.create_tempfile(suffix='.qza').name
        self.series2_filename = self.create_tempfile(suffix='.qza').name

        self.series_1 = pd.Series({
            'sample-foo-bar': 7.24, 'sample-baz-qux': 8.25,
            'sample-3': 6.4, },
            name='observed_otus'
        )

        self.series_2 = pd.Series({
            'sample-foo-bar': 9.01, 'sample-qux-quux': 9.04},
            name='chao1'
        )

        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.series_1
        )
        imported_artifact.save(self.series1_filename)
        imported_artifact = Artifact.import_data(
            "SampleData[AlphaDiversity]", self.series_2
        )
        imported_artifact.save(self.series2_filename)
        config.resources.update({'alpha_resources': {
            'observed_otus': self.series1_filename,
            'chao1': self.series2_filename,
        }})
        resources.update(config.resources)

    def test_resources_available(self):
        response = self.client.get('/api/diversity/alpha/metrics/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('alpha_metrics', obs)
        self.assertCountEqual(['observed_otus', 'chao1'], obs['alpha_metrics'])

    def test_group_summary(self):
        response = self.client.post(
            '/api/diversity/alpha/group/observed_otus'
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


class AllIntegrationTest(
        AlphaIntegrationTests,
        TaxonomyIntegrationTests,
        MetadataIntegrationTests,
        ):

    def test_metadata_filter_on_taxonomy(self):
        response = self.client.get('/api/metadata/sample_ids?taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-1', 'sample-2', 'sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample_ids?taxonomy=table2&age_cat=50s')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample_ids?alpha_metric=observed_otus&age_cat=50s')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample_ids?alpha_metric=observed_otus&age_cat=50s'
            '&taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat_empty(self):
        response = self.client.get(
            '/api/metadata/sample_ids?alpha_metric=observed_otus&age_cat=30s'
            '&taxonomy=table2')
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual([],
                              obs['sample_ids'])
