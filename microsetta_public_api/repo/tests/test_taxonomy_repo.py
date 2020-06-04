from unittest import TestCase
from unittest.mock import patch, PropertyMock
import pandas as pd
import numpy as np
import biom
from biom.util import biom_open
from qiime2 import Artifact
from pandas.testing import assert_frame_equal

from microsetta_public_api import config
from microsetta_public_api.resources import resources
from microsetta_public_api.utils.testing import TempfileTestCase
from microsetta_public_api.repo._taxonomy_repo import TaxonomyRepo


class TestTaxonomyRepoHelpers(TestCase):

    def test_get_resource_table_not_available(self):
        taxonomy_repo = TaxonomyRepo()
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo'
                   '.tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {'foo': {'table': 'some-tb'},
                                        'bar': {'table': 'some-other-tb'}}
            with self.assertRaisesRegex(ValueError, 'No table with taxonomy '
                                                    'available for '
                                                    '`bad-table`'):
                taxonomy_repo._get_resource('bad-table')

    def test_get_resource_component(self):
        taxonomy_repo = TaxonomyRepo()
        with patch('microsetta_public_api.repo._taxonomy_repo.TaxonomyRepo'
                   '.tables', new_callable=PropertyMock) as mock_tables:
            mock_tables.return_value = {'foo': {'table': 'some-tb',
                                                'variances': 'var-tb'},
                                        'bar': {'table': 'some-other-tb'}}

            res = taxonomy_repo._get_resource('bar')
        self.assertDictEqual({'table': 'some-other-tb'}, res)


class TestTaxonomyRepoWithResources(TempfileTestCase):

    def setUp(self):
        self._config_copy = config.resources.copy()
        self._resources_copy = resources.copy()
        self.no_resources_repo = TaxonomyRepo()
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
            'table3': {
                'table': self.table3_filename,
                'feature-data-taxonomy': self.taxonomy2_filename,
                'variances': self.table3_filename,
            },
            'table4': {
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
        self.repo = TaxonomyRepo()

    def tearDown(self):
        config.resources = self._config_copy
        resources.clear()
        resources.update(self._resources_copy)
        super().tearDown()

    def test_available_taxonomy_tables(self):
        exp = ['table2', 'table3', 'table4']
        obs = self.repo.resources()
        self.assertCountEqual(exp, obs)

    def test_available_taxonomy_tables_empty_repo(self):
        exp = []
        obs = self.no_resources_repo.resources()
        self.assertCountEqual(exp, obs)

    def test_get_table(self):
        exp = self.table
        obs = self.repo.table('table2')
        self.assertEqual(exp, obs)

    def test_get_table_invalid(self):
        with self.assertRaises(ValueError):
            self.repo.table('table1')

    def test_get_taxonomy(self):
        exp = self.taxonomy_df
        obs = self.repo.feature_data_taxonomy('table4')
        obs['Confidence'] = obs['Confidence'].astype('float64')
        assert_frame_equal(exp, obs)

    def test_get_taxonomy_invalid(self):
        with self.assertRaises(ValueError):
            self.repo.table('foo')

    def test_get_variances(self):
        exp = self.table3
        obs = self.repo.variances('table3')
        self.assertEqual(exp, obs)

    def test_get_variances_none(self):
        exp = None
        obs = self.repo.variances('table4')
        self.assertIs(exp, obs)

    def test_get_variances_invalid(self):
        with self.assertRaises(ValueError):
            self.repo.table('table6')

    def test_exists(self):
        exp = [False, True, True]
        obs = self.repo.exists(['sample-1', 'sample-2', 'sample-3'], 'table3')
        self.assertListEqual(exp, obs)

    def test_exists_single(self):
        obs = self.repo.exists('sample-1', 'table2')
        self.assertTrue(obs)
