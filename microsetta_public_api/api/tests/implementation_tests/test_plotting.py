from microsetta_public_api.repo._alpha_repo import AlphaRepo
from unittest.mock import patch
import pandas as pd
from microsetta_public_api.api.plotting import plot_alpha_filtered

from microsetta_public_api.utils.testing import MockedJsonifyTestCase


class AlphaPlottingTestCase(MockedJsonifyTestCase):
    jsonify_to_patch = [
        'microsetta_public_api.api.plotting.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

    def test_simple_plot(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_group, \
                patch('microsetta_public_api.api.plotting._validate_query'
                      ) as invalid_query, \
                patch('microsetta_public_api.api.plotting._filter_matching_ids'
                      ) as filter_matching_ids:
            invalid_query.return_value = False
            mock_ids = ['a', 'b', 'c', 'd']
            filter_matching_ids.return_value = mock_ids, None, None
            mock_group.return_value = pd.Series([0.1, 7.24, 8.25, 0.9],
                                                index=mock_ids,
                                                name='faith_pd')

            response, code = plot_alpha_filtered(alpha_metric='faith_pd')

        self.assertEqual(200, code)

    def test_simple_plot_with_vertline_for_sample_id(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_group, \
                patch('microsetta_public_api.api.plotting._validate_query'
                      ) as invalid_query, \
                patch('microsetta_public_api.api.plotting._filter_matching_ids'
                      ) as filter_matching_ids:
            invalid_query.return_value = False
            mock_ids = ['a', 'b', 'c', 'd']
            filter_matching_ids.return_value = mock_ids, None, None
            mock_group.side_effect = [
                pd.Series([0.1, 7.24, 8.25, 0.9],
                          index=mock_ids,
                          name='faith_pd'),
                pd.Series([3]),
                ]

            response, code = plot_alpha_filtered(alpha_metric='faith_pd',
                                                 sample_id='sample-715')

        self.assertEqual(200, code)
