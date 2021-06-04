import unittest
import pandas as pd
import pandas.testing as pdt
import biom
import numpy as np
import numpy.testing as npt

from qiime2 import Artifact
from microsetta_public_api.models._taxonomy import (
    GroupTaxonomy, Taxonomy, get_lineage_max_level,
    create_tree_node_from_lineages,
)

from microsetta_public_api.exceptions import (DisjointError, UnknownID,
                                              SubsetError)
from microsetta_public_api.utils import DataTable, create_data_entry


class UtilityTests(unittest.TestCase):

    def test_get_lineage_max_level(self):
        lineages = [
            'k__a;  p__b;  c__d',
            'k__a;  p__b;  c__c;  o__d;  f__e',
            'k__a;  p__b;  c__c;  o__',
            'k__a;  p__f;  c__g;  o__h',
        ]
        formatted_lineages = get_lineage_max_level(lineages, 4)
        exp = [('k__a', 'p__b', 'c__d'),
               ('k__a', 'p__b', 'c__c'),
               ('k__a', 'p__b', 'c__c', 'o__d'),
               ('k__a', 'p__f', 'c__g', 'o__h'),
               ]
        self.assertCountEqual(exp, formatted_lineages)

    def test_create_tree_from_lineages(self):
        lineages = [
            ('k__a', 'p__b', 'c__d'),
            ('k__a', 'p__b', 'c__c'),
            ('k__a', 'p__b', 'c__c', 'o__d'),
            ('k__a', 'p__f', 'c__g', 'o__h'),
            ]
        expected_tip_names = ['k__a; p__b; c__d', 'k__a; p__b; c__c; o__d',
                              'k__a; p__f; c__g; o__h']
        observed_tree = create_tree_node_from_lineages(lineages)
        observed_tip_names = [tip.name for tip in observed_tree.tips()]
        self.assertCountEqual(observed_tip_names, expected_tip_names)
        t_array = observed_tree.to_array()
        expected_names = ['k__a',
                          'k__a; p__b',
                          'k__a; p__f',
                          'k__a; p__b; c__c',
                          'k__a; p__b; c__d',
                          'k__a; p__f; c__g',
                          'k__a; p__b; c__c; o__d',
                          'k__a; p__f; c__g; o__h',
                          None
                          ]
        observed_names = t_array['name']
        self.assertCountEqual(expected_names, observed_names)


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
        self.collapse_table = biom.Table(
            np.array(
                [[0, 1, 2],
                 [2, 4, 6],
                 [3, 0, 1],
                 [2, 0, 0],
                 ]
            ),
            ['feature-1', 'feature-2', 'feature-3', 'feature-4'],
            ['sample-1', 'sample-2', 'sample-3']
        )
        self.collapse_taxonomy_df = pd.DataFrame(
            [['feature-1', 'a; b; c', 0.123],
             ['feature-2', 'a; b; c; d; e', 0.345],
             ['feature-3', 'a; f; g; h', 0.478],
             ['feature-4', 'a', 0.200],
             ],
            columns=['Feature ID', 'Taxon', 'Confidence']
        )
        self.collapse_taxonomy_df.set_index('Feature ID', inplace=True)

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

        self.taxonomy_superset_df = self.taxonomy2_df.copy()
        self.taxonomy_superset_df.loc['feature-2'] = \
            self.taxonomy_df.loc['feature-2']

        self.taxonomy_greengenes_df = pd.DataFrame(
            [['feature-1', 'k__a;  p__b;  o__c', 0.123],
             ['feature-2', 'k__a;  p__b;  o__c;  f__d;  g__e', 0.34],
             ['feature-3', 'k__a;  p__f;  o__g;  f__h', 0.678]],
            columns=['Feature ID', 'Taxon', 'Confidence'])
        self.taxonomy_greengenes_df.set_index('Feature ID', inplace=True)
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
        npt.assert_array_almost_equal(
            taxonomy._table.matrix_data.todense(),
            self.table.copy().norm().matrix_data.todense())
        npt.assert_array_almost_equal(
            taxonomy._variances.matrix_data.todense(),
            self.no_variances.matrix_data.todense(),
        )
        pdt.assert_frame_equal(taxonomy._features, self.taxonomy_df)

    def test_init_variances(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, self.table_vars)
        npt.assert_array_almost_equal(
            taxonomy._table.matrix_data.todense(),
            self.table.copy().norm().matrix_data.todense())
        npt.assert_array_almost_equal(
            taxonomy._variances.matrix_data.todense(),
            self.table_vars.matrix_data.todense(),
        )
        pdt.assert_frame_equal(taxonomy._features, self.taxonomy_df)
        self.assertEqual(list(taxonomy._table.ids(axis='observation')),
                         list(taxonomy._features.index))
        self.assertEqual(list(taxonomy._table.ids(axis='observation')),
                         list(taxonomy._variances.ids(axis='observation')))

    def test_init_disjoint(self):
        with self.assertRaisesRegex(SubsetError,
                                    "not a subset"):
            Taxonomy(self.table, self.taxonomy2_df)
        with self.assertRaisesRegex(SubsetError,
                                    "not a subset"):
            Taxonomy(self.table2, self.taxonomy_df)

    def test_init_allow_taxonomy_superset(self):
        Taxonomy(self.table, self.taxonomy_superset_df)

    def test_init_disjoint_variances(self):
        bad = self.table_vars.copy()
        bad.update_ids({'sample-1': 'sample-bad'}, inplace=True, strict=False)

        with self.assertRaisesRegex(DisjointError,
                                    "Table and variances are disjoint"):
            Taxonomy(self.table, self.taxonomy_df, bad)

    def _clean_sort_df(self, df, cols):
        df.sort_values(cols, inplace=True)
        df.reset_index(drop=True, inplace=True)

    def test_init_rankdata(self):
        exp = pd.DataFrame([['c', 'sample-1', 1.],
                            ['c', 'sample-2', 1],
                            ['c', 'sample-3', 2],
                            ['g', 'sample-1', 2],
                            ['g', 'sample-3', 1]],
                           columns=['Taxon', 'Sample ID', 'Rank'])

        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)

        obs = taxonomy._ranked
        self._clean_sort_df(obs, ['Taxon', 'Sample ID'])
        self._clean_sort_df(exp, ['Taxon', 'Sample ID'])
        pdt.assert_frame_equal(obs, exp, check_like=True)

    def test_init_rankdata_order(self):
        exp = ['c', 'g']
        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)
        obs = list(taxonomy._ranked_order.index)
        self.assertEqual(obs, exp)

    def test_create_collapsed_table(self):
        taxonomy = Taxonomy(self.collapse_table, self.collapse_taxonomy_df,
                            collapse_level=3)
        obs_ids = taxonomy._collapsed_table.ids('observation')
        exp_ids = ['a; b; c', 'a; f; g', 'a']
        self.assertCountEqual(obs_ids, exp_ids)

        expected_feature_metadata = pd.DataFrame(
            [[True], [False], [False]],
            index=['a; b; c', 'a; f; g', 'a'],
            columns=['in_sample']
        )

        feature_metadata = taxonomy.get_collapsed_table_data('sample-2')
        pdt.assert_frame_equal(expected_feature_metadata, feature_metadata)

    def test_ranks_sample(self):
        exp = pd.DataFrame([['c', 'sample-1', 1.],
                            ['c', 'sample-2', 1],
                            ['c', 'sample-3', 2],
                            ['g', 'sample-1', 2],
                            ['g', 'sample-3', 1]],
                           columns=['Taxon', 'Sample ID', 'Rank'])
        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)
        obs = taxonomy.ranks_sample(5)
        self._clean_sort_df(obs, ['Taxon', 'Sample ID'])
        self._clean_sort_df(exp, ['Taxon', 'Sample ID'])
        pdt.assert_frame_equal(obs, exp, check_like=True)

        obs = taxonomy.ranks_sample(4)
        self.assertIn(sorted(obs['Taxon'].values), [['c', 'c', 'c', 'g'],
                                                    ['c', 'c', 'g', 'g']])

        obs = taxonomy.ranks_sample(100)
        self.assertEqual(sorted(obs['Taxon'].values),
                         ['c', 'c', 'c', 'g', 'g'])

    def test_ranks_specific(self):
        exp_1 = pd.DataFrame([['c', 'sample-1', 1.],
                              ['g', 'sample-1', 2]],
                             columns=['Taxon', 'Sample ID', 'Rank'])
        exp_2 = pd.DataFrame([['c', 'sample-2', 1.]],
                             columns=['Taxon', 'Sample ID', 'Rank'])
        exp_3 = pd.DataFrame([['c', 'sample-3', 2.],
                              ['g', 'sample-3', 1]],
                             columns=['Taxon', 'Sample ID', 'Rank'])

        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)

        obs_1 = taxonomy.ranks_specific('sample-1')
        obs_2 = taxonomy.ranks_specific('sample-2')
        obs_3 = taxonomy.ranks_specific('sample-3')

        self._clean_sort_df(obs_1, ['Taxon', 'Sample ID'])
        self._clean_sort_df(obs_2, ['Taxon', 'Sample ID'])
        self._clean_sort_df(obs_3, ['Taxon', 'Sample ID'])

        self._clean_sort_df(exp_1, ['Taxon', 'Sample ID'])
        self._clean_sort_df(exp_2, ['Taxon', 'Sample ID'])
        self._clean_sort_df(exp_3, ['Taxon', 'Sample ID'])

        pdt.assert_frame_equal(obs_1, exp_1, check_like=True)
        pdt.assert_frame_equal(obs_2, exp_2, check_like=True)
        pdt.assert_frame_equal(obs_3, exp_3, check_like=True)

    def test_ranks_specific_missing_id(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)
        with self.assertRaisesRegex(UnknownID, 'foobar'):
            taxonomy.ranks_specific('foobar')

    def test_ranks_order(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)

        exp = ['c', 'g']
        obs = taxonomy.ranks_order()
        self.assertEqual(obs, exp)

        exp = ['c', 'g']
        obs = taxonomy.ranks_order(['g', 'c'])
        self.assertEqual(obs, exp)

        exp = ['c']
        obs = taxonomy.ranks_order(['c', ])
        self.assertEqual(obs, exp)

    def test_ranks_order_unknown(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df, rank_level=2)
        with self.assertRaisesRegex(UnknownID, "foobar"):
            taxonomy.ranks_order(["foobar", ])

        with self.assertRaisesRegex(UnknownID, "foobar"):
            taxonomy.ranks_order(["c", "foobar", ])

    def test_index_taxa_prevalence(self):
        table = biom.Table(np.array([[0, 1, 2, 0],
                                     [2, 4, 6, 1],
                                     [3, 0, 0, 0]]),
                           ['feature-1', 'feature-2', 'feature-3'],
                           ['sample-1', 'sample-2', 'sample-3', 'sample-4'])
        taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                    ['feature-2', 'a; b; c; d; e', 0.345],
                                    ['feature-3', 'a; f; g; h', 0.678]],
                                   columns=['Feature ID', 'Taxon',
                                            'Confidence'])
        taxonomy_df.set_index('Feature ID', inplace=True)
        tax = Taxonomy(table, taxonomy_df)

        exp_unique = pd.Series([False, False, True],
                               index=['feature-1', 'feature-2', 'feature-3'])
        exp_prev = pd.Series([0.5, 1., 0.25],
                             index=['feature-1', 'feature-2', 'feature-3'])
        pdt.assert_series_equal(exp_unique, tax.feature_uniques)
        pdt.assert_series_equal(exp_prev, tax.feature_prevalence)

    def test_rare_unique(self):
        # feature 1 is "rare" for samples 2 and 3 at a theshold of <= 50%
        # feature 3 is "unique" to sample 1
        table = biom.Table(np.array([[0, 1, 2, 0],
                                     [2, 4, 6, 1],
                                     [3, 0, 0, 0]]),
                           ['feature-1', 'feature-2', 'feature-3'],
                           ['sample-1', 'sample-2', 'sample-3', 'sample-4'])
        taxonomy_df = pd.DataFrame([['feature-1', 'a; b; c', 0.123],
                                    ['feature-2', 'a; b; c; d; e', 0.345],
                                    ['feature-3', 'a; f; g; h', 0.678]],
                                   columns=['Feature ID', 'Taxon',
                                            'Confidence'])
        taxonomy_df.set_index('Feature ID', inplace=True)
        tax = Taxonomy(table, taxonomy_df)

        exp = {'sample-1': {'rare': {'feature-3': 0.25},
                            'unique': ['feature-3', ]},
               'sample-2': {'rare': {'feature-1': 0.5},
                            'unique': None},
               'sample-3': {'rare': {'feature-1': 0.5},
                            'unique': None},
               'sample-4': {'rare': None, 'unique': None}}

        for k, e in exp.items():
            obs = tax.rare_unique(k, rare_threshold=0.51)
            self.assertEqual(obs, e)

    def test_bp_tree(self):
        taxonomy_greengenes_df = pd.DataFrame(
            [['feature-1', 'k__a;  p__b;  o__c', 0.123],
             ['feature-2', 'k__a;  p__b;  o__c;  f__d;  g__e', 0.34],
             ['feature-3', 'k__a;  p__f;  o__g;  f__h;  g__', 0.678]],
            columns=['Feature ID', 'Taxon', 'Confidence'])
        taxonomy_greengenes_df.set_index('Feature ID', inplace=True)
        taxonomy = Taxonomy(self.table, taxonomy_greengenes_df,
                            collapse_level=6)
        bp_tree = taxonomy.bp_tree
        exp_parens = 11
        obs_parens = sum(bp_tree.B)
        self.assertEqual(exp_parens, obs_parens)
        exp_names = [
            'k__a;',
            'k__a; p__b;',
            'k__a; p__b; o__c;',
            'k__a; p__b; o__c',
            'k__a; p__b; o__c; f__d;',
            'k__a; p__b; o__c; f__d; g__e',
            'k__a; p__f;',
            'k__a; p__f; o__g;',
            'k__a; p__f; o__g; f__h;',
            'k__a; p__f; o__g; f__h; g__',
        ]
        self.maxDiff = None
        obs_names = []
        for i in range(len(bp_tree.B)):
            name = bp_tree.name(i)
            if name is not None:
                obs_names.append(name)
        self.assertCountEqual(exp_names, obs_names)

    def test_get_group(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        exp = GroupTaxonomy(name='sample-2',
                            taxonomy='((((feature-1,((feature-2)e)d)c)b)a);',
                            features=['feature-1', 'feature-2'],
                            feature_values=[1. / 5, 4. / 5],
                            feature_variances=[0.0, 0.0])
        obs = taxonomy.get_group(['sample-2'])
        self.assertEqual(obs, exp)

    def test_get_group_multiple(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        exp = GroupTaxonomy(name='foo',
                            taxonomy='((((feature-1,((feature-2)e)d)c)b,(((feature-3)h)g)f)a);',  # noqa
                            features=['feature-1', 'feature-2', 'feature-3'],
                            feature_values=[1. / 10, 6. / 10, 3. / 10],
                            feature_variances=[0.0, 0.0, 0.0])
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
                            feature_variances=[2.0, 3.0])
        obs = taxonomy.get_group(['sample-1'])
        self.assertEqual(obs, exp)

    def test_get_group_missing(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_df)
        with self.assertRaisesRegex(UnknownID, "sample-X does not exist"):
            taxonomy.get_group(['sample-X'])

    def test_get_counts(self):
        taxonomy_df = pd.DataFrame([['feature-1', 'k__a; p__b; c__c', 0.123],
                                    ['feature-2',
                                     'k__a; p__b; c__c; o__d; f__e', 0.345],
                                    ['feature-3', 'k__a; p__f; c__g; o__h',
                                     0.678]],
                                   columns=['Feature ID', 'Taxon',
                                            'Confidence'])
        taxonomy_df.set_index('Feature ID', inplace=True)
        taxonomy = Taxonomy(self.table, taxonomy_df)
        expected = [('Kingdom', {'a': 3}), ('Phylum', {'b': 2, 'f': 1})]

        for level, exp in expected:
            obs = taxonomy.get_counts(level)
            self.assertEqual(obs, exp)
            obs = taxonomy.get_counts(level, samples=['sample-1', 'sample-2',
                                                      'sample-3'])
            self.assertEqual(obs, exp)

        expected_batch = [('sample-1', [('Kingdom', {'a': 2}),
                                        ('Phylum', {'b': 1, 'f': 1})]),
                          ('sample-2', [('Kingdom', {'a': 2}),
                                        ('Phylum', {'b': 2})]),
                          ('sample-3', [('Kingdom', {'a': 3}),
                                        ('Phylum', {'b': 2, 'f': 1})])]
        for sample, expected in expected_batch:
            for level, exp in expected:
                obs = taxonomy.get_counts(level, samples=sample)
                self.assertEqual(obs, exp)

    def test_presence_data_table(self):
        taxonomy = Taxonomy(self.table, self.taxonomy_greengenes_df,
                            self.table_vars)
        obs = taxonomy.presence_data_table(['sample-1', 'sample-2'])

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
            columns=exp_columns,
        )
        self.assertListEqual([{'data': col} for col in exp.columns],
                             obs.columns)
        # wouldn't want to do this on a huge dataframe..., but it checks if
        #  there is a row of obs corresponding to each row of exp...
        exp_df = pd.DataFrame(exp.data)
        obs_df = pd.DataFrame(obs.data)
        obs_df_copy = obs_df.copy()
        for e_idx, row_exp in exp_df.iterrows():
            for o_idx, row_obs in obs_df.iterrows():
                if row_exp.eq(row_obs).all():
                    obs_df_copy.drop(index=o_idx, inplace=True)
                    break
        self.assertTrue(obs_df_copy.empty)


class GroupTaxonomyTests(unittest.TestCase):
    def setUp(self):
        self.tstr = '(((((feature-2)e)d,feature-1)c)b)a;'
        self.obj = GroupTaxonomy(name='sample-2',
                                 taxonomy=self.tstr,
                                 features=['feature-1', 'feature-2'],
                                 feature_values=[1. / 5, 4. / 5],
                                 feature_variances=[0.0, 0.0])

    def test_init(self):
        self.assertEqual(self.obj.name, 'sample-2')
        self.assertEqual(self.obj.taxonomy, self.tstr)
        self.assertEqual(self.obj.features, ['feature-1', 'feature-2'])
        self.assertEqual(self.obj.feature_values, [1. / 5, 4. / 5])
        self.assertEqual(self.obj.feature_variances, [0.0, 0.0])

    def test_init_tree_missing_feature(self):
        with self.assertRaisesRegex(UnknownID,
                                    "is not in the taxonomy."):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr,
                          features=['feature-1', 'feature-3'],
                          feature_values=[1. / 5, 4. / 5],
                          feature_variances=[0.0, 0.0])

    def test_init_feature_value_lengths(self):
        with self.assertRaisesRegex(ValueError,
                                    "length mismatch"):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr + 'feature-3',
                          features=['feature-1', 'feature-2', 'feature-3'],
                          feature_values=[1. / 5, 4. / 5],
                          feature_variances=[0.0, 0.0])

        with self.assertRaisesRegex(ValueError,
                                    "length mismatch"):
            GroupTaxonomy(name='sample-2',
                          taxonomy=self.tstr,
                          features=['feature-1', 'feature-2'],
                          feature_values=[1. / 5, ],
                          feature_variances=[0.0, 0.0])

    def test_to_dict(self):
        exp = {'name': 'sample-2',
               'taxonomy': self.tstr,
               'features': ['feature-1', 'feature-2'],
               'feature_values': [1. / 5, 4. / 5],
               'feature_variances': [0.0, 0.0]}
        obs = self.obj.to_dict()
        self.assertEqual(obs, exp)

    def test_str(self):
        exp = str(self.obj.to_dict())
        obs = str(self.obj)
        self.assertEqual(obs, exp)


if __name__ == '__main__':
    unittest.main()
