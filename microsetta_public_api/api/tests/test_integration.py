import json
import numpy as np
import pandas as pd
import biom
from biom.util import biom_open
from qiime2 import Artifact, Metadata

from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import FlaskTests, \
    TempfileTestCase, ConfigTestCase


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
                'age_cat': ['30s', '40s', '50s', '30s', '30s', '50s'],
                'bmi_cat': ['normal', 'not', 'not', 'normal', 'not', 'normal'],
                'num_cat': [20, 30, 7.15, 8.25, 30, 7.15],
            }, index=pd.Series(['sample-1', 'sample-2', 'sample-3',
                                'sample-4', 'sample-5', 'sample-6'],
                               name='#SampleID')
        )

        Metadata(self.metadata_table).save(self.metadata_path)

        config.resources.update({'metadata': self.metadata_path})
        resources.update(config.resources)


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
        config.resources.update({'table_resources': {
            'table1': {
                'table': self.table1_filename,
            },
            'table2': {
                'table': self.table1_filename,
                'feature-data-taxonomy': self.taxonomy1_filename,
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
        }})
        resources.update(config.resources)

    def test_resources(self):
        response = self.client.get(
            '/api/taxonomy/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('resources', obs)
        self.assertCountEqual(['table2', 'table-fish'], obs['resources'])

    def test_summarize_group(self):
        response = self.client.post('/api/taxonomy/summarize_group/table2',
                                    content_type='application/json',
                                    data=json.dumps({'sample_ids': [
                                        'sample-1']}))

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['taxonomy', 'features',
                               'feature_values', 'feature_variances'],
                              obs.keys())


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
        response = self.client.get('/api/diversity/metrics/alpha/available')

        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertIn('alpha_metrics', obs)
        self.assertCountEqual(['observed_otus', 'chao1'], obs['alpha_metrics'])

    def test_group_summary(self):
        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
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
        response = self.client.get('/api/metadata/sample-ids?taxonomy=table2')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-1', 'sample-2', 'sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample-ids?taxonomy=table2&age_cat=50s')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample-ids?alpha_metric=observed_otus&age_cat=50s')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat(self):
        response = self.client.get(
            '/api/metadata/sample-ids?alpha_metric=observed_otus&age_cat=50s'
            '&taxonomy=table2')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual(['sample-3'],
                              obs['sample_ids'])

    def test_metadata_filter_on_alpha_and_and_taxonomy_and_age_cat_empty(self):
        response = self.client.get(
            '/api/metadata/sample-ids?alpha_metric=observed_otus&age_cat=30s'
            '&taxonomy=table2')
        print(response.data)
        self.assertEqual(response.status_code, 200)
        obs = json.loads(response.data)
        self.assertCountEqual([],
                              obs['sample_ids'])
