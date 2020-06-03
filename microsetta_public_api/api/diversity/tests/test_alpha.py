from microsetta_public_api.repo._alpha_repo import AlphaRepo
from unittest.mock import patch, PropertyMock
from microsetta_public_api.api.diversity.alpha import (
    available_metrics_alpha, get_alpha, alpha_group
)
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import json
from math import sqrt

from microsetta_public_api.utils.testing import MockedJsonifyTestCase


class AlphaDiversityImplementationTests(MockedJsonifyTestCase):

    # need to choose where jsonify is being loaded from
    # see https://stackoverflow.com/a/46465025
    jsonify_to_patch = 'microsetta_public_api.api.diversity.alpha.jsonify'

    @classmethod
    def setUpClass(cls):
        cls.post_body = {'sample_ids': ['sample-foo-bar',
                                        'sample-baz-bat']
                         }

    def test_alpha_diveristy_available_metrics(self):

        with patch('microsetta_public_api.repo._alpha_repo.AlphaRepo'
                   '.resources', new_callable=PropertyMock
                   ) as mock_resources:
            mock_resources.return_value = {
                'faith_pd': '/some/path', 'chao1': '/some/other/path',
            }
            exp_metrics = ['faith_pd', 'chao1']
            response, code = available_metrics_alpha()
            obs = json.loads(response)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual(exp_metrics, obs['alpha_metrics'])

    def test_alpha_diversity_single_sample(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_exists.return_value = [True]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25}, name='observed_otus')
            response, code = get_alpha('sample-foo-bar', 'observed_otus')

        exp = {
            'sample_id': 'sample-foo-bar',
            'alpha_metric': 'observed_otus',
            'data': 8.25,
        }
        obs = json.loads(response)
        self.assertDictEqual(exp, obs)
        self.assertEqual(code, 200)

    def test_alpha_diversity_unknown_id(self):
        with patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_exists.return_value = [False]
            response, code = get_alpha('sample-foo-bar', 'observed-otus')

        self.assertRegex(response,
                         "Sample ID not found.")
        self.assertEqual(code, 404)

    def test_alpha_diversity_group_return_raw_only(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['observed_otus']
            mock_exists.return_value = [True, True]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25, 'sample-baz-bat': 9.01},
                name='observed_otus'
            )
            metric = 'observed_otus'
            response, code = alpha_group(self.post_body,
                                         alpha_metric=metric,
                                         summary_statistics=False,
                                         return_raw=True)

        exp = {
            'alpha_metric': 'observed_otus',
            'alpha_diversity': {'sample-foo-bar': 8.25,
                                'sample-baz-bat': 9.01,
                                }
        }
        obs = json.loads(response.data)

        self.assertDictEqual(exp, obs)
        self.assertEqual(code, 200)

    def test_alpha_diversity_group_return_summary_and_raw(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:

            mock_metrics.return_value = ['observed_otus']
            mock_exists.return_value = [True, True]
            mock_method.return_value = pd.Series(
                {
                    'sample-foo-bar': 7,
                    'sample-baz-bat': 9.5,
                    'sample-qux-quux': 7.5,
                    'sample-4': 8,
                },
                name='observed_otus'
            )
            metric = 'observed_otus'
            response, code = alpha_group(
                body={
                    'sample_ids': [
                        'sample-foo-bar',
                        'sample-baz-bat',
                        'sample-qux-quux',
                        'sample-4',
                    ]
                },
                alpha_metric=metric,
                summary_statistics=True,
                percentiles=[100, 0, 50, 20],
                return_raw=True,
            )

            exp = {
                'alpha_metric': 'observed_otus',
                'alpha_diversity': {
                    'sample-foo-bar': 7,
                    'sample-baz-bat': 9.5,
                    'sample-qux-quux': 7.5,
                    'sample-4': 8,
                    },
                'group_summary': {
                    'mean': 8,
                    'median': 7.75,
                    'std': sqrt(0.875),
                    'group_size': 4,
                    'percentile': [100, 0, 50, 20],
                    'percentile_values': [9.5, 7, 7.75, 7.3]
                }
            }

            self.assertEqual(code, 200)
            obs = json.loads(response.data)
            self.assertCountEqual(exp.keys(), obs.keys())
            self.assertCountEqual(exp['alpha_metric'], obs['alpha_metric'])
            self.assertDictEqual(exp['alpha_diversity'],
                                 obs['alpha_diversity'])
            self.assertCountEqual(exp['group_summary'].keys(),
                                  obs['group_summary'].keys()
                                  )
            gs_exp = exp['group_summary']
            gs_obs = obs['group_summary']

            npt.assert_array_almost_equal(gs_exp.pop('percentile'),
                                          gs_obs.pop('percentile'))
            npt.assert_array_almost_equal(gs_exp.pop('percentile_values'),
                                          gs_obs.pop('percentile_values'))
            # checks of the numerical parts of the expected and observed are
            #  almost the same
            pdt.assert_series_equal(pd.Series(gs_exp), pd.Series(gs_obs),
                                    check_exact=False)

    def test_alpha_diversity_group_return_summary_only(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:

            mock_metrics.return_value = ['observed_otus']
            mock_exists.return_value = [True, True]
            mock_method.return_value = pd.Series(
                {
                    'sample-foo-bar': 7,
                    'sample-baz-bat': 9.5,
                    'sample-qux-quux': 7.5,
                    'sample-4': 8,
                },
                name='observed_otus'
            )
            metric = 'observed_otus'
            response, code = alpha_group(
                body={
                    'sample_ids': [
                        'sample-foo-bar',
                        'sample-baz-bat',
                        'sample-qux-quux',
                        'sample-4',
                    ]
                },
                alpha_metric=metric,
                summary_statistics=True,
                percentiles=[100, 0, 50, 20],
                return_raw=False,
            )

            exp = {
                'alpha_metric': 'observed_otus',
                'group_summary': {
                    'mean': 8,
                    'median': 7.75,
                    'std': sqrt(0.875),
                    'group_size': 4,
                    'percentile': [100, 0, 50, 20],
                    'percentile_values': [9.5, 7, 7.75, 7.3]
                }
            }

            self.assertEqual(code, 200)
            obs = json.loads(response.data)
            self.assertCountEqual(exp.keys(), obs.keys())
            self.assertCountEqual(exp['alpha_metric'], obs['alpha_metric'])
            self.assertCountEqual(exp['group_summary'].keys(),
                                  obs['group_summary'].keys()
                                  )
            gs_exp = exp['group_summary']
            gs_obs = obs['group_summary']
            npt.assert_array_almost_equal(gs_exp.pop('percentile'),
                                          gs_obs.pop('percentile'))
            npt.assert_array_almost_equal(gs_exp.pop('percentile_values'),
                                          gs_obs.pop('percentile_values'))
            # checks of the numerical parts of the expected and observed are
            #  almost the same
            pdt.assert_series_equal(pd.Series(gs_exp), pd.Series(gs_obs),
                                    check_exact=False)

    def test_alpha_diversity_group_percentiles_none(self):
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:

            mock_metrics.return_value = ['observed_otus']
            mock_exists.return_value = [True, True]
            mock_method.return_value = pd.Series(
                {
                    'sample-foo-bar': 7,
                    'sample-baz-bat': 9.5,
                    'sample-qux-quux': 7.5,
                    'sample-4': 8,
                },
                name='observed_otus'
            )
            metric = 'observed_otus'
            response, code = alpha_group(
                body={
                    'sample_ids': [
                        'sample-foo-bar',
                        'sample-baz-bat',
                        'sample-qux-quux',
                        'sample-4',
                    ]
                },
                alpha_metric=metric,
                summary_statistics=True,
                percentiles=None,
                return_raw=False,
            )
            self.assertEqual(code, 200)
            obs = json.loads(response.data)
            self.assertIn('group_summary', obs)
            summary = obs['group_summary']
            self.assertIn('percentile', summary)
            perc = summary['percentile']
            # check default value of percentiles is returned
            npt.assert_array_almost_equal(perc, list(range(10, 91, 10)))

    def test_alpha_diversity_group_unknown_metric(self):
        with patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['metric-a', 'metric-b']
            metric = 'observed_otus'
            response, code = alpha_group(self.post_body,
                                         alpha_metric=metric,
                                         summary_statistics=False,
                                         return_raw=True)

        api_out = json.loads(response.data)
        self.assertRegex(api_out['text'],
                         r"Requested metric: 'observed_otus' is unavailable. "
                         r"Available metrics: \[(.*)\]")
        self.assertEqual(code, 404)

    def test_alpha_diversity_group_unknown_sample(self):
        # One ID not found (out of two)
        with patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['observed_otus']
            mock_exists.side_effect = [True, False]
            response, code = alpha_group(self.post_body, 'observed_otus',
                                         )

        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)

        # Multiple IDs do not exist
        with patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['observed_otus']
            mock_exists.side_effect = [False, False]
            response, code = alpha_group(self.post_body, 'observed_otus',
                                         )
        api_out = json.loads(response.data)
        self.assertListEqual(api_out['missing_ids'],
                             ['sample-foo-bar',
                              'sample-baz-bat'])
        self.assertRegex(api_out['text'],
                         r'Sample ID\(s\) not found.')
        self.assertEqual(code, 404)
