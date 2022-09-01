from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from unittest.mock import patch
import pandas as pd
from microsetta_public_api.api.plotting import plot_alpha_filtered,\
    plot_alpha_filtered_alt
from microsetta_public_api.config import DictElement, AlphaElement
from microsetta_public_api.utils.testing import MockedJsonifyTestCase,\
    MockMetadataElement, TrivialVisitor


class AlphaPlottingTestCase(MockedJsonifyTestCase):
    jsonify_to_patch = [
        'microsetta_public_api.api.plotting.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()
        faith_pd_values = [1, 2, 3, 4]
        faith_pd_index = ['s01', 's02', 's04', 's05']
        shannon_values = [7.24, 9.05, 8.25]
        shannon_index = ['s01', 's02', 'sOther']
        alpha_resources = AlphaRepo({
            'faith_pd': pd.Series(faith_pd_values,
                                  index=faith_pd_index),
            'shannon': pd.Series(shannon_values,
                                 index=shannon_index),
        })
        self.res_patcher = patch(
            'microsetta_public_api.api.plotting._alpha_repo_getter')
        self.mock_resources = self.res_patcher.start()
        self.mock_resources.return_value = alpha_resources

        self.metadata = MetadataRepo(pd.DataFrame({
            'age_cat': ['30s', '40s', '50s', '30s', '30s'],
            'num_var': [3, 4, 5, 6, 7],
        }, index=['s01', 's02', 's04', 's05', 'sOther']))
        self.md_patcher = patch(
            'microsetta_public_api.api.plotting._metadata_repo_getter')
        self.mock_metadata = self.md_patcher.start()
        self.mock_metadata.return_value = self.metadata

    def test_simple_plot(self):
        response, code = plot_alpha_filtered(alpha_metric='faith_pd')

        self.assertEqual(200, code)

    def test_simple_plot_with_vertline_for_sample_id(self):
        response, code = plot_alpha_filtered(alpha_metric='faith_pd',
                                             sample_id='s01')

        self.assertEqual(200, code)


class AlphaPlottingAltTestCase(MockedJsonifyTestCase):
    jsonify_to_patch = [
        'microsetta_public_api.api.plotting.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()
        faith_pd_values = [1, 2, 3, 4]
        faith_pd_index = ['s01', 's02', 's04', 's05']
        shannon_values = [7.24, 9.05, 8.25]
        shannon_index = ['s01', 's02', 'sOther']
        metadata = MockMetadataElement(pd.DataFrame({
            'age_cat': ['30s', '40s', '50s', '30s', '30s'],
            'num_var': [3, 4, 5, 6, 7],
        }, index=['s01', 's02', 's04', 's05', 'sOther']))
        self.resources = DictElement({
            'datasets': DictElement({
                'dataset1': DictElement({
                    '__metadata__': metadata,
                    '__alpha__': AlphaElement({
                        'faith_pd': pd.Series(faith_pd_values,
                                              index=faith_pd_index),
                        'shannon': pd.Series(shannon_values,
                                             index=shannon_index),
                    })
                }),
                'dataset2': DictElement({
                    '__metadata__': metadata,
                }),
            }),
        })
        self.resources.accept(TrivialVisitor())
        self.res_patcher = patch(
            'microsetta_public_api.api.plotting.get_resources')
        self.mock_resources = self.res_patcher.start()
        self.mock_resources.return_value = self.resources

    def test_simple_plot(self):
        response, code = plot_alpha_filtered_alt(
            dataset='dataset1', alpha_metric='faith_pd')

        self.assertEqual(200, code)

    def test_simple_plot_with_vertline_for_sample_id(self):
        response, code = plot_alpha_filtered_alt(
            dataset='dataset1', alpha_metric='faith_pd',
            sample_id='s01')

        self.assertEqual(200, code)


class BetaPlottingAltMPLTestCase(MockedJsonifyTestCase):
    # skeleton for testing BetaPlotting
    # add plot_beta_alt_mpl to from microsetta_public_api.api.plotting import
    jsonify_to_patch = [
        'microsetta_public_api.api.plotting.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def setUp(self):
        super().setUp()

    def test_simple_plot(self):
        # response, code = plot_beta_alt_mpl(dataset='',
        #                                    beta_metric='',
        #                                    named_sample_set='',
        #                                    sample_id=None,
        #                                    category=None,
        #                                    language_tag='es_MX')

        # self.assertEqual(200, code)
        pass
