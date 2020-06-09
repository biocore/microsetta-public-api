import unittest
import pandas as pd
import pandas.testing as pdt
import biom
import numpy as np
import numpy.testing as npt

from qiime2 import Artifact
from microsetta_public_api.models._taxonomy import GroupTaxonomy, Taxonomy
from microsetta_public_api.exceptions import DisjointError, UnknownID


class TaxonomyTests(unittest.TestCase):
    def setUp(self):
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
        self.table_ranks = self.table.rankdata(inplace=False)

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
        self.table2_ranks = self.table2.rankdata(inplace=False)

        # variances
        self.table_vars = biom.Table(np.array([[0, 1, 2],
                                               [2, 4, 6],
                                               [3, 0, 1]]),
                                     ['feature-1', 'feature-2', 'feature-3'],
                                     ['sample-1', 'sample-2', 'sample-3'])
        self.no_variances = biom.Table(np.zeros((3, 3)),
                                       ['feature-1', 'feature-2', 'feature-3'],
                                       ['sample-1', 'sample-2', 'sample-3'])

    def test_qza_integration(self):
        table_qza = Artifact.import_data(
            "FeatureTable[Frequency]", self.table
        )
        taxonomy_qza = Artifact.import_data(
            "FeatureData[Taxonomy]", self.taxonomy_df,
        )
        table = table_qza.view(biom.Table)
        taxonomy_df = taxonomy_qza.view(pd.DataFrame)
        taxonomy = Taxonomy(table, taxonomy_df)
        taxonomy.get_group(['sample-1', 'sample-2'], 'foo')

    def test_get_sample_ids(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        npt.assert_equal(taxonomy._get_sample_ids(), ['sample-1', 'sample-2',
                                                      'sample-3'])

    def test_get_feature_ids(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        npt.assert_equal(taxonomy._get_feature_ids(), ['feature-1',
                                                       'feature-2',
                                                       'feature-3'])

    def test_init_no_variances(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        self.assertEqual(taxonomy._table, self.table.copy().norm())
        self.assertEqual(taxonomy._variances, self.no_variances)
        pdt.assert_frame_equal(taxonomy._features, self.taxonomy_df)

    def test_init_variances(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, self.table_vars)
        self.assertEqual(taxonomy._table, self.table.copy().norm())
        self.assertEqual(taxonomy._variances, self.table_vars)
        pdt.assert_frame_equal(taxonomy._features, self.taxonomy_df)
        self.assertEqual(list(taxonomy._table.ids(axis='observation')),
                         list(taxonomy._features.index))
        self.assertEqual(list(taxonomy._table.ids(axis='observation')),
                         list(taxonomy._variances.ids(axis='observation')))

    def test_init_disjoint(self):
        with self.assertRaisesRegex(DisjointError,
                                    "Table and features are disjoint"):
            Taxonomy(self.table, self.taxonomy2_df)
        with self.assertRaisesRegex(DisjointError,
                                    "Table and features are disjoint"):
            Taxonomy(self.table2, self.taxonomy_df)

    def test_init_disjoint_variances(self):
        bad = self.table_vars.copy()
        bad.update_ids({'sample-1': 'sample-bad'}, inplace=True, strict=False)

        with self.assertRaisesRegex(DisjointError,
                                    "Table and variances are disjoint"):
            Taxonomy(self.table, self.taxonomy_df, bad)

    def test_get_group(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        exp = GroupTaxonomy(name='sample-2',
                            taxonomy='((((feature-1,((feature-2)e)d)c)b)a);',
                            features=['feature-1', 'feature-2'],
                            feature_values=[1. / 5, 4. / 5],
                            feature_variances=[0.0, 0.0],
                            feature_ranks=None)
        obs = taxonomy.get_group(['sample-2'])
        self.assertEqual(obs, exp)

    def test_get_group_multiple(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        exp = GroupTaxonomy(name='foo',
                            taxonomy='((((feature-1,((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',  # noqa
                            features=['feature-1', 'feature-2', 'feature-3'],
                            feature_values=[1. / 10, 6. / 10, 3. / 10],
                            feature_variances=[0.0, 0.0, 0.0],
                            feature_ranks=None)
        obs = taxonomy.get_group(['sample-1', 'sample-2'], 'foo')
        self.assertEqual(obs.name, exp.name)
        self.assertEqual(obs.taxonomy, exp.taxonomy)
        self.assertEqual(obs.features, exp.features)
        npt.assert_almost_equal(obs.feature_values, exp.feature_values)
        self.assertEqual(obs.feature_variances, exp.feature_variances)

    def test_get_group_with_variances(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, self.table_vars)
        exp = GroupTaxonomy(name='sample-1',
                            taxonomy='((((((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',  # noqa
                            features=['feature-2', 'feature-3'],
                            feature_values=[2. / 5, 3. / 5],
                            feature_variances=[2.0, 3.0],
                            feature_ranks=None,)
        obs = taxonomy.get_group(['sample-1'])
        self.assertEqual(obs, exp)

    def test_get_group_missing(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        with self.assertRaisesRegex(UnknownID, "sample-X does not exist"):
            taxonomy.get_group(['sample-X'])

    # def test_get_group_raw(self):
    #     # dont do the taxonomy voodoo
    #     # possibly provide a 2d representation
    #     self.fail()
    #
    # def test_do_annotations(self):
    #     self.fail("its only harder later")


class GroupTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.tstr = '(((((feature-2)e)d,feature-1)c)b)a;'
        self.obj = GroupTaxonomy(name='sample-2',
                                 taxonomy=self.tstr,
                                 features=['feature-1', 'feature-2'],
                                 feature_values=[1. / 5, 4. / 5],
                                 feature_variances=[0.0, 0.0],
                                 feature_ranks=[1.0, 2.0])

    def test_init(self):
        self.assertEqual(self.obj.name, 'sample-2')
        self.assertEqual(self.obj.taxonomy, self.tstr)
        self.assertEqual(self.obj.features, ['feature-1', 'feature-2'])
        self.assertEqual(self.obj.feature_values, [1. / 5, 4. / 5])
        self.assertEqual(self.obj.feature_variances, [0.0, 0.0])
        self.assertEqual(self.obj.feature_ranks, [1.0, 2.0])

    def test_init_tree_missing_feature(self):
        with self.assertRaisesRegex(UnknownID,
                                    "is not in the taxonomy."):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr,
                          features=['feature-1', 'feature-3'],
                          feature_values=[1. / 5, 4. / 5],
                          feature_variances=[0.0, 0.0],
                          feature_ranks=[1.0, 2.0])

    def test_init_feature_value_lengths(self):
        with self.assertRaisesRegex(ValueError,
                                    "length mismatch"):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr + 'feature-3',
                          features=['feature-1', 'feature-2', 'feature-3'],
                          feature_values=[1. / 5, 4. / 5],
                          feature_variances=[0.0, 0.0],
                          feature_ranks=[1.0, 2.0])

        with self.assertRaisesRegex(ValueError,
                                    "length mismatch"):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr,
                          features=['feature-1', 'feature-2'],
                          feature_values=[1. / 5, ],
                          feature_variances=[0.0, 0.0],
                          feature_ranks=[1.0, 2.0])

    def test_to_dict(self):
        exp = {'name': 'sample-2',
               'taxonomy': self.tstr,
               'features': ['feature-1', 'feature-2'],
               'feature_values': [1. / 5, 4. / 5],
               'feature_variances': [0.0, 0.0],
               'feature_ranks': [1.0, 2.0]}
        obs = self.obj.to_dict()
        self.assertEqual(obs, exp)

    def test_str(self):
        exp = str(self.obj.to_dict())
        obs = str(self.obj)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    unittest.main()
