from microsetta_public_api.repo._alpha_repo import AlphaRepo
from microsetta_public_api.repo._metadata_repo import MetadataRepo
from unittest.mock import patch
import pandas as pd
from microsetta_public_api.api.plotting import plot_alpha_filtered,\
    plot_alpha_filtered_alt
from microsetta_public_api.config import DictElement, AlphaElement
from microsetta_public_api.utils.testing import MockedJsonifyTestCase,\
    MockMetadataElement, TrivialVisitor
from microsetta_public_api.api.plotting import _make_mpl_fig
from pandas import Series
from numpy import array, histogram
from skimage.io import imread
from scipy.stats import ks_2samp
import json
from microsetta_public_api.utils.testing import FlaskTests


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


class BetaPlottingAltMPLTestCase(FlaskTests):
    def mock_translate(*args, **kwargs):
        map_en_us_to_es_mx = {
            # TODO: Not proficient in Spanish. These translations need to be
            #  reviewed. Translations provided by Google Translate.
            "Mouth": "Boca",
            "Skin": "La Piel",
            "Stool": "Heces",
            "You": "Tú"
        }

        if args[0] in map_en_us_to_es_mx:
            return map_en_us_to_es_mx[args[0]]

        return 'UNKNOWN'

    # get_locale() is not currently called by _make_mpl_fig(). Annotation is
    # useful for testing purposes, however.
    # @patch('flask_babel.get_locale', return_value='es_MX')
    @patch('flask_babel._', side_effect=mock_translate)
    def test_make_mpl_fig(self, MockGetLocale, MockUnderline):
        # As PyBabel works only when the server is running, we must Mock() the
        # PyBabel calls used by _make_mpl_fig() if we wish to generate a plot
        # with the legend translated from English to Spanish.
        # MockGetLocale object does not need to be used as the stock
        # return value is all that's needed.
        # side_effect() is used to simulate _() calls.

        with open('saved_sample_data.json', 'r') as f:
            # d['x'] and d['y'] contain the positional metadata for all points
            # in the test graph. d['membership'] contains a list of strings
            # denoting which cluster each point belongs to. _make_mpl_fig()
            # will use this info to generate a plot with multiple colors and
            # a map legend containing the enumerated values found in
            # d['membership'].
            d = json.load(f)
            membership = Series(d['membership'])
            membership.index = d['membership']

            # call _make_mpl_fig to generate the plot, translating the default
            # en_US values to es_MX.
            output = _make_mpl_fig(membership, d['x'], d['y'], 'You', 'es_MX')

            # write the test output out to file for manual review.
            with open('test_output.png', 'wb') as f:
                f.write(output.getvalue())

            # read the test output back in from file and generate a histogram
            # of the image. Compare the histogram with the known histogram on
            # file using the Kolmogorov–Smirnov test. Consider the test
            # output good if the p_value is greater than or equal to 95%.
            image = imread(fname='test_output.png', as_gray=True)
            histogram1, _ = histogram(image, bins=256, range=(0, 1))
            histogram2 = array(d['image_histogram_mx'])
            _, p_value = ks_2samp(histogram1, histogram2)
            self.assertTrue(p_value >= 0.95)
