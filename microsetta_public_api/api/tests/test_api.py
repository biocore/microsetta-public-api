from unittest.mock import patch
from flask import jsonify
import json
from microsetta_public_api.utils.testing import FlaskTests


class AlphaDiversityTestCase(FlaskTests):

    def setUp(self):
        super().setUp()
        self.request_content = {
                                'sample_ids': ['sample-foo-bar',
                                               'sample-baz-bat'],
                                }
        self.minimal_response = {'alpha_metric': 'faith_pd',
                                 'alpha_diversity': {'sample1': 5.27},
                                 }


class AlphaDiversityTests(AlphaDiversityTestCase):

    def test_alpha_diversity_available_metrics_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app_context():
            mock_resources.return_value = jsonify({
                 'alpha_metrics': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            exp_metrics = ['faith_pd', 'chao1']
            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual(exp_metrics, obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

            mock_resources.return_value = jsonify({
                'alpha_metrics': []
            }), 200
            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            obs = json.loads(response.data)
            self.assertIn('alpha_metrics', obs)
            self.assertListEqual([], obs['alpha_metrics'])
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_available_metrics_api_bad_response(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.available_metrics_alpha'
                   ) as mock_resources, self.app_context():
            mock_resources.return_value = jsonify({
                'some wrong keyword': ['faith_pd', 'chao1']
            }), 200

            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/metrics/alpha/available')

            self.assertEqual(response.status_code, 500)
            mock_resources.return_value = jsonify({
                'some wrong additional keyword': ['faith_pd', 'chao1'],
                'alpha_metrics': ['faith_pd', 'chao1'],
            }), 200
            self.assertEqual(response.status_code, 500)
            mock_resources.return_value = jsonify({
                'alpha_metrics': 'faith_pd',
            }), 200
            self.assertEqual(response.status_code, 500)

    def test_alpha_diversity_single_sample_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.get_alpha'
                   ) as mock_method, self.app_context():

            exp = {
                'sample_id': 'sample-foo-bar',
                'alpha_metric': 'observed_otus',
                'data': 8.25,
            }
            mock_output = jsonify(exp), 200
            mock_method.return_value = mock_output

            _, self.client = self.build_app_test_client()
            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

            obs = json.loads(response.data)

            self.assertDictEqual(exp, obs)
            self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_unknown_id_api(self):
        with patch('microsetta_public_api.api.diversity.alpha'
                   '.get_alpha'
                   ) as mock_method, self.app_context():

            mock_method.return_value = jsonify(error=404, text="Sample ID "
                                                               "not found."), \
                                       404
            _, self.client = self.build_app_test_client()

            response = self.client.get(
                '/api/diversity/alpha/observed_otus/sample-foo-bar')

        self.assertRegex(response.data.decode(),
                         "Sample ID not found.")
        self.assertEqual(response.status_code, 404)


class AlphaDiversityGroupTests(AlphaDiversityTestCase):

    def setUp(self):
        super().setUp()
        self.patcher = patch('microsetta_public_api.api.diversity.alpha'
                             '.alpha_group')
        self.mock_method = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_alpha_diversity_group_api(self):
        exp = {
            'alpha_metric': 'observed_otus',
            'alpha_diversity': {'sample-foo-bar': 8.25,
                                'sample-baz-bat': 9.01,
                                }
        }

        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 200

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )

        obs = json.loads(response.data)

        self.assertDictEqual(exp, obs)
        self.assertEqual(response.status_code, 200)

    def test_alpha_diversity_group_unknown_metric_api(self):

        available_metrics = ['metric1', 'metric2']
        exp = dict(error=404, text=f"Requested metric: 'observed_otus' "
                                   f"is unavailable. Available metrics: "
                                   f"{available_metrics}")
        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 404

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        api_out = json.loads(response.data.decode())
        self.assertEqual(api_out['text'],
                         exp['text'])
        self.assertEqual(response.status_code, 404)

    def test_alpha_diversity_group_unknown_sample_api(self):
        missing_ids = ['sample-baz-bat']
        exp = dict(missing_ids=missing_ids,
                   error=404, text="Sample ID(s) not found for "
                                   "metric: observed_otus")

        with self.app_context():
            self.mock_method.return_value = jsonify(exp), 404

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        api_out = json.loads(response.data.decode())
        self.assertEqual(api_out, exp)
        self.assertEqual(response.status_code, 404)

    def test_alpha_diverstiy_group_default_arguments(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(self.minimal_response), 200

        _, self.client = self.build_app_test_client()

        self.client.post(
            '/api/diversity/alpha_group/observed_otus',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.mock_method.assert_called_with(
            alpha_metric='observed_otus',
            body=self.request_content,
            summary_statistics=True,
            percentiles=None,
            return_raw=False,
        )

    def test_alpha_diversity_group_summary_statistics_queries(self):
        with self.app_context():
            self.mock_method.return_value = jsonify(self.minimal_response), 200

        _, self.client = self.build_app_test_client()

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?summary_statistics=true',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?summary_statistics=true&percentiles=1,2,45',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?summary_statistics=false&percentiles=1,2,45',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?summary_statistics=true&percentiles=0,50,100',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?percentiles=50',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            self.mock_method.return_value = jsonify(
                error=400, text='at least one of summary_statistics'
                                'and return_raw should be true'), 400
        response = self.client.post(
            '/api/diversity/alpha_group/observed_otus'
            '?summary_statistics=true',
            content_type='application/json',
            data=json.dumps(self.request_content)
        )
        self.assertEqual(response.status_code, 400)

    def _minimal_query(self):
        minimal_query = '/api/diversity/alpha_group/observed_otus'
        return self.client.post(minimal_query,
                                content_type='application/json',
                                data=json.dumps(self.request_content)
                                )

    def test_alpha_diversity_group_summary_statistics_responses(self):
        _, self.client = self.build_app_test_client()
        with self.app_context():
            # test that alpha_metric, alpha_diversity is okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'alpha_diversity': {'sample1': 4.5}
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that alpha_metric, group_summary is okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'group_summary': {
                        'mean': 4.5,
                        'median': 3.2,
                        'std': 1.2,
                        'group_size': 7,
                        'percentile': [0, 12, 45],
                        'percentile_values': [1.2, 3.0, 3.1],
                    },
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that alpha_metric, group_summary, _and_ alpha_diveristy is
            #  okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                    'group_summary': {
                        'mean': 4.5,
                        'median': 3.2,
                        'std': 1.2,
                        'group_size': 7,
                        'percentile': [0, 12, 45],
                        'percentile_values': [1.2, 3.0, 3.1],
                    },
                    'alpha_diversity': {'sample1': 4.5}
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 200)

        with self.app_context():
            # test that only alpha_metric is not okay
            self.mock_method.return_value = jsonify(
                {
                    'alpha_metric': 'chao1',
                }
            ), 200
        response = self._minimal_query()
        self.assertEqual(response.status_code, 500)
