import json
import numpy as np
import pandas as pd
from unittest.mock import patch
from skbio.stats.ordination import OrdinationResults
from microsetta_public_api.utils.testing import (
    MockMetadataElement,
    MockedJsonifyTestCase,
    TrivialVisitor,
)
from microsetta_public_api.repo._pcoa_repo import PCoARepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from microsetta_public_api.api.emperor import plot_pcoa, plot_pcoa_alt
from microsetta_public_api.config import (
    DictElement,
    PCOAElement,
)
from microsetta_public_api.exceptions import UnknownResource


class EmperorImplementationTests(MockedJsonifyTestCase):

    # need to choose where jsonify is being loaded from
    # see https://stackoverflow.com/a/46465025
    jsonify_to_patch = [
        'microsetta_public_api.api.emperor.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    @classmethod
    def setUpClass(cls):
        axis_labels = ['PC1', 'PC2', 'PC3']
        cls.test_df1 = pd.DataFrame.from_dict({
            's1': [0.1, 0.2, 7],
            's2': [0.9, 0.2, 7],
        },
            orient='index',
            columns=axis_labels,
        )
        cls.test_df1.index.name = 'Sample ID'
        cls.pcoa1 = OrdinationResults('pcoa1', 'pcoa1',
                                      eigvals=pd.Series([7, 2, 1],
                                                        index=axis_labels,
                                                        ),
                                      samples=cls.test_df1,
                                      proportion_explained=pd.Series(
                                          [0.7, 0.2, 0.1],
                                          index=axis_labels,
                                      ),
                                      )

        cls.test_metadata = pd.DataFrame({
                'age_cat': ['30s', '40s', '50s', '30s', None],
                'num_cat': [7.24, 7.24, 8.25, 7.24, None],
                'other': [1, 2, 3, 4, None],
            }, index=pd.Series(['s1', 's2', 'c', 'd', 'e'], name='#SampleID')
        )

    def test_emperor_impl(self):
        with patch.object(PCoARepo, 'has_pcoa') as mock_has_pc, \
                patch.object(MetadataRepo, 'has_category') as mock_has_md, \
                patch.object(PCoARepo, 'get_pcoa') as mock_get_pc, \
                patch.object(MetadataRepo, 'get_metadata') as mock_get_md:
            # using samples s1, s2
            # using categories 'num_cat' and 'age_cat'
            mock_has_pc.return_value = True
            mock_has_md.return_value = [True, True]
            mock_get_pc.return_value = self.pcoa1
            mock_get_md.return_value = self.test_metadata.loc[['s1', 's2'],
                                                              ['num_cat',
                                                               'age_cat']
                                                              ]
            response, code = plot_pcoa('beta_metric', 'sample_set',
                                       ['num_cat', 'age_cat'])
        response = json.loads(response)
        self.assertEqual(code, 200)

        decomp = response['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa1.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa1.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['s1', 's2']
                                      )

        self.assertListEqual(response['metadata'],
                             [[7.24, '30s'], [7.24, '40s']]
                             )
        self.assertListEqual(response['metadata_headers'],
                             ['num_cat', 'age_cat']
                             )

    def test_emperor_impl_missing_pcoa_404(self):
        with patch.object(PCoARepo, 'has_pcoa') as mock_has_pc, \
                patch.object(MetadataRepo, 'has_category') as mock_has_md:
            # using samples s1, s2
            # using categories 'num_cat' and 'age_cat'
            mock_has_pc.return_value = False
            mock_has_md.return_value = [True, True]
            with self.assertRaises(UnknownResource):
                plot_pcoa('beta_metric', 'sample_set_dne',
                          ['num_cat', 'age_cat'])

    def test_emperor_impl_missing_category_404(self):
        with patch.object(PCoARepo, 'has_pcoa') as mock_has_pc, \
                patch.object(MetadataRepo, 'has_category') as mock_has_md, \
                patch.object(PCoARepo, 'get_pcoa') as mock_get_pc:
            # using samples s1, s2
            # using categories 'num_cat' and 'age_cat'
            mock_has_pc.return_value = True
            mock_has_md.return_value = [False, True]
            mock_get_pc.return_value = self.pcoa1
            with self.assertRaisesRegex(UnknownResource, 'num_cat'):
                plot_pcoa('beta_metric', 'sample_set',
                          ['num_cat', 'age_cat'])


class EmperorAltTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.emperor.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    @classmethod
    def setUpClass(cls):
        axis_labels = ['PC1', 'PC2', 'PC3']
        cls.test_df1 = pd.DataFrame.from_dict({
            's1': [0.1, 0.2, 7],
            's2': [0.9, 0.2, 7],
        },
            orient='index',
            columns=axis_labels,
        )
        cls.test_df1.index.name = 'Sample ID'
        cls.pcoa1 = OrdinationResults('pcoa1', 'pcoa1',
                                      eigvals=pd.Series([7, 2, 1],
                                                        index=axis_labels,
                                                        ),
                                      samples=cls.test_df1,
                                      proportion_explained=pd.Series(
                                          [0.7, 0.2, 0.1],
                                          index=axis_labels,
                                      ),
                                      )
        cls.test_metadata = pd.DataFrame(
            {
                'age_cat': ['30s', '40s', '50s', '30s', None],
                'num_cat': [7.24, 7.24, 8.25, 7.24, None],
                'other': [1, 2, 3, 4, None],
            }, index=pd.Series(['s1', 's2', 'c', 'd', 'e'], name='#SampleID')
        )
        cls.resources = DictElement({
            'datasets': DictElement({
                'dataset1': DictElement({
                    '__metadata__': MockMetadataElement(cls.test_metadata),
                    '__pcoa__': PCOAElement({
                        'sample_set': DictElement({
                            'beta_metric': cls.pcoa1,
                        }),
                    })
                }),
                'dataset2': DictElement({
                    '__metadata__': MockMetadataElement(cls.test_metadata),
                }),
            }),
        })
        cls.resources.accept(TrivialVisitor())
        cls.res_patcher = patch(
            'microsetta_public_api.api.emperor.get_resources')
        cls.mock_resources = cls.res_patcher.start()
        cls.mock_resources.return_value = cls.resources

    def test_emperor_impl(self):
        response, code = plot_pcoa_alt('dataset1', beta_metric='beta_metric',
                                       named_sample_set='sample_set',
                                       metadata_categories=[
                                           'num_cat', 'age_cat'])
        response = json.loads(response)
        self.assertEqual(code, 200)

        decomp = response['decomposition']
        np.testing.assert_array_equal(decomp["coordinates"],
                                      self.pcoa1.samples.values
                                      )
        np.testing.assert_array_equal(decomp["percents_explained"],
                                      100
                                      * self.pcoa1.proportion_explained.values
                                      )
        np.testing.assert_array_equal(decomp["sample_ids"],
                                      ['s1', 's2']
                                      )

        self.assertListEqual(response['metadata'],
                             [[7.24, '30s'], [7.24, '40s']]
                             )
        self.assertListEqual(response['metadata_headers'],
                             ['num_cat', 'age_cat']
                             )

    def test_emperor_impl_missing_pcoa_404(self):
        # using samples s1, s2
        # using categories 'num_cat' and 'age_cat'
        with self.assertRaises(UnknownResource):
            plot_pcoa_alt('dataset1', beta_metric='beta_metric',
                          named_sample_set='sample_set_dne',
                          metadata_categories=['num_cat', 'age_cat'])

    def test_emperor_impl_missing_category_404(self):
        # using samples s1, s2
        # using categories 'num_cat' and 'age_cat'
        with self.assertRaisesRegex(UnknownResource, 'num_var'):
            plot_pcoa_alt('dataset1', beta_metric='beta_metric',
                          named_sample_set='sample_set',
                          metadata_categories=['num_var', 'age_cat'])
