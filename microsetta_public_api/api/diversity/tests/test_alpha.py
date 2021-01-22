from microsetta_public_api.repo._alpha_repo import AlphaRepo
from unittest.mock import patch, PropertyMock
from microsetta_public_api.api.diversity.alpha import (
    available_metrics_alpha, get_alpha, alpha_group, exists_single,
    exists_group,
    available_metrics_alpha_alt,
    get_alpha_alt,
    alpha_group_alt,
    exists_single_alt,
    exists_group_alt,
)
from microsetta_public_api.config import DictElement, AlphaElement
from microsetta_public_api.exceptions import (
    UnknownResource, UnknownID, IncompatibleOptions,
)
from microsetta_public_api.repo._metadata_repo import MetadataRepo
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import json
from math import sqrt

from microsetta_public_api.utils.testing import (
    MockMetadataElement,
    MockedJsonifyTestCase,
    TrivialVisitor,
)


class AlphaDiversityImplementationTests(MockedJsonifyTestCase):

    # need to choose where jsonify is being loaded from
    # see https://stackoverflow.com/a/46465025
    jsonify_to_patch = [
        'microsetta_public_api.api.diversity.alpha.jsonify',
        'microsetta_public_api.utils._utils.jsonify',
    ]

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

    def test_alpha_diveristy_exists_single(self):

        with patch('microsetta_public_api.repo._alpha_repo.AlphaRepo'
                   '.resources', new_callable=PropertyMock
                   ) as mock_resources, \
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_resources.return_value = {
                'faith_pd': '/some/path', 'chao1': '/some/other/path',
            }
            mock_exists.return_value = True

            response, code = exists_single(alpha_metric='faith_pd',
                                           sample_id='sample_1')
            obs = json.loads(response)
        self.assertTrue(obs)
        self.assertEqual(200, code)

    def test_alpha_diveristy_exists_single_404(self):

        with patch('microsetta_public_api.repo._alpha_repo.AlphaRepo'
                   '.resources', new_callable=PropertyMock
                   ) as mock_resources, \
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_resources.return_value = {
                'faith_pd': '/some/path', 'chao1': '/some/other/path',
            }
            mock_exists.side_effect = [True]

            with self.assertRaises(UnknownResource):
                exists_single(alpha_metric='other-metric',
                              sample_id='sample_1')

    def test_alpha_diveristy_exists_group(self):

        with patch('microsetta_public_api.repo._alpha_repo.AlphaRepo'
                   '.resources', new_callable=PropertyMock
                   ) as mock_resources, \
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_resources.return_value = {
                'faith_pd': '/some/path', 'chao1': '/some/other/path',
            }
            mock_exists.return_value = [True, False, True]

            response, code = exists_group(alpha_metric='faith_pd',
                                          body=['s1', 's2', 's3'])
            obs = json.loads(response)
        self.assertListEqual(obs, [True, False, True])
        self.assertEqual(200, code)

    def test_alpha_diveristy_exists_group_404(self):
        with patch('microsetta_public_api.repo._alpha_repo.AlphaRepo'
                   '.resources', new_callable=PropertyMock
                   ) as mock_resources, \
                patch.object(AlphaRepo, 'exists') as mock_exists:
            mock_resources.return_value = {
                'faith_pd': '/some/path', 'chao1': '/some/other/path',
            }
            mock_exists.side_effect = [True, False, True]

            with self.assertRaises(UnknownResource):
                exists_group(alpha_metric='other-metric',
                             body=['s1', 's2', 's3'])

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
            with self.assertRaises(UnknownID):
                get_alpha('sample-foo-bar', 'observed-otus')

    def test_alpha_diversity_improper_parameters(self):
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
            with self.assertRaises(IncompatibleOptions):
                alpha_group(self.post_body,
                            alpha_metric=metric,
                            summary_statistics=False,
                            return_raw=False)

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

    def test_alpha_diversity_group_return_raw_only_metadata_query_OR(self):
        post_body = {
            'sample_ids': [
                'sample-foo-bar',
                'sample-baz-bat',
            ],
            'metadata_query': {
                'some query': 'value'
            },
            'condition': "OR",
        }
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo,
                             'available_metrics') as mock_metrics, \
                patch.object(MetadataRepo,
                             'sample_id_matches') as mock_matches:
            mock_metrics.return_value = ['observed_otus']
            # first two values are used on checking requested ids, the other
            # two are used for checking ids that match metadata query
            mock_exists.side_effect = [True, True, True, False]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25, 'sample-baz-bat': 9.01},
                name='observed_otus'
            )
            mock_matches.return_value = ['sample-3', 'sample-4']
            metric = 'observed_otus'
            response, code = alpha_group(post_body,
                                         alpha_metric=metric,
                                         summary_statistics=False,
                                         return_raw=True)
        self.assertEqual(code, 200)
        args, kwargs = mock_method.call_args
        self.assertCountEqual(args[0], ['sample-foo-bar', 'sample-baz-bat',
                                        'sample-3'])

    def test_alpha_diversity_group_return_raw_only_metadata_query_AND(self):
        post_body = {
            'sample_ids': [
                'sample-foo-bar',
                'sample-baz-bat',
            ],
            'metadata_query': {
                'some query': 'value'
            },
            'condition': "AND",
        }
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo,
                             'available_metrics') as mock_metrics, \
                patch.object(MetadataRepo,
                             'sample_id_matches') as mock_matches:
            mock_metrics.return_value = ['observed_otus']
            # first two values are used on checking requested ids, the other
            # two are used for checking ids that match metadata query
            mock_exists.side_effect = [True, True, True, True]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25, 'sample-baz-bat': 9.01},
                name='observed_otus'
            )
            mock_matches.return_value = ['sample-foo-bar', 'sample-4']
            metric = 'observed_otus'
            response, code = alpha_group(post_body,
                                         alpha_metric=metric,
                                         summary_statistics=False,
                                         return_raw=True)
        self.assertEqual(code, 200)
        args, kwargs = mock_method.call_args
        self.assertCountEqual(args[0], ['sample-foo-bar'])

    def test_alpha_diversity_group_return_raw_only_metadata_query_only(self):
        post_body = {
            'metadata_query': {
                'some query': 'value'
            },
        }
        with patch.object(AlphaRepo, 'get_alpha_diversity') as mock_method, \
                patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo,
                             'available_metrics') as mock_metrics, \
                patch.object(MetadataRepo,
                             'sample_id_matches') as mock_matches:
            mock_metrics.return_value = ['observed_otus']
            # first two values are used on checking requested ids, the other
            # two are used for checking ids that match metadata query
            mock_exists.side_effect = [True, True, True, True]
            mock_method.return_value = pd.Series({
                'sample-foo-bar': 8.25, 'sample-baz-bat': 9.01},
                name='observed_otus'
            )
            mock_matches.return_value = ['sample-foo-bar', 'sample-4']
            metric = 'observed_otus'
            response, code = alpha_group(post_body,
                                         alpha_metric=metric,
                                         summary_statistics=False,
                                         return_raw=True)
        self.assertEqual(code, 200)
        args, kwargs = mock_method.call_args
        self.assertCountEqual(args[0], ['sample-foo-bar', 'sample-4'])

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
            with self.assertRaises(UnknownResource):
                alpha_group(self.post_body,
                            alpha_metric=metric,
                            summary_statistics=False,
                            return_raw=True)

    def test_alpha_diversity_group_unknown_sample(self):
        # One ID not found (out of two)
        with patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['observed_otus']
            mock_exists.side_effect = [True, False]
            with self.assertRaises(UnknownID):
                alpha_group(self.post_body, 'observed_otus')

        # Multiple IDs do not exist
        with patch.object(AlphaRepo, 'exists') as mock_exists, \
                patch.object(AlphaRepo, 'available_metrics') as mock_metrics:
            mock_metrics.return_value = ['observed_otus']
            mock_exists.side_effect = [False, False]
            with self.assertRaises(UnknownID):
                alpha_group(self.post_body, 'observed_otus')


class AlphaAltTests(MockedJsonifyTestCase):

    jsonify_to_patch = [
        'microsetta_public_api.api.diversity.alpha.jsonify',
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
            'microsetta_public_api.api.diversity.alpha.get_resources')
        self.mock_resources = self.res_patcher.start()
        self.mock_resources.return_value = self.resources

    def tearDown(self):
        self.res_patcher.stop()
        super().tearDown()

    def test_availalbe_metrics_alt(self):
        response, code = available_metrics_alpha_alt('dataset1')
        avail = json.loads(response)
        self.assertEqual(200, code)
        self.assertDictEqual(avail, {'alpha_metrics': ['faith_pd', 'shannon']})
        with self.assertRaises(UnknownResource):
            # check for dataset that exists but has no alpha
            available_metrics_alpha_alt('dataset2')
        with self.assertRaises(UnknownResource):
            # check for dataset that does not exist
            available_metrics_alpha_alt('dataset3')

    def test_get_alpha_alt(self):
        faith_pd, code1 = get_alpha_alt('dataset1', 's01',
                                        'faith_pd')
        shannon, code2 = get_alpha_alt('dataset1', 's02', 'shannon')
        faith_pd_value = json.loads(faith_pd)
        shannon_value = json.loads(shannon)
        self.assertEqual(faith_pd_value['data'], 1)
        self.assertEqual(200, code1)
        self.assertEqual(shannon_value['data'], 9.05)
        self.assertEqual(200, code2)

    def test_get_alpha_alt_404(self):
        with self.assertRaisesRegex(UnknownResource, 'dataset3'):
            get_alpha_alt('dataset3', 's03', 'faith_pd')
        with self.assertRaisesRegex(UnknownResource, '__alpha__'):
            get_alpha_alt('dataset2', 's03', 'faith_pd')

    def test_alpha_group_alt(self):
        request = {'sample_ids': ['s01', 's04']}
        response, code = alpha_group_alt(request, 'dataset1', 'faith_pd',
                                         return_raw=True)
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertDictEqual({'s01': 1, 's04': 3},
                             obs['alpha_diversity'])

    def test_alpha_group_alt_404_sample_id(self):
        request = {'sample_ids': ['s01', 'dne']}
        with self.assertRaises(UnknownID):
            alpha_group_alt(request, 'dataset1', 'faith_pd',
                            return_raw=True)

    def test_alpha_group_alt_404_metric(self):
        request = {'sample_ids': ['s01', 's04']}
        with self.assertRaises(UnknownResource):
            alpha_group_alt(request, 'dataset1', 'bad-metric',
                            return_raw=True)

    def test_alpha_group_alt_filter_metadata_OR(self):
        post_body = {
            'sample_ids': [
                's04',
            ],
            'metadata_query': {
                    "condition": "AND",
                    "rules": [
                        {
                            "id": "age_cat",
                            "field": "age_cat",
                            "operator": "equal",
                            "value": "30s",
                        },
                    ],
                },
            'condition': "OR",
        }
        response, code = alpha_group_alt(post_body, 'dataset1', 'faith_pd',
                                         return_raw=True)
        obs = json.loads(response)
        self.assertEqual(code, 200)
        sample_ids = obs['alpha_diversity'].keys()
        self.assertCountEqual(['s01', 's04', 's05'], sample_ids)

    def test_alpha_exists_single_alt(self):
        response, code = exists_single_alt('dataset1', 'faith_pd', 's01')
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertTrue(obs)

        response, code = exists_single_alt('dataset1', 'faith_pd', 's-dne')
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertFalse(obs)

        response, code = exists_single_alt('dataset1', 'shannon', 's03')
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertFalse(obs)

    def test_alpha_exists_single_alt_errors(self):
        with self.assertRaises(UnknownResource):
            exists_single_alt('dataset2', 'shannon', 's03')

        with self.assertRaises(UnknownResource):
            exists_single_alt('dataset1', 'dne-metric', 's03')

    def test_alpha_exists_group_alt(self):
        body = ['s01', 's03', 's04']
        response, code = exists_group_alt(body, 'dataset1', 'faith_pd')
        self.assertEqual(code, 200)
        obs = json.loads(response)
        self.assertListEqual(obs, [True, False, True])

    def test_alpha_exists_group_alt_errors(self):
        body = ['s01', 's03', 's04']
        with self.assertRaises(UnknownResource):
            exists_group_alt(body, 'dataset2', 'faith_pd')

        with self.assertRaises(UnknownResource):
            exists_group_alt(body, 'dataset1', 'dne-metric')
